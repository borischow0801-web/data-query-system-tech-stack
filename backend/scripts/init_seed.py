"""
初始化基础数据：
- 管理员账号 admin / admin123
- 示例接口配置（dev / prod 各一套，便于开放 API 默认 envCode=prod 联调）
- 开放 API 演示客户端
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.user import DqUser
from app.models.interface_config import DqInterfaceConfig
from app.models.interface_param_template import DqInterfaceParamTemplate
from app.models.open_api_client import DqOpenApiClient
from app.db.base import Base


def _ensure_demo_interface(db: Session, env_code: str) -> None:
    iface = (
        db.query(DqInterfaceConfig)
        .filter(
            DqInterfaceConfig.interface_code == "province_case_push",
            DqInterfaceConfig.env_code == env_code,
        )
        .first()
    )
    if iface:
        return
    iface = DqInterfaceConfig(
        interface_code="province_case_push",
        interface_name="省办件归集数据下发(示例)",
        interface_category="示例",
        env_code=env_code,
        base_url="http://example.com/mock",
        request_path="/api/mock/province-case-push",
        request_method="POST",
        content_type="application/json",
        timeout_ms=5000,
        encrypt_mode="SM2_SM4",
        allow_open_api=1,
        status=1,
    )
    db.add(iface)
    db.flush()
    print(f"创建示例接口 province_case_push（环境 {env_code}）")
    tpl = DqInterfaceParamTemplate(
        interface_id=iface.id,
        param_code="sblsh",
        param_name="申办流水号",
        display_name="申办流水号",
        data_type="string",
        form_component="input",
        required_flag=1,
        sort_no=1,
    )
    db.add(tpl)


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False, future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        admin = db.query(DqUser).filter(DqUser.username == "admin").first()
        if not admin:
            admin = DqUser(
                username="admin",
                password_hash=get_password_hash("admin123"),
                real_name="管理员",
                status=1,
            )
            db.add(admin)
            print("创建管理员账号 admin / admin123")

        _ensure_demo_interface(db, "dev")
        _ensure_demo_interface(db, "prod")

        oa = db.query(DqOpenApiClient).filter(DqOpenApiClient.client_code == "demo_client").first()
        if not oa:
            oa = DqOpenApiClient(
                client_code="demo_client",
                client_name="演示对接系统",
                app_key="demo_app_key",
                app_secret_hash="demo_app_secret",
                status=1,
            )
            db.add(oa)
            print("创建开放 API 客户端 demo_app_key / demo_app_secret（见 docs/open-api-doc.md）")

        db.commit()
        print("初始化完成")


if __name__ == "__main__":
    main()
