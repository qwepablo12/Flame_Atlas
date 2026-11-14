"""Data schema for FlameAtlas."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Phase(str, Enum):
    solid = "solid"
    liquid = "liquid"
    gas = "gas"
    aerosol = "aerosol"
    unknown = "unknown"


class Category(str, Enum):
    prevention = "prevention"
    detection = "detection"
    suppression = "suppression"
    fundamental = "fundamental"
    unknown = "unknown"


class Outcome(str, Enum):
    ignited_spread = "ignited_spread"
    ignited_no_spread = "ignited_no_spread"
    no_ignition = "no_ignition"
    extinguished = "extinguished"
    detected = "detected"
    other = "other"
    unknown = "unknown"


class TestRecord(BaseModel):
    """A single test condition. Every numeric field is optional: never guess."""

    investigation: str = Field(description="Investigation acronym, e.g. BASS-II, FLEX-2, Saffire-II, ACME/CFI-G")
    hardware: Optional[str] = Field(None, description="Facility/apparatus, e.g. MSG, CIR/MDCA, CIR/ACME, Cygnus")
    platform: Optional[str] = Field(None, description="ISS, Cygnus, drop tower, parabolic flight, ground (1g)")
    year: Optional[int] = None
    category: Category = Category.unknown
    objective: Optional[str] = Field(None, description="What the test was trying to learn, one sentence")

    fuel: Optional[str] = Field(None, description="Fuel or material, e.g. PMMA, cotton-fiberglass fabric, n-heptane, ethylene")
    phase: Phase = Phase.unknown
    sample_geometry: Optional[str] = Field(None, description="Shape/size, e.g. '1 cm sphere', 'thin sheet 10x40 cm', '3 mm droplet'")

    pressure_kpa: Optional[float] = Field(None, description="Ambient pressure in kPa (1 psi = 6.895 kPa, 1 atm = 101.3 kPa)")
    o2_percent: Optional[float] = Field(None, description="Ambient oxygen mole fraction in percent (0-100)")
    diluent: Optional[str] = Field(None, description="N2, CO2, He, etc.")
    flow_speed_cm_s: Optional[float] = Field(None, description="Imposed airflow speed in cm/s (0 = quiescent)")
    gravity_g: Optional[float] = Field(None, description="Gravity level in g; microgravity ~ 0, Earth = 1")

    outcome: Outcome = Outcome.unknown
    spread_rate_mm_s: Optional[float] = Field(None, description="Flame spread rate in mm/s if reported")
    measurements: Optional[str] = Field(None, description="Sensors/diagnostics, e.g. 'color video, radiometer, thermocouples'")
    key_finding: Optional[str] = Field(None, description="Main result for this test, one or two sentences")

    quote: Optional[str] = Field(None, description="Verbatim sentence from the source that supports the numbers above")
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    page: Optional[int] = None
    confidence: float = Field(0.5, ge=0, le=1, description="Extractor's confidence in this row")


class ExtractionResult(BaseModel):
    tests: list[TestRecord]


CSV_COLUMNS = list(TestRecord.model_fields.keys())
