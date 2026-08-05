"""
DNS record lookups via dnspython.

dnspython talks to a resolver directly (not the OS stub resolver),
so it works the same way on every platform and lets us set our own
timeout/nameservers if needed.
"""

import dns.resolver
import dns.exception

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]


def _query(domain: str, record_type: str, timeout: float = 5.0) -> list[str]:
    """Query one record type; return [] if the record doesn't exist."""
    try:
        answers = dns.resolver.resolve(domain, record_type, lifetime=timeout)
        return [rdata.to_text() for rdata in answers]
    except (
        dns.resolver.NoAnswer,
        dns.resolver.NXDOMAIN,
        dns.resolver.NoNameservers,
        dns.exception.Timeout,
    ):
        return []


def lookup_all_records(domain: str, timeout: float = 5.0) -> dict:
    """
    Query every record type in RECORD_TYPES for `domain`.

    Returns a dict keyed by record type -> list of record values.
    A domain that genuinely doesn't exist (NXDOMAIN on every type)
    will just come back with all-empty lists; the router decides
    whether that should be surfaced as a 404.
    """
    results = {"domain": domain}
    for rtype in RECORD_TYPES:
        results[rtype] = _query(domain, rtype, timeout=timeout)
    return results


def domain_exists(records: dict) -> bool:
    """True if at least one record type returned data."""
    return any(records.get(rtype) for rtype in RECORD_TYPES)
