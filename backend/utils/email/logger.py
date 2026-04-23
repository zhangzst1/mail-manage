"""
邮件处理模块的日志配置。
"""

import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

# 日志级别
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def ensure_log_dir() -> Path:
    """确保日志目录存在，并返回绝对路径。"""
    log_dir = Path(__file__).resolve().parents[2] / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def create_safe_file_handler(file_path: Path, level: int, formatter: logging.Formatter):
    """创建可回退的文件日志处理器，避免 Windows 文件锁导致启动失败。"""
    candidates = [
        file_path,
        file_path.with_name(f"{file_path.stem}_{os.getpid()}{file_path.suffix}"),
        Path(tempfile.gettempdir()) / file_path.name,
        Path(tempfile.gettempdir()) / f"{file_path.stem}_{os.getpid()}{file_path.suffix}",
    ]
    last_error = None

    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(candidate, encoding='utf-8')
            handler.setLevel(level)
            handler.setFormatter(formatter)
            return handler, None
        except OSError as exc:
            last_error = exc

    return None, last_error


def configure_logger():
    """配置邮件处理模块的日志。"""
    log_dir = ensure_log_dir()
    logger = logging.getLogger('email_utils')

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    current_date = datetime.now().strftime("%Y%m%d")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    detail_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    main_log_file = log_dir / f"email_assistant_{current_date}.log"
    file_handler, file_error = create_safe_file_handler(main_log_file, logging.INFO, detail_formatter)
    if file_handler:
        logger.addHandler(file_handler)

    error_log_file = log_dir / f"email_assistant_error_{current_date}.log"
    error_handler, error_file_error = create_safe_file_handler(error_log_file, logging.ERROR, detail_formatter)
    if error_handler:
        logger.addHandler(error_handler)

    logger.propagate = False

    if file_error:
        logger.warning(f"主日志文件不可写，已降级到其他日志目标: {file_error}")
    if error_file_error:
        logger.warning(f"错误日志文件不可写，已降级到其他日志目标: {error_file_error}")

    return logger


logger = configure_logger()


def log_email_start(email_address, email_id):
    """记录开始处理邮箱的日志。"""
    logger.info(f"===== 开始处理邮箱 {email_address} (ID:{email_id}) =====")


def log_email_complete(email_address, email_id, total_emails, processed, saved):
    """记录邮箱处理完成的日志。"""
    logger.info(f"===== 邮箱处理完成: {email_address} (ID:{email_id}) =====")
    logger.info(f"总邮件数: {total_emails}, 成功处理: {processed}, 新增: {saved}")


def log_email_error(email_address, email_id, error):
    """记录邮箱处理错误的日志。"""
    logger.error(f"===== 邮箱处理错误: {email_address} (ID:{email_id}) =====")
    logger.error(f"错误详情: {str(error)}")


def log_message_processing(message_id, index, total, subject):
    """记录单封邮件处理的日志。"""
    logger.debug(f"处理邮件 {index}/{total} (ID:{message_id}) - 主题: {subject[:50]}")


def log_message_error(message_id, error):
    """记录单封邮件处理错误的日志。"""
    logger.error(f"处理邮件 (ID:{message_id}) 失败: {str(error)}")


def log_progress(email_id, progress, message):
    """记录进度信息。"""
    if progress in [0, 25, 50, 75, 100]:
        logger.info(f"邮箱 (ID:{email_id}) 进度: {progress}% - {message}")


def timing_decorator(func):
    """用于测量函数执行时间的装饰器。"""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"函数 {func.__name__} 执行时间: {execution_time:.2f}秒")
        return result

    return wrapper
