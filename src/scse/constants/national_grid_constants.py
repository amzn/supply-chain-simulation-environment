from dataclasses import dataclass

PERIOD_LENGTH_HOURS = 0.5

ELECTRICITY_ASIN: str = 'electricity'

@dataclass
class _EnergyGenerationAsins:
    solar: str = 'Solar'
    fossil_gas: str = 'Fossil Gas'
    wind_onshore: str = 'Wind Onshore'
ENERGY_GENERATION_ASINS = _EnergyGenerationAsins()
