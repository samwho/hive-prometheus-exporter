import os
from datetime import datetime
from pprint import pprint

from apscheduler.schedulers.blocking import BlockingScheduler
from prometheus_client import start_http_server, Counter, Gauge, Info
from pyhiveapi import Hive, SMS_REQUIRED, Auth, API

PORT = os.getenv("PORT", 8888)
HIVE_USERNAME = os.getenv("HIVE_USERNAME")
HIVE_PASSWORD = os.getenv("HIVE_PASSWORD")
POLLING_INTERVAL_SECONDS = os.getenv("POLLING_INTERVAL_SECONDS", 60)

SESSION = None
TOKENS = None


def poll(client):
    client.refreshTokens()
    data = client.getAll()
    pprint(data)


def main():
    if HIVE_USERNAME is None:
        print("HIVE_USERNAME environment variable is not set")
        exit(1)

    if HIVE_PASSWORD is None:
        print("HIVE_PASSWORD environment variable is not set")
        exit(1)

    hive = Hive(username=HIVE_USERNAME, password=HIVE_PASSWORD)
    session = hive.login()

    if session.get("ChallengeName") == SMS_REQUIRED:
        print("2FA not supported")
        exit(1)

    if "AuthenticationResult" not in session:
        print("authentication unsuccessful")
        exit(1)

    client = API(hive)
    pprint(client.session.tokens.tokenData)

    start_http_server(PORT)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        lambda: poll(client),
        id="poll",
        trigger="interval",
        seconds=POLLING_INTERVAL_SECONDS,
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(),
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
