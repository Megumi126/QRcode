import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", 'root')
db_address = os.environ.get("MYSQL_ADDRESS", '127.0.0.1:3306')
db_name = os.environ.get("MYSQL_DB", 'antifake_db')

# 限流与安全
RATE_LIMIT_IP = os.environ.get("RATE_LIMIT_IP", "60 per minute")
RATE_LIMIT_CODE = os.environ.get("RATE_LIMIT_CODE", "20 per minute")
TIMEZONE_FORMAT = os.environ.get("TIMEZONE_FORMAT", "Asia/Singapore")
MASK_IP = os.environ.get("MASK_IP", "1") == "1"
