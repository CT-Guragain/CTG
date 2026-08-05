"""
IP geolocation via ip-api.com's free tier.

Free tier notes (as of writing):
- No API key required.
- HTTP only (not HTTPS) on the free plan.
- Rate limit: 45 requests/minute per source IP.
- Swap GEO_API_URL for ipinfo.io or another provider if you need
  HTTPS or a higher rate limit — just adjust `_parse_response`
  to match that provider's field names.
"""

import ipaddress

import httpx

GEO_API_URL = "http://ip-api.com/json/{ip}"
FIELDS = "status,message,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,query"


class PrivateIPError(ValueError):
    """Raised when the caller asks us to geolocate a private/reserved IP."""


def _reject_non_public(ip: str) -> None:
    addr = ipaddress.ip_address(ip)
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
        raise PrivateIPError(
            f"{ip} is a private/reserved address and has no public geolocation."
        )


def _parse_response(data: dict, ip: str) -> dict:
    return {
        "ip": ip,
        "country": data.get("country"),
        "country_code": data.get("countryCode"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
        "timezone": data.get("timezone"),
        "isp": data.get("isp"),
        "org": data.get("org"),
        "as_number": data.get("as"),
    }


async def geolocate(ip: str, timeout: float = 5.0) -> dict:
    """
    Look up geolocation for a public IP address.

    Raises:
        PrivateIPError: if `ip` is private/loopback/reserved.
        httpx.HTTPError: on network failure.
        ValueError: if the provider reports a lookup failure
                    (e.g. invalid IP, rate limited).
    """
    _reject_non_public(ip)

    url = GEO_API_URL.format(ip=ip) + f"?fields={FIELDS}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "success":
        raise ValueError(data.get("message", "geolocation lookup failed"))

    return _parse_response(data, ip)
