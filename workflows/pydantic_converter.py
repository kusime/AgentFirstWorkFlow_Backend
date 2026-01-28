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
        """Convert a standard JSON payload back to a Pydantic object."""
        if type_hint and issubclass(type_hint, BaseModel):
            data = payload.data.decode("utf-8")
            # Deserialize using the type hint class
            return type_hint.model_validate_json(data) if hasattr(type_hint, "model_validate_json") else type_hint.parse_raw(data)
        
        # Fallback if no type hint is provided (returns dict)
        return json.loads(payload.data.decode("utf-8"))

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
