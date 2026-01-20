from datetime import datetime

from wxcloudrun import db
from sqlalchemy.dialects.mysql import DATETIME


# 防伪码使用记录表
class AntiCounterfeitCodes(db.Model):
    __tablename__ = 'AntiCounterfeitCodes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), unique=True, nullable=False)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    first_used_at = db.Column('firstUsedAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    last_used_at = db.Column('lastUsedAt', db.TIMESTAMP, nullable=False, default=datetime.now())


# 新版防伪码主表
class AntiFakeCode(db.Model):
    __tablename__ = 'antifake_codes'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    code = db.Column(db.CHAR(16), nullable=False, unique=True, index=True)
    is_test = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(DATETIME(fsp=6), nullable=False)
    scan_count = db.Column(db.BigInteger, nullable=False, default=0)
    last_scan_time = db.Column(DATETIME(fsp=6), nullable=True, index=True)
    last_scan_ip = db.Column(db.String(45), nullable=True)


class AntiFakeScanLog(db.Model):
    __tablename__ = 'antifake_scan_logs'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    code = db.Column(db.CHAR(16), nullable=False, index=True)
    server_ip = db.Column(db.String(45), nullable=False)
    client_ip = db.Column(db.String(45), nullable=True)
    server_time = db.Column(DATETIME(fsp=6), nullable=False, index=True)
    client_scan_time = db.Column(DATETIME(fsp=6), nullable=True)
    status = db.Column(db.Enum('first', 'repeat', 'error'), nullable=False, index=True)
    is_test = db.Column(db.Boolean, nullable=False, default=False)
    duration_ms = db.Column(db.Integer, nullable=False)
    suspicious = db.Column(db.Boolean, nullable=False, default=False)
