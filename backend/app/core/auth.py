from __future__ import annotations

from functools import lru_cache
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network
from typing import Any

import jwt
from fastapi import Depends, Header, Request

from app.core.config import Settings, get_settings


class AuthError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


Network = IPv4Network | IPv6Network
Address = IPv4Address | IPv6Address


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache(maxsize=64)
def _parse_networks(raw: str) -> tuple[Network, ...]:
    networks: list[Network] = []
    for item in _split_csv(raw):
        try:
            networks.append(ip_network(item, strict=False))
        except ValueError:
            continue
    return tuple(networks)


def _parse_ip(value: str) -> Address | None:
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.startswith("[") and "]" in candidate:
        candidate = candidate[1 : candidate.index("]")]
    try:
        return ip_address(candidate)
    except ValueError:
        if candidate.count(":") == 1 and "." in candidate:
            host, _port = candidate.split(":", 1)
            try:
                return ip_address(host)
            except ValueError:
                return None
        return None


def _ip_in_networks(address: Address, networks: tuple[Network, ...]) -> bool:
    return any(address in network for network in networks)


def _allowlist_enabled(settings: Settings) -> bool:
    if not settings.ip_allowlist_enabled:
        return False
    if settings.env.lower() == "production" and not settings.ip_allowlist_configured:
        return False
    return True


def _get_client_ip(request: Request, settings: Settings) -> Address | None:
    if request.client is None or not request.client.host:
        return None
    client_ip = _parse_ip(request.client.host)
    if client_ip is None:
        return None
    trusted_proxies = _parse_networks(settings.trusted_proxy_cidrs)
    if trusted_proxies and _ip_in_networks(client_ip, trusted_proxies):
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            first_hop = forwarded_for.split(",", 1)[0].strip()
            forwarded_ip = _parse_ip(first_hop)
            if forwarded_ip:
                return forwarded_ip
    return client_ip


def _is_request_allowlisted(request: Request, settings: Settings) -> bool:
    client_ip = _get_client_ip(request, settings)
    if client_ip is None:
        return False
    allowlist_networks = _parse_networks(settings.ip_allowlist)
    if not allowlist_networks:
        return False
    return _ip_in_networks(client_ip, allowlist_networks)


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def _decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    secret = settings.supabase_jwt_secret
    if not secret:
        raise AuthError("鉴权失败，请稍后重试。")
    options = {"verify_aud": bool(settings.supabase_jwt_audience)}
    decode_kwargs: dict[str, Any] = {}
    if settings.supabase_jwt_audience:
        decode_kwargs["audience"] = settings.supabase_jwt_audience
    if settings.supabase_jwt_issuer:
        decode_kwargs["issuer"] = settings.supabase_jwt_issuer
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options=options,
            **decode_kwargs,
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("登录已过期，请重新登录。") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("鉴权失败，请登录。") from exc


async def require_user(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise AuthError("未登录或鉴权失败。")
    claims = _decode_supabase_jwt(token, settings)
    user_id = claims.get("sub") or claims.get("user_id")
    if not user_id:
        raise AuthError("鉴权失败，请登录。")
    request.state.user_id = user_id
    return user_id


async def require_user_or_allowlisted(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> str | None:
    token = _extract_bearer_token(authorization)
    auth_error: AuthError | None = None
    if token:
        try:
            claims = _decode_supabase_jwt(token, settings)
        except AuthError as exc:
            auth_error = exc
        else:
            user_id = claims.get("sub") or claims.get("user_id")
            if not user_id:
                raise AuthError("鉴权失败，请登录。")
            request.state.user_id = user_id
            return user_id

    if _allowlist_enabled(settings) and _is_request_allowlisted(request, settings):
        return None

    if auth_error:
        raise auth_error
    raise AuthError("未登录或鉴权失败。")
