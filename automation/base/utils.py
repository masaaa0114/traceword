"""
base/utils.py
共通ユーティリティ
"""
import os
import logging
from datetime import datetime
import pytz

TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Asia/Tokyo"))

def now_jst() -> datetime:
    """日本時間の現在時刻"""
    return datetime.now(TIMEZONE)

def today_str() -> str:
    """今日の日付文字列 YYYY-MM-DD"""
    return now_jst().strftime("%Y-%m-%d")

def today_label() -> str:
    """日本語の日付ラベル（例：2026年5月26日（火））"""
    d = now_jst()
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    return f"{d.year}年{d.month}月{d.day}日（{weekdays[d.weekday()]}）"

def week_label() -> str:
    """週ラベル（例：2026年第21週）"""
    d = now_jst()
    return f"{d.year}年第{d.isocalendar()[1]}週"

def setup_logger(job_name: str) -> logging.Logger:
    """ジョブ用ロガーのセットアップ"""
    logger = logging.getLogger(job_name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
    return logger

def log_job_start(logger: logging.Logger, job_name: str) -> None:
    logger.info(f"=== {job_name} 開始 ===")

def log_job_end(logger: logging.Logger, job_name: str) -> None:
    logger.info(f"=== {job_name} 完了 ===")

def log_job_error(logger: logging.Logger, job_name: str, error: Exception) -> None:
    logger.error(f"=== {job_name} エラー: {error} ===")
