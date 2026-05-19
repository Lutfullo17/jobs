from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(None, max_length=255, description="Bo'sh bo'lsa name'dan generatsiya")
    logo_url: str | None = None
    about: str = ""
    website: str | None = None
    industry: str = ""
    company_size: str = ""
    country: str = ""
    city: str = ""
    address: str = ""


class CompanyUpdateBody(BaseModel):
    name: str | None = Field(None, max_length=255)
    logo_url: str | None = None
    about: str | None = None
    website: str | None = None
    industry: str | None = None
    company_size: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None


class CompanyOut(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None
    about: str
    website: str | None
    industry: str
    company_size: str
    country: str
    city: str
    address: str
    verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyPublicOut(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None
    about: str
    website: str | None
    industry: str
    company_size: str
    country: str
    city: str
    verified: bool

    model_config = ConfigDict(from_attributes=True)
