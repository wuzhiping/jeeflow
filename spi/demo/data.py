import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str):
    with open(os.path.join(_BASE, name), encoding="utf-8") as f:
        return json.load(f)


SPI_USERS: dict = _load("DEMO_USERS.json")
SPI_ROLES: dict = _load("DEMO_ROLES.json")
SPI_DICTS: dict = _load("DEMO_DICTS.json")
SPI_ROLE_TO_USERS: dict = _load("DEMO_ROLE_TO_USERS.json")