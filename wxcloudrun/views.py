from datetime import datetime
import json
from urllib.parse import parse_qs, urlparse
from flask import render_template, request
from run import app
from wxcloudrun.dao import (
    delete_counterbyid,
    insert_antifake_record,
    insert_counter,
    query_antifake_by_code,
    query_counterbyid,
    update_antifake_record,
    update_counterbyid,
)
from wxcloudrun.model import AntiCounterfeitCodes, Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


def extract_code_from_qr(qr_data):
    """
    解析二维码内容，提取防伪码
    :param qr_data: 二维码原始内容
    :return: 防伪码字符串
    """
    if not qr_data:
        return None

    if isinstance(qr_data, dict):
        for key in ['code', 'antiCounterfeitCode', 'anti_code', 'antifake_code']:
            if qr_data.get(key):
                return str(qr_data[key]).strip()
        return None

    if not isinstance(qr_data, str):
        return None

    raw = qr_data.strip()
    if not raw:
        return None

    if raw.startswith('{') or raw.startswith('['):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            for key in ['code', 'antiCounterfeitCode', 'anti_code', 'antifake_code']:
                if payload.get(key):
                    return str(payload[key]).strip()

    if raw.startswith('code='):
        return raw.split('=', 1)[1].strip()

    if '://' in raw or '?' in raw:
        parsed = urlparse(raw)
        query = parse_qs(parsed.query)
        for key in ['code', 'antiCounterfeitCode', 'anti_code', 'antifake_code']:
            if key in query and query[key]:
                return str(query[key][0]).strip()

    return raw


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/api/verify', methods=['POST'])
def verify_code():
    """
    :return: 防伪码比对结果
    """
    params = request.get_json()
    if not params:
        return make_err_response('缺少请求参数')

    qr_data = params.get('qr_data') or params.get('code')
    code = extract_code_from_qr(qr_data)
    if not code:
        return make_err_response('未识别到防伪码')

    record = query_antifake_by_code(code)
    now = datetime.now()

    if record is None:
        record = AntiCounterfeitCodes(
            code=code,
            usage_count=1,
            first_used_at=now,
            last_used_at=now,
        )
        insert_antifake_record(record)
        return make_succ_response({
            'status': 'genuine',
            'message': '正品',
            'code': code,
            'usageCount': 1,
        })

    record.usage_count += 1
    record.last_used_at = now
    update_antifake_record(record)
    return make_succ_response({
        'status': 'reused',
        'message': '该防伪码已被使用',
        'code': code,
        'usageCount': record.usage_count,
    })
