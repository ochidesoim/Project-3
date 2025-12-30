# The central lookup table for Engineering DNA
# This file will import specific DNA implementations and map them to keywords

# Lazy import to avoid circular dependencies if any
from src.library.rocket_dna import RocketEngineDNA

DNA_CATALOG = {
    # Keys should be lowercase
    "rocket": RocketEngineDNA,
    "engine": RocketEngineDNA,
    "thruster": RocketEngineDNA,
    "nozzle": RocketEngineDNA,
    "booster": RocketEngineDNA,
    "propulsion": RocketEngineDNA,
}

def get_dna_class(keyword: str):
    """
    Returns the DNA class associated with the keyword, or None if not found.
    """
    return DNA_CATALOG.get(keyword.lower())

def register_dns(keyword: str, dna_class):
    """
    Dynamically register a DNA class (useful for plugins or runtime additions).
    """
    DNA_CATALOG[keyword.lower()] = dna_class
