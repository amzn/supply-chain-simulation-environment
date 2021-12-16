from dataclasses import dataclass

PERIOD_LENGTH_HOURS = 0.5

DEFAULT_CONSUMER = 'Consumers'
DEFAULT_BALANCE_SOURCE = 'Balance Source'
DEFAULT_BALANCE_SINK = 'Balance Sink'

ELECTRICITY_ASIN: str = 'electricity'

@dataclass
class _EnergyGenerationAsins:
    solar: str = 'Solar'
    fossil_gas: str = 'Fossil Gas'
    wind_onshore: str = 'Wind Onshore'
ENERGY_GENERATION_ASINS = _EnergyGenerationAsins()
