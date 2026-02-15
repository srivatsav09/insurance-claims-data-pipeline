"""
Synthetic Insurance Claims Data Generator
Generates 3 interlinked CSV files: policyholders, vehicles, claims.
Uses realistic distributions for insurance domain data.
"""

import os
import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker("en_US")
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

# --- Constants & Distributions ---

STATES = {
    "Northeast": ["NY", "NJ", "PA", "CT", "MA", "NH", "VT", "ME", "RI"],
    "South": ["TX", "FL", "GA", "NC", "VA", "TN", "AL", "SC", "LA", "KY"],
    "Midwest": ["IL", "OH", "MI", "IN", "WI", "MN", "MO", "IA", "KS", "NE"],
    "West": ["CA", "WA", "OR", "CO", "AZ", "NV", "UT", "ID", "NM", "MT"],
}

# Flatten with region mapping
STATE_TO_REGION = {}
ALL_STATES = []
for region, states in STATES.items():
    for s in states:
        STATE_TO_REGION[s] = region
        ALL_STATES.append(s)

# Weighted state distribution (roughly by population)
STATE_WEIGHTS = {
    "CA": 12, "TX": 9, "FL": 7, "NY": 6, "PA": 4, "IL": 4, "OH": 4,
    "GA": 3, "NC": 3, "MI": 3, "NJ": 3, "VA": 3, "WA": 2, "AZ": 2,
    "MA": 2, "TN": 2, "IN": 2, "MO": 2, "MN": 2, "WI": 2, "CO": 2,
}

INCOME_BRACKETS = ["<25K", "25K-50K", "50K-75K", "75K-100K", "100K-150K", "150K+"]
INCOME_WEIGHTS = [10, 25, 25, 20, 13, 7]

EDUCATION_LEVELS = ["High School", "Associate", "Bachelor", "Master", "PhD"]
EDUCATION_WEIGHTS = [25, 15, 35, 20, 5]

OCCUPATIONS = [
    "Engineer", "Teacher", "Nurse", "Sales", "Manager", "Technician",
    "Driver", "Accountant", "Lawyer", "Retired", "Self-Employed", "Student",
]

VEHICLE_MAKES = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Tacoma"],
    "Honda": ["Civic", "Accord", "CR-V", "Pilot"],
    "Ford": ["F-150", "Escape", "Explorer", "Mustang"],
    "Chevrolet": ["Silverado", "Equinox", "Malibu", "Tahoe"],
    "Nissan": ["Altima", "Rogue", "Sentra", "Pathfinder"],
    "Hyundai": ["Elantra", "Tucson", "Santa Fe", "Sonata"],
    "BMW": ["3 Series", "5 Series", "X3", "X5"],
    "Tesla": ["Model 3", "Model Y", "Model S"],
}

FUEL_TYPES = ["Gasoline", "Diesel", "Hybrid", "Electric"]
FUEL_WEIGHTS = [60, 10, 20, 10]

CLAIM_TYPES = ["Collision", "Theft", "Liability", "Comprehensive"]
CLAIM_TYPE_WEIGHTS = [45, 10, 25, 20]

CLAIM_STATUSES = ["Approved", "Denied", "Pending", "Under Review"]
CLAIM_STATUS_WEIGHTS = [55, 15, 15, 15]


def weighted_state():
    """Pick a state weighted roughly by population."""
    states = list(STATE_WEIGHTS.keys())
    weights = list(STATE_WEIGHTS.values())
    chosen = random.choices(states, weights=weights, k=1)[0]
    return chosen


def generate_policyholders(n=10000):
    """Generate policyholder records."""
    print(f"Generating {n} policyholders...")
    records = []

    for i in range(1, n + 1):
        state = weighted_state()
        gender = random.choice(["M", "F"])
        age = int(random.triangular(18, 85, 38))
        policy_start = fake.date_between(start_date="-5y", end_date="-6m")
        policy_length_days = random.choice([365, 730, 1095])
        policy_end = policy_start + timedelta(days=policy_length_days)

        # Premium correlates with age and income
        base_premium = random.gauss(1200, 400)
        if age < 25:
            base_premium *= 1.5
        elif age > 65:
            base_premium *= 1.3
        base_premium = max(400, min(5000, base_premium))

        deductible = random.choice([250, 500, 1000, 1500, 2000])

        records.append({
            "policy_id": f"POL-{i:06d}",
            "first_name": fake.first_name_male() if gender == "M" else fake.first_name_female(),
            "last_name": fake.last_name(),
            "gender": gender,
            "age": age,
            "income_bracket": random.choices(INCOME_BRACKETS, weights=INCOME_WEIGHTS, k=1)[0],
            "education": random.choices(EDUCATION_LEVELS, weights=EDUCATION_WEIGHTS, k=1)[0],
            "occupation": random.choice(OCCUPATIONS),
            "marital_status": random.choice(["Single", "Married", "Divorced", "Widowed"]),
            "policy_start_date": policy_start.isoformat(),
            "policy_end_date": policy_end.isoformat(),
            "premium_amount": round(base_premium, 2),
            "deductible": deductible,
            "region_code": STATE_TO_REGION[state],
            "state": state,
        })

    return pd.DataFrame(records)


def generate_vehicles(policyholders_df, avg_vehicles_per_policy=1.2):
    """Generate vehicle records linked to policyholders."""
    n = int(len(policyholders_df) * avg_vehicles_per_policy)
    print(f"Generating {n} vehicles...")
    records = []
    policy_ids = policyholders_df["policy_id"].tolist()

    for i in range(1, n + 1):
        policy_id = random.choice(policy_ids)
        make = random.choice(list(VEHICLE_MAKES.keys()))
        model = random.choice(VEHICLE_MAKES[make])
        year = random.randint(2005, 2025)
        vehicle_age = 2025 - year
        fuel = random.choices(FUEL_TYPES, weights=FUEL_WEIGHTS, k=1)[0]
        if make == "Tesla":
            fuel = "Electric"

        records.append({
            "vehicle_id": f"VEH-{i:06d}",
            "policy_id": policy_id,
            "make": make,
            "model": model,
            "year": year,
            "vehicle_age": vehicle_age,
            "fuel_type": fuel,
            "annual_mileage": int(random.gauss(12000, 4000)),
        })

    return pd.DataFrame(records)


def generate_claims(policyholders_df, vehicles_df, n=50000):
    """Generate claim records linked to policyholders and vehicles."""
    print(f"Generating {n} claims...")
    records = []

    # Build policy->vehicles mapping
    policy_vehicles = vehicles_df.groupby("policy_id")["vehicle_id"].apply(list).to_dict()
    policy_ids = list(policy_vehicles.keys())

    # Build policy->state mapping
    policy_state = policyholders_df.set_index("policy_id")["state"].to_dict()

    for i in range(1, n + 1):
        policy_id = random.choice(policy_ids)
        vehicle_id = random.choice(policy_vehicles[policy_id])
        state = policy_state.get(policy_id, "CA")

        claim_type = random.choices(CLAIM_TYPES, weights=CLAIM_TYPE_WEIGHTS, k=1)[0]

        # Claim amount distribution depends on type
        if claim_type == "Collision":
            amount = random.gauss(8000, 5000)
        elif claim_type == "Theft":
            amount = random.gauss(15000, 8000)
        elif claim_type == "Liability":
            amount = random.gauss(12000, 7000)
        else:  # Comprehensive
            amount = random.gauss(3000, 2000)

        amount = max(100, round(amount, 2))

        # Fraud flag (~5% overall, higher for theft)
        fraud_prob = 0.12 if claim_type == "Theft" else 0.04
        fraud_flag = random.random() < fraud_prob

        # Status: fraudulent claims more likely denied
        if fraud_flag:
            status = random.choices(CLAIM_STATUSES, weights=[20, 50, 15, 15], k=1)[0]
        else:
            status = random.choices(CLAIM_STATUSES, weights=CLAIM_STATUS_WEIGHTS, k=1)[0]

        claim_date = fake.date_between(start_date="-3y", end_date="today")

        records.append({
            "claim_id": f"CLM-{i:06d}",
            "policy_id": policy_id,
            "vehicle_id": vehicle_id,
            "claim_date": claim_date.isoformat(),
            "claim_amount": amount,
            "claim_type": claim_type,
            "status": status,
            "fraud_flag": fraud_flag,
            "incident_city": fake.city(),
            "incident_state": state,
            "police_report_filed": random.random() < 0.6,
            "witnesses": random.randint(0, 4),
            "injury_claim": round(max(0, random.gauss(2000, 3000)), 2) if random.random() < 0.3 else 0.0,
            "property_claim": round(max(0, random.gauss(5000, 4000)), 2) if random.random() < 0.5 else 0.0,
        })

    return pd.DataFrame(records)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    policyholders_df = generate_policyholders(n=10000)
    vehicles_df = generate_vehicles(policyholders_df, avg_vehicles_per_policy=1.2)
    claims_df = generate_claims(policyholders_df, vehicles_df, n=50000)

    # Save to CSV
    policyholders_path = os.path.join(OUTPUT_DIR, "policyholders.csv")
    vehicles_path = os.path.join(OUTPUT_DIR, "vehicles.csv")
    claims_path = os.path.join(OUTPUT_DIR, "claims.csv")

    policyholders_df.to_csv(policyholders_path, index=False)
    vehicles_df.to_csv(vehicles_path, index=False)
    claims_df.to_csv(claims_path, index=False)

    print(f"\nData generated successfully:")
    print(f"  Policyholders: {len(policyholders_df):,} rows -> {policyholders_path}")
    print(f"  Vehicles:      {len(vehicles_df):,} rows -> {vehicles_path}")
    print(f"  Claims:        {len(claims_df):,} rows -> {claims_path}")


if __name__ == "__main__":
    main()
