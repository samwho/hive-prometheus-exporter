from datetime import datetime
import os
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

from apscheduler.schedulers.blocking import BlockingScheduler
from prometheus_client import start_http_server, Counter, Gauge, Info
from pyhiveapi import Hive, SMS_REQUIRED, API
from dpath.util import search

PORT = int(os.getenv("PORT", "8888"))
HIVE_USERNAME = os.getenv("HIVE_USERNAME")
HIVE_PASSWORD = os.getenv("HIVE_PASSWORD")
POLLING_INTERVAL_SECONDS = os.getenv("POLLING_INTERVAL_SECONDS", 60)

ONLINE = Gauge("hive_online", "", ("home_id", "home_name", "type", "id", "name"))
VERSION = Gauge(
    "hive_version",
    "",
    ("home_id", "home_name", "type", "id", "name", "version"),
)
MODEL = Gauge(
    "hive_model",
    "",
    ("home_id", "home_name", "type", "id", "name", "model"),
)
UPGRADE_AVAILABLE = Gauge(
    "hive_upgrade_available",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)
UPGRADING = Gauge(
    "hive_upgrading",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)
UPGRADE_STATUS = Gauge(
    "hive_upgrade_status",
    "",
    ("home_id", "home_name", "type", "id", "name", "status"),
)
POWER = Gauge(
    "hive_power",
    "",
    ("home_id", "home_name", "type", "id", "name", "power"),
)
SIGNAL = Gauge(
    "hive_signal",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)
BATTERY = Gauge(
    "hive_battery",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

TRV_TEMPERATURE = Gauge(
    "hive_trv_temperature",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

TRV_WORKING = Gauge(
    "hive_trv_working",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

TRV_TARGET = Gauge(
    "hive_trv_target",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

TRV_MODE = Gauge(
    "hive_trv_mode",
    "",
    ("home_id", "home_name", "type", "id", "name", "mode"),
)

TRV_AUTO_BOOSE_TARGET = Gauge(
    "hive_trv_auto_boost_target",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)


def get_homes(client):
    url = f"https://beekeeper-uk.hivehome.com/1.0/nodes/all?"
    response = client.request("GET", url)
    return response.json()["homes"]["homes"]


def get_products(client, home_id=None):
    url = f"https://beekeeper-uk.hivehome.com/1.0/products?"
    if home_id:
        url += f"homeId={home_id}&"
    response = client.request("GET", url)
    return response.json()


def get_devices(client, home_id=None):
    url = f"https://beekeeper-uk.hivehome.com/1.0/devices?"
    if home_id:
        url += f"homeId={home_id}&"
    response = client.request("GET", url)
    return response.json()


def get_actions(client, home_id=None):
    url = f"https://beekeeper-uk.hivehome.com/1.0/actions?"
    if home_id:
        url += f"homeId={home_id}&"
    response = client.request("GET", url)
    return response.json()


def handle_device(home, device):
    if state := device.get("state", None):
        ONLINE.labels(
            home["id"],
            home["name"],
            device["type"],
            device["id"],
            state["name"],
        ).set(1 if device["props"].get("online", False) else 0)

        if props := device.get("props", None):
            VERSION.labels(
                home["id"],
                home["name"],
                device["type"],
                device["id"],
                state["name"],
                props["version"],
            ).set(1)

            MODEL.labels(
                home["id"],
                home["name"],
                device["type"],
                device["id"],
                state["name"],
                props["model"],
            ).set(1)

            POWER.labels(
                home["id"],
                home["name"],
                device["type"],
                device["id"],
                state["name"],
                props["power"],
            ).set(1)

            if signal := props.get("signal", None):
                SIGNAL.labels(
                    home["id"],
                    home["name"],
                    device["type"],
                    device["id"],
                    state["name"],
                ).set(signal)

            if battery := props.get("battery", None):
                BATTERY.labels(
                    home["id"],
                    home["name"],
                    device["type"],
                    device["id"],
                    state["name"],
                ).set(battery)

            if upgrade := props.get("upgrade", None):
                UPGRADE_AVAILABLE.labels(
                    home["id"],
                    home["name"],
                    device["type"],
                    device["id"],
                    state["name"],
                ).set(1 if upgrade.get("available", False) else 0)

                UPGRADING.labels(
                    home["id"],
                    home["name"],
                    device["type"],
                    device["id"],
                    state["name"],
                ).set(1 if upgrade.get("upgrading", False) else 0)

                if status := upgrade.get("status", None):
                    UPGRADE_STATUS.labels(
                        home["id"],
                        home["name"],
                        device["type"],
                        device["id"],
                        state["name"],
                        status,
                    ).set(1)


def handle_product(home, product):
    if product["type"] == "trvcontrol":
        handle_trvcontrol(home, product)


def handle_trvcontrol(home, product):
    if state := product.get("state", None):
        if target := state.get("target", None):
            TRV_TARGET.labels(
                home["id"],
                home["name"],
                product["type"],
                product["id"],
                state["name"],
            ).set(target)

        if mode := state.get("mode", None):
            TRV_MODE.labels(
                home["id"],
                home["name"],
                product["type"],
                product["id"],
                state["name"],
                mode,
            ).set(1)

        if auto_boost_target := state.get("autoBoostTarget", None):
            TRV_AUTO_BOOSE_TARGET.labels(
                home["id"],
                home["name"],
                product["type"],
                product["id"],
                state["name"],
            ).set(auto_boost_target)

        if props := product.get("props", None):
            TRV_WORKING.labels(
                home["id"],
                home["name"],
                product["type"],
                product["id"],
                state["name"],
            ).set(1 if props.get("working", False) else 0)

            if temperature := props.get("temperature", None):
                TRV_TEMPERATURE.labels(
                    home["id"],
                    home["name"],
                    product["type"],
                    product["id"],
                    state["name"],
                ).set(temperature)


def poll(client):
    logging.info("polling...")
    client.refreshTokens()
    for home in get_homes(client):
        for device in get_devices(client, home["id"]):
            handle_device(home, device)
        for product in get_products(client, home["id"]):
            handle_product(home, product)

    logging.info("polling done")


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
