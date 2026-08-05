from fastapi import APIRouter, HTTPException

from app.models import ReverseDNSResult
from app.services import reverse_dns_service

router = APIRouter(tags=["reverse-dns"])


@router.get("/reverse-dns/{ip}", response_model=ReverseDNSResult)
def get_reverse_dns(ip: str):
    """
    Resolve `ip` back to a hostname (PTR lookup).

    Example: GET /reverse-dns/8.8.8.8
    resolved=False just means no PTR record exists for that IP —
    that's a normal result, not an error.
    """
    try:
        reverse_dns_service.validate_ip(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"'{ip}' is not a valid IP address.")

    return reverse_dns_service.reverse_lookup(ip)
