import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str):
    with open(os.path.join(_BASE, name), encoding="utf-8") as f:
        return json.load(f)


SPI_USERS: dict = _load("FDEP_USERS.json")
SPI_ROLES: dict = _load("FDEP_ROLES.json")
SPI_DICTS: dict = _load("FDEP_DICTS.json")
SPI_ROLE_TO_USERS: dict = _load("FDEP_ROLE_TO_USERS.json")
SPI_DEPT_LEADERS: dict = _load("FDEP_DEPT_LEADERS.json")
SPI_DEPT_MAIN_LEADERS: dict = _load("FDEP_DEPT_MAIN_LEADERS.json")
SPI_FIND_USER_BY_ROLE_DEPT: dict = _load("FDEP_FIND_USER_BY_ROLE_DEPT.json")
