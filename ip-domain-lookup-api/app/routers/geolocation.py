import ipaddress

import httpx
from fastapi import APIRouter, HTTPException

from app.models import GeolocationResult
from app.services import geo_service

router = APIRouter(tags=["geolocation"])


@router.get("/geolocation/{ip}", response_model=GeolocationResult)
async def get_geolocation(ip: str):
    """
    Return country/region/city/coords/ISP for a public IP address.

    Example: GET /geolocation/8.8.8.8
    Private, loopback, and reserved addresses (RFC1918, 127.0.0.1,
    etc.) are rejected with a 400 — they have no public geolocation.
    """
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"'{ip}' is not a valid IP address.")

    try:
        return await geo_service.geolocate(ip)
    except geo_service.PrivateIPError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502, detail="Geolocation provider is unreachable right now."
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
