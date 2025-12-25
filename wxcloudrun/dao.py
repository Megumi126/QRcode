import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import AntiCounterfeitCodes, Counters

# 初始化日志
logger = logging.getLogger('log')


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        return Counters.query.filter(Counters.id == id).first()
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        counter = Counters.query.get(id)
        if counter is None:
            return
        db.session.delete(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        db.session.add(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        counter = query_counterbyid(counter.id)
        if counter is None:
            return
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_counterbyid errorMsg= {} ".format(e))


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
