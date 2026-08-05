from fastapi import APIRouter, HTTPException

from app.models import DNSRecordSet
from app.services import dns_service

router = APIRouter(tags=["dns"])


@router.get("/dns/{domain}", response_model=DNSRecordSet)
def get_dns_records(domain: str):
    """
    Return A, AAAA, MX, NS, TXT, CNAME, and SOA records for `domain`.

    Example: GET /dns/example.com
    """
    records = dns_service.lookup_all_records(domain)

    if not dns_service.domain_exists(records):
        raise HTTPException(
            status_code=404,
            detail=f"No DNS records found for '{domain}'. It may not exist "
            "or all queried record types are genuinely empty.",
        )

    return records
