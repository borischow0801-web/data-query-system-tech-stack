"""参数模板管理服务：CRUD、批量保存与动态表单 schema 输出。"""
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import NotFoundError, ValidationError
from app.models.interface_param_template import DqInterfaceParamTemplate
from app.models.interface_config import DqInterfaceConfig


class ParameterTemplateService:
    def list_params(self, db: Session, interface_id: int) -> List[Dict[str, Any]]:
        rows = (
            db.query(DqInterfaceParamTemplate)
            .filter(
                DqInterfaceParamTemplate.interface_id == interface_id,
                DqInterfaceParamTemplate.deleted_flag == 0,
            )
            .order_by(DqInterfaceParamTemplate.sort_no, DqInterfaceParamTemplate.id)
            .all()
        )
        return [self._to_dict(r) for r in rows]

    def save_params_batch(
        self,
        db: Session,
        interface_id: int,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        差量保存（避免“逻辑删除仍占唯一键”导致 Duplicate entry）：
        - 现存记录（含 deleted=1）按 param_code 建索引
        - 入参 items：
          - 已存在：update 并把 deleted_flag 置 0（可“复活”旧行）
          - 不存在：insert
        - 未出现在入参中的现存有效记录：逻辑删除（deleted_flag=1）
        """
        items = items or []

        # 1) 入参校验：paramCode 不能为空、且不能重复
        seen: set[str] = set()
        normalized: List[Dict[str, Any]] = []
        for idx, item in enumerate(items):
            code = (item.get("paramCode") or "").strip()
            if not code:
                raise ValidationError("paramCode 不能为空")
            if code in seen:
                raise ValidationError(f"参数编码重复: {code}")
            seen.add(code)
            normalized.append({**item, "paramCode": code, "sortNo": item.get("sortNo") or (idx + 1)})

        # 2) 拉取现存记录（含 deleted=1），用于 update/复活
        rows = (
            db.query(DqInterfaceParamTemplate)
            .filter(DqInterfaceParamTemplate.interface_id == interface_id)
            .all()
        )
        by_code: dict[str, DqInterfaceParamTemplate] = {r.param_code: r for r in rows}

        # 3) upsert
        result: List[Dict[str, Any]] = []
        try:
            for item in normalized:
                code = item["paramCode"]
                row = by_code.get(code)
                if row:
                    # update + 复活
                    row.deleted_flag = 0
                    row.param_name = item.get("paramName") or code
                    row.display_name = item.get("displayName") or code
                    row.data_type = item.get("dataType", "string")
                    row.form_component = item.get("formComponent", "input")
                    row.required_flag = item.get("requiredFlag", 0)
                    row.default_value = item.get("defaultValue")
                    row.example_value = item.get("exampleValue")
                    row.placeholder_text = item.get("placeholderText")
                    row.validation_rule = item.get("validationRule")
                    row.request_path_expr = item.get("requestPathExpr")
                    row.sort_no = int(item.get("sortNo") or 0)
                    row.visible_flag = item.get("visibleFlag", 1)
                    row.queryable_flag = item.get("queryableFlag", 1)
                    row.analyzable_flag = item.get("analyzableFlag", 0)
                    row.exportable_flag = item.get("exportableFlag", 1)
                    row.remark = item.get("remark")
                    db.flush()
                    result.append(self._to_dict(row))
                else:
                    row = DqInterfaceParamTemplate(
                        interface_id=interface_id,
                        param_code=code,
                        param_name=item.get("paramName") or code,
                        display_name=item.get("displayName") or code,
                        data_type=item.get("dataType", "string"),
                        form_component=item.get("formComponent", "input"),
                        required_flag=item.get("requiredFlag", 0),
                        default_value=item.get("defaultValue"),
                        example_value=item.get("exampleValue"),
                        placeholder_text=item.get("placeholderText"),
                        validation_rule=item.get("validationRule"),
                        request_path_expr=item.get("requestPathExpr"),
                        sort_no=int(item.get("sortNo") or 0),
                        visible_flag=item.get("visibleFlag", 1),
                        queryable_flag=item.get("queryableFlag", 1),
                        analyzable_flag=item.get("analyzableFlag", 0),
                        exportable_flag=item.get("exportableFlag", 1),
                        remark=item.get("remark"),
                    )
                    db.add(row)
                    db.flush()
                    result.append(self._to_dict(row))

            # 4) 逻辑删除那些不在入参里的“当前有效”记录（deleted_flag=0）
            for r in rows:
                if r.deleted_flag == 0 and r.param_code not in seen:
                    r.deleted_flag = 1
            db.flush()
            return sorted(result, key=lambda x: x.get("sortNo") or 0)
        except IntegrityError as e:
            # 数据库唯一键冲突等
            raise ValidationError(f"参数模板保存失败（唯一键冲突/重复编码）：{e.orig}") from e

    def update_param(self, db: Session, param_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        row: DqInterfaceParamTemplate | None = (
            db.query(DqInterfaceParamTemplate)
            .filter(DqInterfaceParamTemplate.id == param_id, DqInterfaceParamTemplate.deleted_flag == 0)
            .first()
        )
        if not row:
            raise NotFoundError("参数模板不存在")
        mapping = {
            "paramCode": "param_code",
            "paramName": "param_name",
            "displayName": "display_name",
            "dataType": "data_type",
            "formComponent": "form_component",
            "requiredFlag": "required_flag",
            "defaultValue": "default_value",
            "exampleValue": "example_value",
            "placeholderText": "placeholder_text",
            "validationRule": "validation_rule",
            "requestPathExpr": "request_path_expr",
            "sortNo": "sort_no",
            "visibleFlag": "visible_flag",
            "queryableFlag": "queryable_flag",
            "analyzableFlag": "analyzable_flag",
            "exportableFlag": "exportable_flag",
            "remark": "remark",
        }
        for k, v in data.items():
            if k in mapping:
                setattr(row, mapping[k], v)
        db.flush()
        return self._to_dict(row)

    def delete_param(self, db: Session, param_id: int) -> None:
        row = (
            db.query(DqInterfaceParamTemplate)
            .filter(DqInterfaceParamTemplate.id == param_id, DqInterfaceParamTemplate.deleted_flag == 0)
            .first()
        )
        if not row:
            return
        row.deleted_flag = 1
        db.flush()

    def build_query_form_schema(self, db: Session, interface_id: int) -> Dict[str, Any]:
        """根据参数模板生成动态表单 schema。"""
        # 确认接口存在
        exists = (
            db.query(DqInterfaceConfig)
            .filter(DqInterfaceConfig.id == interface_id, DqInterfaceConfig.deleted_flag == 0)
            .first()
        )
        if not exists:
            raise NotFoundError("接口配置不存在")
        fields = self.list_params(db, interface_id)
        # schema 结构可供前端直接使用
        return {
            "interfaceId": interface_id,
            "fields": [
                {
                    "field": f["paramCode"],
                    "label": f["displayName"],
                    "dataType": f["dataType"],
                    "component": f["formComponent"],
                    "required": bool(f["requiredFlag"]),
                    "defaultValue": f.get("defaultValue"),
                    "placeholder": f.get("placeholderText"),
                    "options": (f.get("ext") or {}).get("options") if isinstance(f.get("ext"), dict) else None,
                }
                for f in fields
            ],
        }

    def _to_dict(self, p: DqInterfaceParamTemplate) -> Dict[str, Any]:
        return {
            "id": p.id,
            "interfaceId": p.interface_id,
            "paramCode": p.param_code,
            "paramName": p.param_name,
            "displayName": p.display_name,
            "dataType": p.data_type,
            "formComponent": p.form_component,
            "requiredFlag": p.required_flag,
            "defaultValue": p.default_value,
            "exampleValue": p.example_value,
            "placeholderText": p.placeholder_text,
            "validationRule": p.validation_rule,
            "requestPathExpr": p.request_path_expr,
            "sortNo": p.sort_no,
            "visibleFlag": p.visible_flag,
            "queryableFlag": p.queryable_flag,
            "analyzableFlag": p.analyzable_flag,
            "exportableFlag": p.exportable_flag,
            "remark": p.remark,
        }

