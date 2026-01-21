from datetime import datetime
import json
from urllib.parse import parse_qs, urlparse
from flask import render_template, request, jsonify
from run import app
from wxcloudrun.dao import (
    insert_antifake_record,
    query_antifake_by_code,
    update_antifake_record,
)
from wxcloudrun import db, limiter
from wxcloudrun.model import AntiCounterfeitCodes, AntiFakeCode, AntiFakeScanLog
from wxcloudrun.response import make_succ_response, make_err_response
import re
from datetime import timezone
import pytz
import config
from flask import Response


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')



def _parse_scan_time(value):
    try:
        dt = datetime.strptime(value, '%Y/%m/%d %H:%M:%S')
        return dt.replace(tzinfo=pytz.UTC)
    except Exception:
        return None

def _now_utc():
    return datetime.now(timezone.utc)

def _real_ip():
    xff = request.headers.get('X-Forwarded-For', '')
    parts = [p.strip() for p in xff.split(',') if p.strip()]
    if parts:
        return parts[0]
    return request.remote_addr or ''

def _mask_ip(ip):
    if not ip:
        return ''
    if ':' in ip:
        segs = ip.split(':')
        segs[-1] = 'xxxx'
        return ':'.join(segs)
    if '.' in ip:
        segs = ip.split('.')
        if len(segs) == 4:
            segs[-1] = 'xxx'
        return '.'.join(segs)
    return ip

def _fmt_time_sg(dt):
    tz = pytz.timezone(config.TIMEZONE_FORMAT)
    return dt.astimezone(tz).strftime('%Y/%m/%d %H:%M:%S')

def _validate_payload(payload):
    if not isinstance(payload, dict):
        return False
    code = payload.get('code')
    scan_time = payload.get('scanTime')
    ip = payload.get('ip')
    if not isinstance(code, str) or not re.fullmatch(r'^\d{16}$', code or ''):
        return False
    if not isinstance(scan_time, str) or _parse_scan_time(scan_time) is None:
        return False
    if not isinstance(ip, str):
        return False
    return True

def _error(status_code=200):
    return jsonify({"status": "error"}), status_code

@app.route('/api/antifake/verify', methods=['POST'])
@limiter.limit(config.RATE_LIMIT_IP)
@limiter.limit(config.RATE_LIMIT_CODE, key_func=lambda: (request.json.get('code') if request.is_json else 'nocode'))
def antifake_verify():
    try:
        payload = request.get_json(silent=True)
        if not _validate_payload(payload):
            return _error(200)
        code = payload['code']
        client_ip = payload.get('ip') or ''
        client_scan_dt = _parse_scan_time(payload.get('scanTime'))
        server_ip = _real_ip()
        now = _now_utc()
        suspicious = 0
        if client_scan_dt is not None:
            delta = abs((now - client_scan_dt).total_seconds())
            if delta > 600:
                suspicious = 1

        with db.session.begin():
            row = db.session.query(AntiFakeCode).filter(AntiFakeCode.code == code).with_for_update().first()
            if row is None:
                db.session.add(AntiFakeScanLog(
                    code=code,
                    server_ip=server_ip,
                    client_ip=client_ip,
                    server_time=now,
                    client_scan_time=client_scan_dt,
                    status='error',
                    is_test=False,
                    duration_ms=0,
                    suspicious=suspicious,
                ))
                return _error(200)

            prev_time = row.last_scan_time
            prev_ip = row.last_scan_ip or ''
            prev_count = row.scan_count or 0

            if not prev_time or prev_count == 0:
                row.scan_count = 1
                row.last_scan_time = now
                row.last_scan_ip = server_ip
                db.session.flush()
                db.session.add(AntiFakeScanLog(
                    code=code,
                    server_ip=server_ip,
                    client_ip=client_ip,
                    server_time=now,
                    client_scan_time=client_scan_dt,
                    status='first',
                    is_test=bool(row.is_test),
                    duration_ms=0,
                    suspicious=suspicious,
                ))
                return jsonify({"status": "first"}), 200

            masked_prev_ip = _mask_ip(prev_ip) if config.MASK_IP else prev_ip
            new_count = prev_count + 1
            row.scan_count = new_count
            row.last_scan_time = now
            row.last_scan_ip = server_ip
            db.session.flush()
            db.session.add(AntiFakeScanLog(
                code=code,
                server_ip=server_ip,
                client_ip=client_ip,
                server_time=now,
                client_scan_time=client_scan_dt,
                status='repeat',
                is_test=bool(row.is_test),
                duration_ms=0,
                suspicious=suspicious,
            ))
            return jsonify({
                "status": "repeat",
                "lastQueryTime": _fmt_time_sg(prev_time),
                "lastQueryIp": masked_prev_ip,
                "queryCount": int(new_count),
            }), 200
    except Exception:
        return _error(500)


def _json(data, status=200):
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/json', status=status)

def _code_valid(s):
    return isinstance(s, str) and re.fullmatch(r'^\d{16}$', s or '') is not None

@app.route('/api/antifake/codes', methods=['GET'])
def list_codes():
    rows = db.session.query(AntiFakeCode).order_by(AntiFakeCode.created_at.desc()).all()
    def to_dict(r):
        return {
            "code": r.code,
            "is_test": bool(r.is_test),
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "scan_count": int(r.scan_count or 0),
            "last_scan_time": r.last_scan_time.isoformat() if r.last_scan_time else None,
            "last_scan_ip": r.last_scan_ip or "",
        }
    return _json({"list": [to_dict(r) for r in rows]})

@app.route('/api/antifake/codes', methods=['POST'])
def create_code():
    payload = request.get_json(silent=True) or {}
    code = payload.get('code')
    is_test = bool(payload.get('is_test', False))
    if not _code_valid(code):
        return _json({"ok": False}, 200)
    exists = db.session.query(AntiFakeCode).filter(AntiFakeCode.code == code).first()
    if exists:
        return _json({"ok": False, "msg": "exists"}, 200)
    row = AntiFakeCode(
        code=code,
        is_test=is_test,
        created_at=_now_utc(),
        scan_count=0,
    )
    db.session.add(row)
    db.session.commit()
    return _json({"ok": True}, 200)

@app.route('/api/antifake/codes/<code>', methods=['PUT'])
def update_code(code):
    if not _code_valid(code):
        return _json({"ok": False}, 200)
    payload = request.get_json(silent=True) or {}
    row = db.session.query(AntiFakeCode).filter(AntiFakeCode.code == code).first()
    if not row:
        return _json({"ok": False, "msg": "not_found"}, 200)
    if 'is_test' in payload:
        row.is_test = bool(payload.get('is_test'))
    if 'scan_count' in payload:
        try:
            val = int(payload.get('scan_count'))
            if val >= 0:
                row.scan_count = val
        except Exception:
            pass
    db.session.commit()
    return _json({"ok": True}, 200)

@app.route('/api/antifake/codes/<code>', methods=['DELETE'])
def delete_code(code):
    if not _code_valid(code):
        return _json({"ok": False}, 200)
    row = db.session.query(AntiFakeCode).filter(AntiFakeCode.code == code).first()
    if not row:
        return _json({"ok": False, "msg": "not_found"}, 200)
    db.session.delete(row)
    db.session.commit()
    return _json({"ok": True}, 200)
