"""BDD #1207 FIX-T85 (2026-09-20) §4.3.1：OpenAPI 3.0 spec 自动生成

扫描 vendor/jeeflow/facade.py 的 _processXxx 方法, 提取 action 列表,
生成 OpenAPI 3.0 spec 到 docs/openapi.json
"""
import sys, os, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "vendor"))
sys.path.insert(0, ROOT)

from fastapi.openapi.utils import get_openapi

# 直接 import main 模块 (会触发 setup_vendor_path)
import importlib.util
spec = importlib.util.spec_from_file_location("main_app", os.path.join(ROOT, "main.py"))
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)
app = main_mod.app

# 自定义 OpenAPI: 展开 /wf/{action} 为 48 个具体路径
action_methods = {}
facade_path = os.path.join(ROOT, "vendor", "jeeflow", "facade.py")
with open(facade_path) as f:
    src = f.read()
# 抓所有 _processXxx 或 _processXxx_yyy 方法
for m in re.finditer(r"async def (_process\w+)\(self, args: dict\)", src):
    action = m.group(1)[1:].replace("_", "/")  # 去掉前导 _
    action_methods[action] = True

# 生成
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="jeeFlow API",
        version="1.9.0+",
        description="私用定位的工作流引擎 API (BDD #1207 FIX-T85 §4.3.1)\n- 48 个 action 端点全部在 /wf/{action:path} 路由\n- 兼容 Phase 1+2 所有 endpoint",
        routes=app.routes,
    )
    # 展开 /wf/{action} 为具体 path
    new_paths = {}
    for path, path_item in openapi_schema.get("paths", {}).items():
        if path == "/wf/{action}":
            # 保留一个通用 path
            new_paths[path] = path_item
            for action in sorted(action_methods.keys()):
                new_paths[f"/wf/{action}"] = {
                    "post": {
                        "summary": action,
                        "description": f"Facade._process{action.replace('/', '_')}",
                        "requestBody": {
                            "required": False,
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "responses": {
                            "200": {
                                "description": "成功",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                            },
                            "99999999": {
                                "description": "业务异常 (见 docs/state.md)",
                            },
                        },
                    }
                }
        else:
            new_paths[path] = path_item
    openapi_schema["paths"] = new_paths
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["schemas"] = openapi_schema["components"].get("schemas", {})
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "code": {"type": "integer", "description": "0=成功, 99999999=失败"},
            "msg": {"type": "string"},
            "data": {"type": "object"},
        },
    }
    openapi_schema["components"]["schemas"]["InstanceState"] = {
        "type": "integer",
        "enum": [10, 20, 30, 40, 45, 50, 99],
        "description": "10=DOING, 20=DONE, 30=WITHDRAW, 40=INTERRUPT, 45=REJECT, 50=PENDING, 99=ABANDON",
    }
    openapi_schema["components"]["schemas"]["SubmitType"] = {
        "type": "integer",
        "enum": [0, 1, 2, 3, 4, 5, 6, 20],
        "description": "0=APPLY, 1=AGREE, 2=REJECT, 3=ROLLBACK, 4=JUMP, 5=RE_APPLY, 6=DELEGATE, 20=COUNTERSIGN_DISAGREE",
    }
    app.openapi_schema = openapi_schema
    return openapi_schema

schema = custom_openapi()
out_path = os.path.join(ROOT, "docs", "openapi.json")
with open(out_path, "w") as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)
print(f"OpenAPI spec 写入 {out_path}")
print(f"paths: {len(schema['paths'])}")
print(f"action endpoints: {sum(1 for p in schema['paths'] if p.startswith('/wf/'))}")
print(f"schemas: {len(schema['components']['schemas'])}")
