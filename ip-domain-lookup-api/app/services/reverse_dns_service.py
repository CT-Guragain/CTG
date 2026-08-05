"""
Reverse DNS (PTR) lookups using the standard-library socket module.

socket.gethostbyaddr() does the PTR lookup for us and also returns
any known aliases for the hostname it finds.
"""

import ipaddress
import socket


def validate_ip(ip: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Raise ValueError via ipaddress if `ip` isn't a valid IPv4/IPv6 address."""
    return ipaddress.ip_address(ip)


def reverse_lookup(ip: str) -> dict:
    """
    Resolve `ip` back to a hostname.

    Returns a dict with resolved=False (rather than raising) when the
    IP has no PTR record — that's a normal, expected outcome for a
    lot of IPs, not an error condition.
    """
    try:
        hostname, aliases, _ = socket.gethostbyaddr(ip)
        return {
            "ip": ip,
            "hostname": hostname,
            "aliases": aliases,
            "resolved": True,
        }
    except (socket.herror, socket.gaierror):
        return {
            "ip": ip,
            "hostname": None,
            "aliases": [],
            "resolved": False,
        }
