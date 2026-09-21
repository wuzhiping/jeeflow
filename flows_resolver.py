"""解析本仓流程定义目录（维护者与用户统一入口）。

目录布局：
  flows/         适配 spi.dev 的版本（运行时引擎默认加载，作为种子流程）
  flows_demo/    原 Java 源副本（保留作为对照参考，不参与运行时加载）

唯一编辑源是 jeeflow-java 仓的 test/resources/flows/。本仓 flows_demo/ 是其精确副本，
flows/ 由 flows_demo/ 经"用户/组织相关设定"适配生成后入库 commit。

dir() 的语义：
  1. 环境变量 JEEFLOW_FLOWS_DIR 显式覆盖（容器/特殊部署）
  2. 否则从当前工作目录向上找第一个含 flows/（且有 .json）的目录 = 本仓根
  3. 若本仓根的兄弟目录里有 Java 源（维护者机器）→ 精确镜像进本仓 flows_demo/
     （拷贝所有 .json + 删除本仓多出的孤儿 .json，防 id 按文件名排序错位）
  4. 始终返回本仓 flows/ 路径 —— 所有读取点只读这里，Java 仓不再被直接读取

放在仓根（不进 jeeflow* 发布包）：main.py / main_pg.py 已把仓根 insert 进 sys.path，
pytest 从仓根跑，两者都能 import flows_resolver。
"""
import os

# java 源目录相对本仓根的位置（jeeflow-java 与本仓是 jeeflow-hub 下的兄弟目录）
_JAVA_FLOWS_REL = os.path.join("..", "jeeflow-java", "jeeflow-core", "src", "test", "resources", "flows")


def dir() -> str:
    """返回本仓 flows/ 绝对路径（spi.dev 适配版, 运行时引擎加载此目录）；维护者机器上会先把 Java 源精确镜像进 flows_demo/。"""
    env = os.environ.get("JEEFLOW_FLOWS_DIR")
    if env:
        return env
    root = _find_flows_root(os.getcwd())
    if root is None:
        raise FileNotFoundError("flows_resolver: no flows/ directory found from %s" % os.getcwd())
    _mirror(root)
    return os.path.join(root, "flows")


def _find_flows_root(start):
    """从 start 向上找第一个含 flows/ 且内有 .json 的目录（本仓根）。"""
    d = os.path.abspath(start)
    while True:
        if _has_flows(d):
            return d
        parent = os.path.dirname(d)
        if parent == d:  # 到文件系统顶
            return None
        d = parent


def _has_flows(d):
    fdir = os.path.join(d, "flows")
    if not os.path.isdir(fdir):
        return False
    return any(f.endswith(".json") for f in os.listdir(fdir))


def _mirror(root):
    """若 Java 源存在则精确镜像到本仓 flows_demo/（拷所有 + 删孤儿），不存在则原样返回。

    注意：镜像目标是 flows_demo/（保留 Java 原版），不是 flows/（spi.dev 适配版, 由 flows_demo/ 派生, 不应被覆盖）。
    """
    import shutil
    src = os.path.join(root, _JAVA_FLOWS_REL)
    dst = os.path.join(root, "flows_demo")
    if not os.path.isdir(src):  # 用户单仓 / 容器：无 Java 源，跳过镜像
        return
    os.makedirs(dst, exist_ok=True)
    src_names = set()
    for f in os.listdir(src):
        if not f.endswith(".json"):
            continue
        src_names.add(f)
        shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))
    # 孤儿清理：本仓有、Java 源已无的 .json（防 id 错位）
    for f in os.listdir(dst):
        if f.endswith(".json") and f not in src_names:
            os.remove(os.path.join(dst, f))