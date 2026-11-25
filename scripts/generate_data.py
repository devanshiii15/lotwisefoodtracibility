"""
Generate realistic, referentially-consistent sample data for LotWise.

Relationships:
    Supplier  ->  Lot  ->  Batch  ->  Shipment
                   |
                   +----> Lab Report

Run:  python scripts/generate_data.py
Output CSVs are written to ../data/
"""

import csv
import os
import random
from datetime import date, timedelta

# Deterministic output so the demo is reproducible.
random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference values
# ---------------------------------------------------------------------------
SUPPLIER_NAMES = [
    "GreenFields Farms", "Sunrise Organics", "Blue River Dairy", "Golden Grain Co",
    "Harvest Valley", "Pure Leaf Produce", "Nova Foods", "Coastal Catch Ltd",
    "Meadow Brook Farms", "Alpine Naturals", "Prairie Gold Mills", "Fresh Roots",
    "Silver Lake Poultry", "Orchard Hill", "Terra Verde", "Sunny Acres",
    "Crystal Springs", "Evergreen Foods", "Red Barn Produce", "Maple Ridge",
]

COUNTRIES = ["USA", "Canada", "Mexico", "Spain", "India", "Brazil", "Netherlands"]
CITIES = ["Fresno", "Portland", "Austin", "Denver", "Chicago", "Toronto",
          "Guadalajara", "Valencia", "Pune", "Sao Paulo", "Rotterdam"]

INGREDIENTS = [
    "Romaine Lettuce", "Wheat Flour", "Whole Milk", "Chicken Breast", "Tomatoes",
    "Spinach", "Cane Sugar", "Almonds", "Cheddar Cheese", "Salmon Fillet",
    "Basmati Rice", "Olive Oil", "Cocoa Powder", "Black Pepper", "Strawberries",
]

PRODUCTS = [
    "Caesar Salad Kit", "Sandwich Bread", "Vanilla Yogurt", "Grilled Chicken Wrap",
    "Marinara Sauce", "Spinach Smoothie", "Chocolate Bar", "Almond Granola",
    "Cheese Crackers", "Salmon Ready-Meal", "Rice Bowl", "Trail Mix",
]

FACILITIES = ["Plant A - Fresno", "Plant B - Denver", "Plant C - Austin",
              "Plant D - Chicago", "Plant E - Portland"]

DISTRIBUTORS = ["FreshLine Distribution", "QuickMart Wholesale", "MetroFoods",
                "ValueGrocer Supply", "CityMart Logistics"]

DESTINATIONS = ["Los Angeles, CA", "Seattle, WA", "Houston, TX", "Miami, FL",
                "Boston, MA", "Phoenix, AZ", "Atlanta, GA", "Denver, CO"]

TEST_TYPES = ["Salmonella", "E. coli", "Listeria", "Pesticide Residue",
              "Heavy Metals", "Aflatoxin"]


def d(start, end):
    """Random date between two dates."""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ---------------------------------------------------------------------------
# Suppliers  (S001 ... S020)
# ---------------------------------------------------------------------------
suppliers = []
for i, name in enumerate(SUPPLIER_NAMES, start=1):
    sid = f"S{i:03d}"
    suppliers.append({
        "supplier_id": sid,
        "name": name,
        "city": random.choice(CITIES),
        "country": random.choice(COUNTRIES),
        "ingredient_supplied": random.choice(INGREDIENTS),
        "contact_email": f"contact@{name.lower().replace(' ', '')}.com",
        "rating": round(random.uniform(3.2, 5.0), 1),
    })

# ---------------------------------------------------------------------------
# Lots  (L200 ... L259)   ~60 lots
# ---------------------------------------------------------------------------
lots = []
for i in range(60):
    lid = f"L{200 + i}"
    supplier = random.choice(suppliers)
    lots.append({
        "lot_id": lid,
        "supplier_id": supplier["supplier_id"],
        "ingredient": supplier["ingredient_supplied"],
        "quantity_kg": random.randint(200, 5000),
        "received_date": d(date(2025, 1, 1), date(2025, 6, 30)).isoformat(),
        "status": "Received",
    })

# ---------------------------------------------------------------------------
# Batches  (B100 ... )   ~80 batches, each made from one lot
# ---------------------------------------------------------------------------
batches = []
for i in range(80):
    bid = f"B{100 + i}"
    lot = random.choice(lots)
    prod_date = d(date(2025, 2, 1), date(2025, 7, 15))
    batches.append({
        "batch_id": bid,
        "lot_id": lot["lot_id"],
        "product_name": random.choice(PRODUCTS),
        "production_date": prod_date.isoformat(),
        "quantity_units": random.randint(500, 8000),
        "facility": random.choice(FACILITIES),
    })

# ---------------------------------------------------------------------------
# Shipments  (SH900 ... )  ~90 shipments, each carries one batch
# ---------------------------------------------------------------------------
shipments = []
for i in range(90):
    shid = f"SH{900 + i}"
    batch = random.choice(batches)
    ship_date = d(date(2025, 3, 1), date(2025, 7, 31))
    shipments.append({
        "shipment_id": shid,
        "batch_id": batch["batch_id"],
        "distributor": random.choice(DISTRIBUTORS),
        "destination": random.choice(DESTINATIONS),
        "ship_date": ship_date.isoformat(),
        "status": random.choice(["Delivered", "In Transit", "Delivered", "Delivered"]),
    })

# ---------------------------------------------------------------------------
# Lab reports  (R500 ... )  ~60 reports, a few positive (contaminated)
# ---------------------------------------------------------------------------
lab_reports = []
tested_lots = random.sample(lots, 55)
for i, lot in enumerate(tested_lots):
    rid = f"R{500 + i}"
    # ~12% positive results
    positive = random.random() < 0.12
    lab_reports.append({
        "report_id": rid,
        "lot_id": lot["lot_id"],
        "test_type": random.choice(TEST_TYPES),
        "test_date": d(date(2025, 2, 1), date(2025, 7, 20)).isoformat(),
        "result": "Positive" if positive else "Negative",
        "status": "Contaminated" if positive else "Clear",
    })

# ---------------------------------------------------------------------------
# SEED A KNOWN CONTAMINATION SCENARIO around Lot L204  (for the demo)
# ---------------------------------------------------------------------------
demo_lot_id = "L204"
demo_lot = next(l for l in lots if l["lot_id"] == demo_lot_id)
demo_lot["ingredient"] = "Romaine Lettuce"
# Point it at a well-known supplier
demo_supplier = suppliers[0]  # GreenFields Farms
demo_supplier["ingredient_supplied"] = "Romaine Lettuce"
demo_lot["supplier_id"] = demo_supplier["supplier_id"]

# Ensure L204 has at least 3 batches
demo_batches = []
for j in range(3):
    bid = f"B{180 + j}"
    demo_batches.append({
        "batch_id": bid,
        "lot_id": demo_lot_id,
        "product_name": "Caesar Salad Kit",
        "production_date": d(date(2025, 5, 1), date(2025, 5, 20)).isoformat(),
        "quantity_units": random.randint(2000, 6000),
        "facility": "Plant A - Fresno",
    })
batches.extend(demo_batches)

# Ensure each demo batch has shipments
for k, b in enumerate(demo_batches):
    for m in range(2):
        shid = f"SH{990 + k * 2 + m}"
        shipments.append({
            "shipment_id": shid,
            "batch_id": b["batch_id"],
            "distributor": random.choice(DISTRIBUTORS),
            "destination": random.choice(DESTINATIONS),
            "ship_date": d(date(2025, 5, 20), date(2025, 6, 5)).isoformat(),
            "status": "Delivered",
        })

# Ensure L204 has a POSITIVE lab report
lab_reports.append({
    "report_id": "R599",
    "lot_id": demo_lot_id,
    "test_type": "E. coli",
    "test_date": "2025-06-01",
    "result": "Positive",
    "status": "Contaminated",
})


# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------
def write_csv(filename, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>3} rows -> {filename}")


print("Generating LotWise sample data...")
write_csv("suppliers.csv", suppliers)
write_csv("lots.csv", lots)
write_csv("batches.csv", batches)
write_csv("shipments.csv", shipments)
write_csv("lab_reports.csv", lab_reports)
print("Done. Demo contaminated lot = L204 (E. coli, GreenFields Farms).")
