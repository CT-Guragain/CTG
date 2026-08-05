from typing import Optional

from pydantic import BaseModel, Field


class DNSRecordSet(BaseModel):
    domain: str
    A: list[str] = Field(default_factory=list)
    AAAA: list[str] = Field(default_factory=list)
    MX: list[str] = Field(default_factory=list)
    NS: list[str] = Field(default_factory=list)
    TXT: list[str] = Field(default_factory=list)
    CNAME: list[str] = Field(default_factory=list)
    SOA: list[str] = Field(default_factory=list)


class ReverseDNSResult(BaseModel):
    ip: str
    hostname: Optional[str] = None
    aliases: list[str] = Field(default_factory=list)
    resolved: bool


class GeolocationResult(BaseModel):
    ip: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    org: Optional[str] = None
    as_number: Optional[str] = None
