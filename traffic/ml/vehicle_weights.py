"""
Passenger car unit (PCU) weights and display categories for the 14 BMD-45 classes.

PCU weights follow the urban-road factors of IRC:106-1990 (lower-share column):
two-wheeler 0.5, car 1.0, auto-rickshaw 1.2, light commercial vehicle 1.4,
truck or bus 2.2, bicycle 0.4. Classes missing from that table are assumptions:
Mini-bus (like a bus), Tempo-traveller (like an LCV), SUV / MUV / Van / Other (like a car).
These are approximate: real PCU values vary with road and traffic mix.
"""

PCU_WEIGHTS = {
    "Hatchback": 1.0,
    "Sedan": 1.0,
    "SUV": 1.0,
    "MUV": 1.0,
    "Bus": 2.2,
    "Truck": 2.2,
    "Three-wheeler": 1.2,
    "Two-wheeler": 0.5,
    "LCV": 1.4,
    "Mini-bus": 2.2,
    "Tempo-traveller": 1.4,
    "Bicycle": 0.4,
    "Van": 1.0,
    "Other": 1.0,
}
DEFAULT_PCU = 1.0

# The 14 detected classes grouped into the 9 display categories of the proposal.
DISPLAY_CATEGORY = {
    "Hatchback": "Car",
    "Sedan": "Car",
    "SUV": "Car",
    "MUV": "Car",
    "Two-wheeler": "Bike",
    "Three-wheeler": "Auto",
    "Bus": "Bus",
    "Mini-bus": "Bus",
    "Truck": "Truck",
    "LCV": "Truck",
    "Tempo-traveller": "Tempo Traveller",
    "Bicycle": "Bicycle",
    "Van": "Van",
    "Other": "Other",
}
CATEGORY_ORDER = [
    "Car", "Bike", "Auto", "Bus", "Truck", "Tempo Traveller", "Bicycle", "Van", "Other",
]


def weighted_load(class_counts):
    """Total load in PCU for a {class name: count} dict, rounded to 1 decimal."""
    total = sum(count * PCU_WEIGHTS.get(name, DEFAULT_PCU) for name, count in class_counts.items())
    return round(total, 1)


def category_counts(class_counts):
    """Group a {class name: count} dict into the 9 display categories (zero counts left out)."""
    grouped = {}
    for name, count in class_counts.items():
        category = DISPLAY_CATEGORY.get(name, "Other")
        grouped[category] = grouped.get(category, 0) + count
    return {c: grouped[c] for c in CATEGORY_ORDER if grouped.get(c)}