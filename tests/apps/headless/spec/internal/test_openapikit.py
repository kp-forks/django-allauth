from dataclasses import dataclass, field
from typing import Optional

from allauth.headless.spec.internal.openapikit import spec_for_dataclass


@dataclass
class ExampleDataclass:
    optional_integer: Optional[int]
    integer: int
    optional_string: Optional[str]
    string: str
    number: float = field(
        metadata={
            "description": "Some float",
            "example": "3.14",
        }
    )


def test_spec_for_dataclass():
    spec = spec_for_dataclass(ExampleDataclass)
    assert spec == (
        {
            "properties": {
                "integer": {
                    "type": "integer",
                },
                "number": {
                    "description": "Some float",
                    "example": "3.14",
                    "format": "float",
                    "type": "number",
                },
                "optional_integer": {
                    "type": "integer",
                },
                "optional_string": {
                    "type": "string",
                },
                "string": {
                    "type": "string",
                },
            },
            "required": [
                "integer",
                "string",
                "number",
            ],
            "type": "object",
        },
        {
            "number": "3.14",
        },
    )
