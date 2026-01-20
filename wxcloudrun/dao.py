import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import AntiCounterfeitCodes

# 初始化日志
logger = logging.getLogger('log')

def query_antifake_by_code(code):
    """
    根据防伪码查询使用记录
    :param code: 防伪码
    :return: AntiCounterfeitCodes实体
    """
    try:
        return AntiCounterfeitCodes.query.filter(AntiCounterfeitCodes.code == code).first()
    except OperationalError as e:
        logger.info("query_antifake_by_code errorMsg= {} ".format(e))
        return None


def insert_antifake_record(record):
    """
    插入防伪码使用记录
    :param record: AntiCounterfeitCodes实体
    """
    try:
        db.session.add(record)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_antifake_record errorMsg= {} ".format(e))


def update_antifake_record(record):
    """
    更新防伪码使用记录
    :param record: AntiCounterfeitCodes实体
    """
    try:
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_antifake_record errorMsg= {} ".format(e))
