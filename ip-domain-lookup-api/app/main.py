"""
IP/Domain Lookup API
---------------------
A small FastAPI service that wraps dnspython, socket, and a free
geolocation API to expose DNS record lookups, reverse DNS, and
IP geolocation over a clean REST interface.

Run locally:
    uvicorn app.main:app --reload

Docs (auto-generated):
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import dns_lookup, reverse_dns, geolocation

app = FastAPI(
    title="IP/Domain Lookup API",
    description=(
        "Look up DNS records, reverse DNS (PTR) entries, and IP "
        "geolocation for any domain or IP address."
    ),
    version="1.0.0",
)

# Wide-open CORS is fine for a portfolio/demo API; tighten this
# (allow_origins=["https://yourdomain.com"]) before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(dns_lookup.router)
app.include_router(reverse_dns.router)
app.include_router(geolocation.router)


@app.get("/", tags=["health"])
def root():
    """Basic health check / index."""
    return {
        "service": "IP/Domain Lookup API",
        "status": "ok",
        "endpoints": [
            "/dns/{domain}",
            "/reverse-dns/{ip}",
            "/geolocation/{ip}",
        ],
        "docs": "/docs",
    }
