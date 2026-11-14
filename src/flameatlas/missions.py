"""Crew-environment presets. Numbers come from the challenge text (Flame in Freefall, NASA Space Apps 2026)."""

PSI_TO_KPA = 6.895

MISSIONS = {
    "Earth / ISS cabin": {
        "pressure_kpa": round(14.7 * PSI_TO_KPA, 1),
        "o2_percent": 21.0,
        "gravity_g": 0.0,
        "note": "Sea-level air, 14.7 psi, 21% O2.",
    },
    "Moon base / pressurized rover": {
        "pressure_kpa": round(10.2 * PSI_TO_KPA, 1),
        "o2_percent": 30.0,
        "gravity_g": 0.16,
        "note": "Expected >=30% O2 at <=10.2 psi. No partial-g data in PSI: bound with 0 g and 1 g results.",
    },
    "Mars habitat (assumed same as Moon)": {
        "pressure_kpa": round(10.2 * PSI_TO_KPA, 1),
        "o2_percent": 30.0,
        "gravity_g": 0.38,
        "note": "Assumption for the demo: same exploration atmosphere as the Moon base.",
    },
    "Spacesuit": {
        "pressure_kpa": round(4.3 * PSI_TO_KPA, 1),
        "o2_percent": 100.0,
        "gravity_g": 0.16,
        "note": "100% O2 at 4.3 psi.",
    },
}
