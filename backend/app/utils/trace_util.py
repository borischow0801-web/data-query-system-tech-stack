"""链路追踪 ID 生成。"""
import uuid


def generate_trace_id() -> str:
    return uuid.uuid4().hex
