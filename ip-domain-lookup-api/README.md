# IP/Domain Lookup API

A small FastAPI service that wraps `dnspython`, `socket`, and a free
IP geolocation API to expose three lookups over REST:

- **DNS records** for a domain (A, AAAA, MX, NS, TXT, CNAME, SOA)
- **Reverse DNS** (PTR) for an IP address
- **IP geolocation** (country, city, lat/lon, ISP, ASN)

Built as a portfolio project to demonstrate calling external
services (DNS resolvers, a third-party geolocation API) from your
own API layer.

## Project structure

```
ip-domain-lookup-api/
├── app/
│   ├── main.py                  # FastAPI app + router registration
│   ├── models.py                # Pydantic response models
│   ├── routers/
│   │   ├── dns_lookup.py        # GET /dns/{domain}
│   │   ├── reverse_dns.py       # GET /reverse-dns/{ip}
│   │   └── geolocation.py       # GET /geolocation/{ip}
│   └── services/
│       ├── dns_service.py       # dnspython record queries
│       ├── reverse_dns_service.py  # socket.gethostbyaddr PTR lookups
│       └── geo_service.py       # httpx calls to ip-api.com
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

```bash
git clone https://github.com/<your-username>/ip-domain-lookup-api.git
cd ip-domain-lookup-api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run it

```bash
uvicorn app.main:app --reload
```

Interactive Swagger docs: http://127.0.0.1:8000/docs

## Endpoints

### `GET /dns/{domain}`
```bash
curl http://127.0.0.1:8000/dns/example.com
```
Returns every A/AAAA/MX/NS/TXT/CNAME/SOA record found. A record type
with no entries just comes back as an empty list — that's normal,
not an error. A domain with nothing at all returns `404`.

### `GET /reverse-dns/{ip}`
```bash
curl http://127.0.0.1:8000/reverse-dns/8.8.8.8
```
Returns the PTR hostname and any aliases. `resolved: false` means
the IP simply has no PTR record — most residential/dynamic IPs
don't.

### `GET /geolocation/{ip}`
```bash
curl http://127.0.0.1:8000/geolocation/8.8.8.8
```
Uses [ip-api.com](https://ip-api.com)'s free tier (no key needed,
45 requests/min limit). Private/loopback/reserved addresses
(RFC1918, 127.0.0.1, etc.) are rejected with `400` since they have
no public geolocation. Swap the provider in `geo_service.py` if you
need HTTPS or a higher rate limit (e.g. ipinfo.io with a token).

## Notes on design choices

- **Services vs. routers**: lookup logic lives in `app/services/`,
  independent of FastAPI, so it's unit-testable without spinning up
  the app and easy to reuse from a CLI or script later.
- **Errors that aren't errors**: a domain with no MX record, or an
  IP with no PTR entry, is a normal outcome — those return `200`
  with empty/`resolved: false` fields rather than a `4xx`. Only
  genuinely bad input (invalid IP, fully nonexistent domain) returns
  `400`/`404`.
- **SSRF-style guardrail**: the geolocation endpoint rejects
  private/reserved IPs before calling out to the provider, since
  there's nothing meaningful to look up and it avoids leaking
  internal-network probing through a public API.

## Deploying

Any ASGI host works — Render, Railway, Fly.io, a small VPS behind
nginx, etc. Production start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Tighten the CORS policy in `app/main.py` (`allow_origins`) before
exposing this publicly.

## Pushing to GitHub

If you're starting this as a brand-new repo:

```bash
cd ip-domain-lookup-api
git init
git add .
git commit -m "Initial commit: IP/Domain Lookup API"
git branch -M main
git remote add origin https://github.com/<your-username>/ip-domain-lookup-api.git
git push -u origin main
```

If the repo already exists on GitHub (created via the "New
repository" button, so it's non-empty or has a README/license
already), pull first to avoid a diverged-history rejection:

```bash
git init
git add .
git commit -m "Initial commit: IP/Domain Lookup API"
git branch -M main
git remote add origin https://github.com/<your-username>/ip-domain-lookup-api.git
git pull origin main --allow-unrelated-histories
git push -u origin main
```

For any later change:

```bash
git add .
git commit -m "Describe what changed"
git push
```
