from typing import Any


def serialize_instance(obj: Any) -> Any:
    if hasattr(obj, "model_dump_json"):
        return obj.model_dump_json()
    raise TypeError(f"Type {type(obj)} not serializable")
