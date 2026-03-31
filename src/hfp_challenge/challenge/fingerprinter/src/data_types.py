from pydantic import BaseModel, Field


class FingerprintInput(BaseModel):
    products: dict = Field(
        ...,
        title="Products",
        description="Raw FingerprintJS products data.",
    )


class FingerprintOutput(BaseModel):
    fingerprint: str = Field(
        ...,
        title="Fingerprint",
        description="Unique fingerprint identifier.",
    )
    is_new: bool = Field(
        ...,
        title="Is New",
        description="Whether this is a new fingerprint.",
    )
    payload: dict = Field(
        ...,
        title="Payload",
        description="Output of a preprocessing step.",
    )


__all__ = [
    "FingerprintInput",
    "FingerprintOutput",
]
