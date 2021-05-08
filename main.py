from datetime import datetime
import os
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

from apscheduler.schedulers.blocking import BlockingScheduler
from prometheus_client import start_http_server, Counter, Gauge, Info
from pyhiveapi import Hive, SMS_REQUIRED, API

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

MODE = Gauge(
    "hive_mode",
    "",
    ("home_id", "home_name", "type", "id", "name", "mode"),
)

MANUFACTURER = Gauge(
    "hive_manufacturer",
    "",
    ("home_id", "home_name", "type", "id", "name", "manufacturer"),
)

IN_USE = Gauge(
    "hive_in_use",
    "",
    ("home_id", "home_name", "type", "id", "name"),
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

WORKING = Gauge(
    "hive_working",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

TARGET = Gauge(
    "hive_target",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

BRIGHTNESS = Gauge(
    "hive_brightness",
    "",
    ("home_id", "home_name", "type", "id", "name", "group"),
)

MOTION = Gauge(
    "hive_motion",
    "",
    ("home_id", "home_name", "type", "id", "name"),
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

HOLIDAY_MODE_ACTIVE = Gauge(
    "hive_holiday_mode_active",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

HOLIDAY_MODE_ENABLED = Gauge(
    "hive_holiday_mode_enabled",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

TEMPERATURE = Gauge(
    "hive_temperature",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

SCHEDULE_OVERRIDE = Gauge(
    "hive_schedule_override",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

AUTO_BOOST_ACTIVE = Gauge(
    "hive_auto_boost_active",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

AUTO_BOOST_TARGET = Gauge(
    "hive_auto_boost_target",
    "",
    ("home_id", "home_name", "type", "id", "name"),
)

AUTO_BOOST_DURATION = Gauge(
    "hive_auto_boost_duration",
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
    if state := product.get("state", None):
        if mode := state.get("mode", None):
            MODE.labels(
                home["id"],
                home["name"],
                product["type"],
                product["id"],
                state["name"],
                mode,
            ).set(1)

        if brightness := state.get("brightness", None):
            BRIGHTNESS.labels(
                home["id"],
                home["name"],
                product["type"],
                product["id"],
                state["name"],
                "true" if state.get("isGroup", False) else "false",
            ).set(brightness)

        if target := state.get("target", None):
            TARGET.labels(
                home["id"],
                home["name"],
                product["type"],
                product["id"],
                state["name"],
            ).set(target)

        if props := product.get("props", None):
            if motion := props.get("motion", None):
                if status := motion.get("status", None):
                    MOTION.labels(
                        home["id"],
                        home["name"],
                        product["type"],
                        product["id"],
                        state["name"],
                    ).set(1 if status else 0)

            if model := props.get("model", None):
                MODEL.labels(
                    home["id"],
                    home["name"],
                    product["type"],
                    product["id"],
                    state["name"],
                    model,
                ).set(1)

            if manufacturer := props.get("manufacturer", None):
                MANUFACTURER.labels(
                    home["id"],
                    home["name"],
                    product["type"],
                    product["id"],
                    state["name"],
                    manufacturer,
                ).set(1)

            if in_use := props.get("inUse", None):
                IN_USE.labels(
                    home["id"],
                    home["name"],
                    product["type"],
                    product["id"],
                    state["name"],
                ).set(1 if in_use else 0)

            if temperature := props.get("temperature", None):
                TEMPERATURE.labels(
                    home["id"],
                    home["name"],
                    product["type"],
                    product["id"],
                    state["name"],
                ).set(temperature)

            if working := props.get("working", None):
                WORKING.labels(
                    home["id"],
                    home["name"],
                    product["type"],
                    product["id"],
                    state["name"],
                ).set(1 if working else 0)

            if schedule_override := props.get("scheduleOverride", None):
                SCHEDULE_OVERRIDE.labels(
                    home["id"],
                    home["name"],
                    product["type"],
                    product["id"],
                    state["name"],
                ).set(1 if schedule_override else 0)

            if auto_boost := props.get("autoBoost", None):
                if auto_boost_target := auto_boost.get("target", None):
                    AUTO_BOOST_TARGET.labels(
                        home["id"],
                        home["name"],
                        product["type"],
                        product["id"],
                        state["name"],
                    ).set(auto_boost_target)

                if auto_boost_active := auto_boost.get("active", None):
                    AUTO_BOOST_ACTIVE.labels(
                        home["id"],
                        home["name"],
                        product["type"],
                        product["id"],
                        state["name"],
                    ).set(1 if auto_boost_active else 0)

                if auto_boost_duration := auto_boost.get("duration", None):
                    AUTO_BOOST_DURATION.labels(
                        home["id"],
                        home["name"],
                        product["type"],
                        product["id"],
                        state["name"],
                    ).set(auto_boost_duration)

            if holiday_mode := props.get("holidayMode", None):
                if holiday_mode_active := holiday_mode.get("active", None):
                    HOLIDAY_MODE_ACTIVE.labels(
                        home["id"],
                        home["name"],
                        product["type"],
                        product["id"],
                        state["name"],
                    ).set(1 if holiday_mode_active else 0)

                if holiday_mode_enabled := holiday_mode.get("enabled", None):
                    HOLIDAY_MODE_ENABLED.labels(
                        home["id"],
                        home["name"],
                        product["type"],
                        product["id"],
                        state["name"],
                    ).set(1 if holiday_mode_enabled else 0)


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
