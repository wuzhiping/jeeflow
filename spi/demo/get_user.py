from spi.demo.data import SPI_USERS


def SPI(payload, token={}) -> dict:
    uid = payload["uid"]
    info = SPI_USERS.get(uid, {"name": "用户" + uid, "post": "工程师"})
    return {"userId": uid, "realName": info["name"], "deptId": "D01", "deptName": "研发部",
            "postId": "P01", "postName": info["post"]}


def pocketflow(payload, token={}) -> dict:
    return SPI(payload, token)