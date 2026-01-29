import json
from typing import Any, Optional, Type
from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DefaultPayloadConverter,
    EncodingPayloadConverter,
    PayloadConverter,
)
from pydantic import BaseModel

class PydanticJSONPayloadConverter(EncodingPayloadConverter):
    """
    A custom payload converter that handles Pydantic models.
    It serializes them to JSON and deserializes them back to the specific Pydantic model class.
    """
    
    @property
    def encoding(self) -> str:
        # We use a custom encoding tag to distinguish this from standard JSON
        return "json/pydantic"

    def to_payload(self, value: Any) -> Optional[Payload]:
        """Convert a Pydantic object to a Temporal Payload."""
        if isinstance(value, BaseModel):
            # Serialize Pydantic model to JSON string
            json_str = value.model_dump_json() if hasattr(value, "model_dump_json") else value.json()
            return Payload(
                metadata={"encoding": self.encoding.encode("utf-8")},
                data=json_str.encode("utf-8"),
            )
        return None

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        """Convert a Pydantic JSON payload back to a Pydantic object."""
        # 只处理我们自己编码的payload（"json/pydantic"）
        payload_encoding = payload.metadata.get("encoding", b"").decode("utf-8")
        if payload_encoding != self.encoding:
            return None  # 让其他converter处理
            
        data_str = payload.data.decode("utf-8")
        
        # 如果有type hint且是BaseModel，使用它
        if type_hint and issubclass(type_hint, BaseModel):
            return type_hint.model_validate_json(data_str) if hasattr(type_hint, "model_validate_json") else type_hint.parse_raw(data_str)
        
        # 没有type hint时，返回dict（但这不应该发生在正确配置的workflow中）
        return json.loads(data_str)


class PydanticDataConverter(CompositePayloadConverter):
    """
    The main DataConverter to use in Client and Worker.
    It includes the standard converters PLUS our custom Pydantic one.
    Important: The Pydantic converter must come BEFORE the default JSON converter.
    """
    def __init__(self):
        super().__init__(
            # Start with our custom Pydantic converter
            PydanticJSONPayloadConverter(),
            # Include all default converters (Binary, Protobuf, JSON, etc.)
            *DefaultPayloadConverter.default_encoding_payload_converters,
        )
