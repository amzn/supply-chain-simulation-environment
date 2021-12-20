from dataclasses import dataclass

PERIOD_LENGTH_HOURS = 0.5

DEFAULT_CONSUMER = 'Consumers'
DEFAULT_BALANCE_SOURCE = 'Balance Source'
DEFAULT_BALANCE_SINK = 'Balance Sink'

ELECTRICITY_ASIN: str = 'electricity'

@dataclass
class _EnergyGenerationAsins:
    solar: str = 'Solar'
    wind_onshore: str = 'Wind Onshore'
    wind_offshore: str = 'Wind Offshore'
    wind_combined: str = 'Wind Combined'
    hydro_storage: str = 'Hydro Pumped Storage'
    hydro_river: str = 'Hydro Run-of-river and poundage'
    biomass: str = 'Biomass'
    fossil_gas: str = 'Fossil Gas'
    fossil_oil: str = 'Fossil Oil'
    fossil_coal: str = 'Fossil Hard coal'
    nuclear: str = 'Nuclear'
    interconnector: str = 'Interconnector'
    other: str = 'Other'
ENERGY_GENERATION_ASINS = _EnergyGenerationAsins()

@dataclass
class _EnergyGenerationLabels:
    solar: str = 'Solar'
    wind_onshore: str = 'Wind Onshore'
    wind_offshore: str = 'Wind Offshore'
    wind_combined: str = 'Wind'
    hydro_storage: str = 'Hydro Storage'
    hydro_river: str = 'Hydro River'
    biomass: str = 'Biomass'
    fossil_gas: str = 'Gas'
    fossil_oil: str = 'Oil'
    fossil_coal: str = 'Coal'
    nuclear: str = 'Nuclear'
    interconnector: str = 'Interconnector'
    other: str = 'Other'
ENERGY_GENERATION_LABELS = _EnergyGenerationLabels()
