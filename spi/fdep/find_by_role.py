from spi.fdep.data import SPI_ROLE_TO_USERS


def SPI(payload, token={}) -> list:
    return SPI_ROLE_TO_USERS.get(payload.get("role_code", ""), [])


def pocketflow(payload, token={}) -> list:
    return SPI(payload, token)
