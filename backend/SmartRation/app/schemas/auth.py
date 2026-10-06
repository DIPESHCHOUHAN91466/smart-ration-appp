"""Auth request rules (DataAnnotations-equivalent) and response models for OpenAPI.

Request bodies are validated with app.core.validation so error messages match
the C# API word for word; the Pydantic models below document the contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.validation import email_address, phone, required, string_length
from app.security.password_policy import MAX_LENGTH, MIN_LENGTH

LOGIN_RULES = {"Email": [required, email_address], "Password": [required]}

REGISTER_RULES = {
    "FullName": [required, string_length(150, 2)],
    "Email": [required, email_address, string_length(200)],
    "MobileNumber": [required, phone, string_length(20)],
    "Password": [required, string_length(MAX_LENGTH, MIN_LENGTH)],   # + app.security.password_policy
}

REFRESH_RULES = {"RefreshToken": [required]}

OTP_REQUEST_RULES = {"MobileNumber": [required, string_length(20)]}

OTP_VERIFY_RULES = {"MobileNumber": [required, string_length(20)], "Otp": [required, string_length(6, 6)]}


class LoginRequest(BaseModel):
    email: str = Field(examples=["rural@example.com"])
    password: str


class RegisterRequest(BaseModel):
    """Self-registration always creates a Rural User account."""
    fullName: str = Field(min_length=2, max_length=150)
    email: str = Field(max_length=200)
    mobileNumber: str = Field(max_length=20)
    password: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH,
                          description="At least 12 characters; not a common password; not built from the email, mobile or name")
    consentToPrivacyPolicy: bool = Field(False, description="the person agreed to the privacy policy (recorded in the audit log)")


class RefreshRequest(BaseModel):
    refreshToken: str


class OtpLoginRequest(BaseModel):
    mobileNumber: str = Field(examples=["9000000001"], description="10-digit mobile; spaces, +91 or a leading 0 are accepted")


class OtpLoginVerify(BaseModel):
    mobileNumber: str = Field(examples=["9000000001"])
    otp: str = Field(min_length=6, max_length=6, examples=["123456"])


class OtpSent(BaseModel):
    mobileMasked: str
    expiresInSeconds: int
    resendAfterSeconds: int
    demoOtpValue: str | None = Field(description="Development demo mode only; always null elsewhere")


class OtpSentEnvelope(BaseModel):
    success: bool
    message: str
    data: OtpSent | None
    errors: list[str] | None


class UserSummary(BaseModel):
    id: int
    fullName: str
    email: str
    mobileNumber: str
    role: str = Field(description="RuralUser | ShopOwner | GovernmentOfficial | Admin")
    rationShopId: int | None


class AuthData(BaseModel):
    accessToken: str = Field(description="JWT (HS256), valid 15 minutes")
    refreshToken: str = Field(description="Opaque; single use (rotated on refresh), valid 7 days")
    accessTokenExpiresAt: str = Field(description="UTC, e.g. 2026-09-24T04:43:04.4875895Z")
    user: UserSummary


class AuthEnvelope(BaseModel):
    success: bool
    message: str
    data: AuthData | None
    errors: list[str] | None


class EmptyEnvelope(BaseModel):
    success: bool
    message: str
    data: None = None
    errors: list[str] | None = None
