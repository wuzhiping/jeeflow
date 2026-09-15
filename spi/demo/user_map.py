from spi.demo.data import SPI_USERS


def SPI(payload, token={}) -> dict:
    return {"USERS": SPI_USERS}


def pocketflow(payload, token={}) -> dict:
    return SPI(payload, token)