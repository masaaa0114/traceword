"""
run_job.py
ジョブ実行エントリーポイント

使い方:
  python run_job.py job01       # 競合・業界情報収集
  python run_job.py job02       # 朝会アジェンダ生成
  python run_job.py job03       # 週報生成
  python run_job.py job04       # SNSコンテンツ生成
  python run_job.py job05       # コードレビュー
  python run_job.py job06       # KPIアラート
  python run_job.py job07       # 月次レポート
  python run_job.py all_daily   # 日次ジョブ全部実行
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def run_job01():
    from jobs.job_01_research import run
    run()

def run_job02():
    from jobs.job_02_briefing import run
    run()

def run_job03():
    from jobs.job_03_06_07 import run as r
    from jobs.job_03_06_07 import run_monthly_report
    r()  # job_03 の run()

def run_job04():
    from jobs.job_04_sns import run
    run()

def run_job05():
    from jobs.job_05_code_review import run
    run()

def run_job06():
    from jobs.job_03_06_07 import run_kpi_alert
    run_kpi_alert()

def run_job07():
    from jobs.job_03_06_07 import run_monthly_report
    run_monthly_report()

def run_all_daily():
    """日次ジョブを順番に実行"""
    print("=== 日次ジョブ 一括実行 ===")
    run_job01()
    run_job02()
    run_job06()
    print("=== 日次ジョブ 完了 ===")

JOBS = {
    "job01": run_job01,
    "job02": run_job02,
    "job03": run_job03,
    "job04": run_job04,
    "job05": run_job05,
    "job06": run_job06,
    "job07": run_job07,
    "all_daily": run_all_daily,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python run_job.py [ジョブ名]")
        print("利用可能なジョブ:", ", ".join(JOBS.keys()))
        sys.exit(1)

    job_name = sys.argv[1]
    if job_name not in JOBS:
        print(f"不明なジョブ: {job_name}")
        print("利用可能なジョブ:", ", ".join(JOBS.keys()))
        sys.exit(1)

    print(f"実行: {job_name}")
    JOBS[job_name]()
