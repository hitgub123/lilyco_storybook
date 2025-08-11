import logging
import os
from logging.handlers import RotatingFileHandler


LOG_LEVEL = os.getenv("LOG_LEVEL")
# --- 配置 ---
# LOG_DIR = os.path.join(os.path.dirname(__file__), 'log')
LOG_DIR = "log"
LOG_FORMAT = "%(asctime)s - %(funcName)s - %(levelname)s - %(message)s"
LOG_FORMAT_ERROR = "%(asctime)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s"
MAX_BYTES = 8 * 1024 * 1024  # 8 MB
# MAX_BYTES = 300
BACKUP_COUNT = 5

# --- 确保日志目录存在 ---
os.makedirs(LOG_DIR, exist_ok=True)

# --- 标记以确保配置只运行一次 ---
_logging_configured = False

'''
log level
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0
'''

def get_logger(name: str):
    """
    获取一个经过配置的 logger 实例。
    这个函数会确保日志系统的基础配置只被执行一次。

    Args:
        name (str): 通常传入 __name__，用于标识日志来源模块。

    Returns:
        logging.Logger: 配置好的 logger 实例。
    """
    global _logging_configured
    if not _logging_configured:
        # 获取根 logger 进行配置
        root_logger = logging.getLogger()
        # root_logger.setLevel(logging.INFO)
        root_logger.setLevel(logging.DEBUG)

        # 1. 配置 app.log handler (INFO 级别)
        app_log_path = os.path.join(LOG_DIR, "app.log")
        debug_handler = RotatingFileHandler(
            app_log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(debug_handler)

        # 2. 同时配置 error.log handler (ERROR 级别)
        error_log_path = os.path.join(LOG_DIR, "error.log")
        error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(LOG_FORMAT_ERROR))
        root_logger.addHandler(error_handler)

        # 3. (可选) 配置控制台输出 handler
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.INFO)
        # console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        # root_logger.addHandler(console_handler)

        _logging_configured = True

        # 打印一条初始化信息
        # initial_logger = logging.getLogger(__name__)
        # initial_logger.debug("Logger has been configured.")

    return logging.getLogger(name)


# --- 示例用法 ---
if __name__ == "__main__":
    # 在不同的模块中，可以像下面这样获取 logger
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    logger1.debug("这是来自 module1 的一条 debug 信息。")
    logger1.warning("这是来自 module1 的一条 warning 信息。")

    logger2.info("这是来自 module2 的一条 info 信息。")
    logger2.error("这是来自 module2 的一条 error 信息。")

    # print(f"日志文件已生成在: {os.path.abspath(LOG_DIR)}")
