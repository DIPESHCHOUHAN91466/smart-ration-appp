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

PASSWORD_CHANGE_RULES = {"CurrentPassword": [required, string_length(MAX_LENGTH)],
                         "NewPassword": [required, string_length(MAX_LENGTH, MIN_LENGTH)]}

PASSWORD_RESET_REQUEST_RULES = OTP_REQUEST_RULES

MFA_SETUP_RULES = {"Password": [required, string_length(MAX_LENGTH)]}
MFA_CODE_RULES = {"Code": [required, string_length(6, 6)]}
MFA_DISABLE_RULES = {"Password": [required, string_length(MAX_LENGTH)], "Code": [required, string_length(6, 6)]}
MFA_VERIFY_RULES = {"MfaToken": [required, string_length(2000)], "Code": [required, string_length(6, 6)]}

PASSWORD_RESET_CONFIRM_RULES = {"MobileNumber": [required, string_length(20)], "Otp": [required, string_length(6, 6)],
                                "NewPassword": [required, string_length(MAX_LENGTH, MIN_LENGTH)]}


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
    refreshToken: str = Field(description="Body mode only; in cookie mode (X-Auth-Mode: cookie) send {} and the cookie is used")


class OtpLoginRequest(BaseModel):
    mobileNumber: str = Field(examples=["9000000001"], description="10-digit mobile; spaces, +91 or a leading 0 are accepted")


class OtpLoginVerify(BaseModel):
    mobileNumber: str = Field(examples=["9000000001"])
    otp: str = Field(min_length=6, max_length=6, examples=["123456"])


class PasswordChangeRequest(BaseModel):
    currentPassword: str
    newPassword: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH,
                             description="At least 12 characters; not common; not built from the email, mobile or name")


class PasswordResetRequest(BaseModel):
    mobileNumber: str = Field(examples=["9000000001"], description="The account's registered mobile number")


class PasswordResetConfirm(BaseModel):
    mobileNumber: str = Field(examples=["9000000001"])
    otp: str = Field(min_length=6, max_length=6)
    newPassword: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH)


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
    refreshToken: str | None = Field(description="Opaque; single use (rotated on refresh), valid 7 days. null in cookie mode "
                                            "(header X-Auth-Mode: cookie): it is then only in the HttpOnly cookie sr_refresh")
    accessTokenExpiresAt: str = Field(description="UTC, e.g. 2026-09-24T04:43:04.4875895Z")
    user: UserSummary


class AuthEnvelope(BaseModel):
    success: bool
    message: str
    data: AuthData | None
    errors: list[str] | None


class MfaChallenge(BaseModel):
    """The password was right; the account uses two-factor sign-in: POST /api/auth/mfa/verify with the code."""
    mfaRequired: bool = True
    mfaToken: str = Field(description="Pending sign-in (5 minutes); not an access token")
    mfaExpiresInSeconds: int


class LoginEnvelope(BaseModel):
    success: bool
    message: str
    data: AuthData | MfaChallenge | None
    errors: list[str] | None


class MfaSetupRequest(BaseModel):
    password: str


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class MfaDisableRequest(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=6)


class MfaVerifyRequest(BaseModel):
    mfaToken: str
    code: str = Field(min_length=6, max_length=6)


class MfaSetup(BaseModel):
    secret: str = Field(description="Base32, for typing into the authenticator app")
    otpauthUri: str = Field(description="otpauth:// URI, shown as a QR code")
    issuer: str


class MfaStatus(BaseModel):
    enabled: bool
    available: bool = Field(description="This account can use it and the server is configured")


class MfaSetupEnvelope(BaseModel):
    success: bool
    message: str
    data: MfaSetup | None
    errors: list[str] | None


class MfaStatusEnvelope(BaseModel):
    success: bool
    message: str
    data: MfaStatus | None
    errors: list[str] | None


class EmptyEnvelope(BaseModel):
    success: bool
    message: str
    data: None = None
    errors: list[str] | None = None
