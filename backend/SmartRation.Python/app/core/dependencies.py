"""Authentication / authorization dependencies (C# [Authorize] equivalents).

    user: CurrentUser = Depends(get_current_user)                # any signed-in user
    user: CurrentUser = Depends(require_roles(UserRole.ShopOwner, ...))

401/403 bodies match the C# JwtBearer events exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request

from app.core.errors import Forbidden, Unauthorized
from app.core.security import ROLE_CLAIM, InvalidToken, decode_access_token
from app.db.enums import UserRole


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


def require_roles(*roles: UserRole):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise Forbidden("You do not have permission to perform this action.")
        return user

    return dependency
