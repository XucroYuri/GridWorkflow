import logging


def get_logger(level: str = "INFO") -> logging.Logger:
    """创建或获取应用 Logger，使用基础控制台输出。"""
    logger = logging.getLogger("gridworkflow")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level.upper())
    return logger


