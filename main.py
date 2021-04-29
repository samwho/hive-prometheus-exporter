import os
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from prometheus_client import start_http_server, Counter, Gauge, Info
from pyhiveapi import Hive

PORT = os.getenv("PORT", 8888)
HIVE_USERNAME = os.getenv("HIVE_USERNAME")
HIVE_PASSWORD = os.getenv("HIVE_PASSWORD")


def poll():
    print("polling...")


def main():
    if HIVE_USERNAME is None:
        print("HIVE_USERNAME environment variable is not set")
        exit(1)

    if HIVE_PASSWORD is None:
        print("HIVE_PASSWORD environment variable is not set")
        exit(1)

    start_http_server(PORT)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        poll,
        id="poll",
        trigger="interval",
        seconds=60,
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(),
    )
    scheduler.start()


if __name__ == "__main__":
    main()
