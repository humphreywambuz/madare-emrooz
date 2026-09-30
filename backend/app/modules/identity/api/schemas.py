from pydantic import BaseModel, ConfigDict, Field


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OtpRequestBody(_Body):
    mobile: str = Field(min_length=1, max_length=32)


class OtpVerifyBody(_Body):
    mobile: str = Field(min_length=1, max_length=32)
    code: str = Field(min_length=1, max_length=16)


class RefreshTokenBody(_Body):
    refresh_token: str = Field(min_length=1, max_length=256)
