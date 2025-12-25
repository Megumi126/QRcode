from datetime import datetime

from wxcloudrun import db


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, default=datetime.now())


# 防伪码使用记录表
class AntiCounterfeitCodes(db.Model):
    __tablename__ = 'AntiCounterfeitCodes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), unique=True, nullable=False)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    first_used_at = db.Column('firstUsedAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    last_used_at = db.Column('lastUsedAt', db.TIMESTAMP, nullable=False, default=datetime.now())
