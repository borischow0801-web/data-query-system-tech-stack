"""
导入四个接口的“结果展示配置”（可维护）。

设计：
- 使用 dq_interface_config.response_mapping_template 存储 result config（JSON）
- 查询结果解析、导出、统计都读取此配置

运行：
  cd backend
  .venv/bin/python scripts/init_result_configs.py
"""

from __future__ import annotations

import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# 确保 backend 在 path 中（允许从任意目录运行）
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.core.config import get_settings
from app.models.interface_config import DqInterfaceConfig
from app.db.base import Base


SEED_CONFIGS: dict[str, dict] = {
    # 1) 根据部门/区划查询政务服务事项办件列表
    "getBusinessListByDeptOrRegion": {
        "result_mode": "list",
        "listPath": "data.data",
        "totalPath": "data.total",
        "columns": [
            {"field": "projid", "label": "申办编号", "sortNo": 1, "visible": True, "minWidth": 120},
            {"field": "orgbusno", "label": "原系统流水号", "sortNo": 2, "visible": True, "minWidth": 140},
            {"field": "itemname", "label": "事项名称", "sortNo": 3, "visible": True, "minWidth": 200},
            {"field": "acceptdeptname", "label": "受理单位", "sortNo": 4, "visible": True, "minWidth": 160},
            {"field": "applydate", "label": "申请时间", "sortNo": 5, "visible": True, "minWidth": 140},
        ],
        "stats": {
            "count": True,
            "groupBy": [{"field": "acceptdeptname", "label": "按受理单位"}],
            "timeTrend": {"field": "applydate", "granularity": "day"},
            "topN": [{"field": "itemname", "label": "事项 Top5", "n": 5}],
        },
    },
    # 2) 根据办件流水号获取办件详细信息
    "getBusinessInfoByProjId": {
        "result_mode": "detail",
        "detailRootPath": "data",
        "detailSections": [
            {"key": "basic", "title": "基本信息", "path": "data.basic"},
            {"key": "proc", "title": "办理过程", "path": "data.proc"},
            {"key": "specialNode", "title": "特别程序", "path": "data.specialNode"},
            {"key": "done", "title": "办结信息", "path": "data.done"},
            {"key": "file", "title": "材料信息", "path": "data.file"},
        ],
    },
    # 3) 根据部门/区划查询一件事办件列表
    "getChainListByDeptOrRegion": {
        "result_mode": "list",
        "listPath": "data.data",
        "totalPath": "data.total",
        "columns": [
            {"field": "projectno", "label": "主题服务办件编码", "sortNo": 1, "visible": True, "minWidth": 160},
            {"field": "taskname", "label": "主题名称", "sortNo": 2, "visible": True, "minWidth": 200},
            {"field": "deptname", "label": "牵头部门", "sortNo": 3, "visible": True, "minWidth": 160},
            {"field": "applytime", "label": "申报时间", "sortNo": 4, "visible": True, "minWidth": 140},
        ],
        "stats": {
            "count": True,
            "groupBy": [{"field": "deptname", "label": "按牵头部门"}],
            "timeTrend": {"field": "applytime", "granularity": "day"},
            "topN": [{"field": "taskname", "label": "主题 Top5", "n": 5}],
        },
    },
    # 4) 根据主题服务办件编码获取一件事详细信息
    "getChainInfoByProjectNo": {
        "result_mode": "detail",
        "detailRootPath": "data",
        "detailSections": [
            {"key": "chainBasic", "title": "基本信息", "path": "data.chainBasic"},
            {"key": "chainProc", "title": "过程信息", "path": "data.chainProc"},
            {"key": "chainDone", "title": "办结信息", "path": "data.chainDone"},
            {"key": "chainFile", "title": "材料信息", "path": "data.chainFile"},
            {"key": "chainSingle", "title": "单事项信息", "path": "data.chainSingle"},
        ],
    },
}


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        for iface_code, cfg in SEED_CONFIGS.items():
            row = (
                db.query(DqInterfaceConfig)
                .filter(DqInterfaceConfig.interface_code == iface_code, DqInterfaceConfig.deleted_flag == 0)
                .first()
            )
            if not row:
                # 仅导入配置，不强行创建接口（避免覆盖你的真实配置）
                print(f"跳过：未找到接口配置 interface_code={iface_code}")
                continue
            row.response_mapping_template = json.dumps(cfg, ensure_ascii=False)
            print(f"写入结果配置：{iface_code}")
        db.commit()
        print("结果配置导入完成")


if __name__ == "__main__":
    main()

