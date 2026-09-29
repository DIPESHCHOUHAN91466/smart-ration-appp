"""Authentication / authorization dependencies (C# [Authorize] equivalents).

    user: CurrentUser = Depends(get_current_user)                # any signed-in user
    user: CurrentUser = Depends(require_roles(UserRole.ShopOwner, ...))

401/403 bodies match the C# JwtBearer events exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request

from app.core.errors import Forbidden, Unauthorized
from app.database.enums import UserRole
from app.security.tokens import ROLE_CLAIM, InvalidToken, decode_access_token


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    role: UserRole
    ration_shop_id: int | None
    email: str


def get_current_user(request: Request) -> CurrentUser:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise Unauthorized("Authentication required.")
    try:
        claims = decode_access_token(token.strip(), request.app.state.settings)
        role = UserRole[claims[ROLE_CLAIM]]
        shop = claims.get("rationShopId")
        user = CurrentUser(int(claims["sub"]), role, int(shop) if shop else None, claims.get("email", ""))
    except (InvalidToken, KeyError, ValueError):
        raise Unauthorized("Authentication required.") from None
    request.state.current_user = user  # lets the audit log record the role
    return user


def optional_current_user(request: Request) -> CurrentUser | None:
    """The signed-in user if the request carries a valid access token, else None (never raises).
    For public endpoints that may add something for signed-in users — never for access control."""
    try:
        return get_current_user(request)
    except Unauthorized:
        return None


def require_roles(*roles: UserRole):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise Forbidden("You do not have permission to perform this action.")
        return user

    return dependency


# Role groups used by the business routes.
STAFF = (UserRole.ShopOwner, UserRole.GovernmentOfficial, UserRole.Admin)
OFFICIALS = (UserRole.GovernmentOfficial, UserRole.Admin)


@dataclass(frozen=True)
class Actor:
    """Who is asking, and from where — what the services need for access rules and audit rows."""

    user_id: int
    role: UserRole
    ration_shop_id: int | None
    ip_address: str | None = None
    user_agent: str | None = None

    @property
    def is_official(self) -> bool:
        return self.role in OFFICIALS


def _actor(request: Request, user: CurrentUser) -> Actor:
    return Actor(user.user_id, user.role, user.ration_shop_id,
                 request.client.host if request.client else None, request.headers.get("user-agent"))


def actor(*roles: UserRole):
    """Dependency: the signed-in caller as an Actor, optionally limited to `roles` (403 otherwise)."""
    def dependency(request: Request, user: CurrentUser = Depends(get_current_user)) -> Actor:
        if roles and user.role not in roles:
            raise Forbidden("You do not have permission to perform this action.")
        return _actor(request, user)

    return dependency
