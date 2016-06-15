
__version__ = '0.10.0'

EVENT_CATEGORIES_TO_DEFAULTS = {
        "consumed": 100,
        "produced": 100,
        "experienced": 100,
        "interacted": 80,
        "formulated": 80,
        "completed": 50,
        "detected": 10,
        "measured": 5
        }

EVENT_CATEGORIES = list(EVENT_CATEGORIES_TO_DEFAULTS.keys())
