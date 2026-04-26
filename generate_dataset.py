import os
import random
import pandas as pd
from pathlib import Path

random.seed(42)

# India geography: state -> {district -> [cities]}
INDIA_GEO = {
    "Uttar Pradesh": {
        "Lucknow":    ["Lucknow", "Gomti Nagar", "Hazratganj"],
        "Varanasi":   ["Varanasi", "Sarnath", "Ramnagar"],
        "Kanpur":     ["Kanpur", "Kanpur Nagar", "Armapur"],
        "Agra":       ["Agra", "Firozabad", "Mathura"],
        "Allahabad":  ["Prayagraj", "Naini", "Jhunsi"],
        "Meerut":     ["Meerut", "Ghaziabad", "Noida"],
        "Bareilly":   ["Bareilly", "Pilibhit", "Shahjahanpur"],
        "Gorakhpur":  ["Gorakhpur", "Deoria", "Kushinagar"],
    },
    "Maharashtra": {
        "Mumbai":      ["Mumbai", "Bandra", "Dharavi", "Andheri"],
        "Pune":        ["Pune", "Pimpri", "Chinchwad", "Hinjewadi"],
        "Nagpur":      ["Nagpur", "Wardha", "Yavatmal"],
        "Nashik":      ["Nashik", "Deolali", "Sinnar"],
        "Aurangabad":  ["Aurangabad", "Jalna", "Osmanabad"],
        "Solapur":     ["Solapur", "Pandharpur", "Barshi"],
    },
    "Tamil Nadu": {
        "Chennai":        ["Chennai", "Tambaram", "Avadi", "Porur"],
        "Coimbatore":     ["Coimbatore", "Tiruppur", "Pollachi"],
        "Madurai":        ["Madurai", "Dindigul", "Sivaganga"],
        "Salem":          ["Salem", "Namakkal", "Dharmapuri"],
        "Tiruchirappalli":["Tiruchirappalli", "Karur", "Perambalur"],
    },
    "West Bengal": {
        "Kolkata":           ["Kolkata", "Howrah", "Dum Dum", "Salt Lake"],
        "North 24 Parganas": ["Barasat", "Barrackpore", "Habra"],
        "Bardhaman":         ["Bardhaman", "Asansol", "Durgapur"],
        "Murshidabad":       ["Berhampore", "Jangipur", "Kandi"],
        "Nadia":             ["Krishnanagar", "Ranaghat", "Santipur"],
    },
    "Karnataka": {
        "Bengaluru Urban": ["Bengaluru", "Whitefield", "Electronic City"],
        "Mysuru":          ["Mysuru", "Hunsur", "Nanjangud"],
        "Dharwad":         ["Hubballi", "Dharwad", "Gadag"],
        "Belagavi":        ["Belagavi", "Khanapur", "Bailhongal"],
    },
    "Rajasthan": {
        "Jaipur":  ["Jaipur", "Ajmer", "Sanganer"],
        "Jodhpur": ["Jodhpur", "Barmer", "Jaisalmer"],
        "Kota":    ["Kota", "Baran", "Bundi"],
        "Udaipur": ["Udaipur", "Chittorgarh", "Dungarpur"],
    },
    "Madhya Pradesh": {
        "Bhopal":   ["Bhopal", "Sehore", "Vidisha"],
        "Indore":   ["Indore", "Dewas", "Ujjain"],
        "Gwalior":  ["Gwalior", "Shivpuri", "Datia"],
        "Jabalpur": ["Jabalpur", "Katni", "Narsinghpur"],
    },
    "Bihar": {
        "Patna":       ["Patna", "Danapur", "Hajipur"],
        "Gaya":        ["Gaya", "Bodh Gaya", "Nawada"],
        "Muzaffarpur": ["Muzaffarpur", "Sitamarhi", "Sheohar"],
        "Bhagalpur":   ["Bhagalpur", "Banka", "Khagaria"],
    },
    "Gujarat": {
        "Ahmedabad": ["Ahmedabad", "Gandhinagar", "Sanand"],
        "Surat":     ["Surat", "Navsari", "Valsad"],
        "Vadodara":  ["Vadodara", "Anand", "Kheda"],
        "Rajkot":    ["Rajkot", "Junagadh", "Amreli"],
    },
    "Andhra Pradesh": {
        "Visakhapatnam": ["Visakhapatnam", "Anakapalle", "Bheemunipatnam"],
        "Krishna":       ["Vijayawada", "Machilipatnam", "Gudivada"],
        "Guntur":        ["Guntur", "Tenali", "Narasaraopet"],
        "Chittoor":      ["Tirupati", "Chittoor", "Madanapalle"],
    },
    "Telangana": {
        "Hyderabad":  ["Hyderabad", "Secunderabad", "Cyberabad"],
        "Warangal":   ["Warangal", "Hanamkonda", "Kazipet"],
        "Rangareddy": ["Kukatpally", "LB Nagar", "Hayathnagar"],
    },
    "Punjab": {
        "Ludhiana":  ["Ludhiana", "Khanna", "Samrala"],
        "Amritsar":  ["Amritsar", "Tarn Taran", "Ajnala"],
        "Jalandhar": ["Jalandhar", "Nakodar", "Phagwara"],
    },
    "Haryana": {
        "Gurugram":  ["Gurugram", "Manesar", "Pataudi"],
        "Faridabad": ["Faridabad", "Ballabhgarh", "Palwal"],
        "Rohtak":    ["Rohtak", "Jhajjar", "Sonipat"],
    },
    "Odisha": {
        "Khordha": ["Bhubaneswar", "Khordha", "Jatni"],
        "Cuttack": ["Cuttack", "Choudwar", "Kendrapara"],
        "Ganjam":  ["Berhampur", "Chhatrapur", "Aska"],
    },
    "Kerala": {
        "Thiruvananthapuram": ["Thiruvananthapuram", "Neyyattinkara", "Attingal"],
        "Ernakulam":          ["Kochi", "Aluva", "Perumbavoor"],
        "Kozhikode":          ["Kozhikode", "Vadakara", "Koyilandy"],
    },
    "Assam": {
        "Kamrup":    ["Guwahati", "Nalbari", "Barpeta"],
        "Dibrugarh": ["Dibrugarh", "Tinsukia", "Sibsagar"],
        "Cachar":    ["Silchar", "Sonai", "Lakhipur"],
    },
    "Jharkhand": {
        "Ranchi":  ["Ranchi", "Hatia", "Kanke"],
        "Dhanbad": ["Dhanbad", "Bokaro", "Sindri"],
    },
    "Chhattisgarh": {
        "Raipur":   ["Raipur", "Durg", "Bhilai"],
        "Bilaspur": ["Bilaspur", "Korba", "Raigarh"],
    },
    "Uttarakhand": {
        "Dehradun": ["Dehradun", "Rishikesh", "Haridwar"],
        "Nainital": ["Nainital", "Haldwani", "Ramnagar"],
    },
    "Himachal Pradesh": {
        "Shimla":  ["Shimla", "Solan", "Baddi"],
        "Kangra":  ["Dharamsala", "Palampur", "Nurpur"],
    },
    "Jammu and Kashmir": {
        "Jammu":    ["Jammu", "Kathua", "Samba"],
        "Srinagar": ["Srinagar", "Baramulla", "Anantnag"],
    },
    "Goa": {
        "North Goa": ["Panaji", "Mapusa", "Calangute"],
        "South Goa": ["Margao", "Vasco da Gama", "Ponda"],
    },
    "Manipur":          {"Imphal East":     ["Imphal", "Porompat", "Heingang"]},
    "Meghalaya":        {"East Khasi Hills": ["Shillong", "Mawlai", "Nongthymmai"]},
    "Tripura":          {"West Tripura":    ["Agartala", "Majlishpur", "Bishalgarh"]},
    "Nagaland":         {"Kohima":          ["Kohima", "Dimapur", "Medziphema"]},
    "Arunachal Pradesh":{"Papum Pare":      ["Itanagar", "Naharlagun", "Nirjuli"]},
    "Sikkim":           {"East Sikkim":     ["Gangtok", "Singtam", "Rangpo"]},
    "Mizoram":          {"Aizawl":          ["Aizawl", "Lunglei", "Champhai"]},
    "Delhi": {
        "New Delhi":   ["New Delhi", "Connaught Place", "Karol Bagh"],
        "South Delhi": ["Hauz Khas", "Saket", "Vasant Kunj"],
        "North Delhi": ["Civil Lines", "Model Town", "Rohini"],
    },
}

# Higher weight = more records for that state
STATE_WEIGHTS = {
    "Uttar Pradesh": 150, "Maharashtra": 120, "Tamil Nadu": 90,
    "West Bengal": 80,    "Karnataka": 70,    "Rajasthan": 60,
    "Madhya Pradesh": 60, "Bihar": 50,        "Gujarat": 50,
    "Andhra Pradesh": 50, "Telangana": 45,    "Punjab": 35,
    "Haryana": 35,        "Odisha": 35,       "Kerala": 35,
    "Assam": 30,          "Jharkhand": 25,    "Chhattisgarh": 25,
    "Uttarakhand": 20,    "Himachal Pradesh": 15, "Jammu and Kashmir": 15,
    "Goa": 10,            "Delhi": 40,        "Manipur": 8,
    "Meghalaya": 8,       "Tripura": 7,       "Nagaland": 6,
    "Arunachal Pradesh": 6, "Sikkim": 5,      "Mizoram": 5,
}

FACILITY_TYPES = {
    "PHC": 30, "Government Hospital": 20, "Private Clinic": 18,
    "Nursing Home": 12, "CHC": 10, "Diagnostic Centre": 6, "Trust Hospital": 4,
}

OWNERSHIP_MAP = {
    "PHC": "government", "CHC": "government",
    "Government Hospital": "government", "Private Clinic": "private",
    "Nursing Home": "private", "Diagnostic Centre": "private",
    "Trust Hospital": "trust",
}

SPECIALTIES = [
    "Cardiology", "Orthopedics", "Gynecology", "Pediatrics", "Neurology",
    "Oncology", "Dermatology", "Ophthalmology", "ENT", "General Surgery",
    "Internal Medicine", "Psychiatry", "Radiology", "Pathology", "Pulmonology",
]

DEITY_NAMES = ["Ram", "Shiva", "Lakshmi", "Durga", "Ganesh", "Krishna", "Vishnu"]
SURNAMES    = ["Sharma", "Patel", "Kumar", "Singh", "Reddy", "Nair", "Rao", "Iyer"]
SUFFIXES    = ["Nagar", "Pur", "Ganj", "Peth", "Wadi", "Bagh", "Khurd", "Kalan"]
SOURCES     = [
    "NHM portal scrape, automated",
    "District Health Office register 2023",
    "Hospital website self-reported",
    "State HMIS database",
    "Field survey data, 2022",
    "NGO health directory",
]


def weighted_choice(options):
    keys = list(options.keys())
    weights = list(options.values())
    return random.choices(keys, weights=weights, k=1)[0]


def maybe_none(value, prob):
    return None if random.random() < prob else value


# --- messiness helpers ---

def add_typo(s):
    if len(s) < 4:
        return s
    i = random.randint(1, len(s) - 2)
    return s[:i] + s[i+1] + s[i] + s[i+2:]


def abbreviate(s):
    replacements = {
        "Government": random.choice(["Govt", "Govt.", "GOV"]),
        "Hospital":   random.choice(["Hosp", "Hosp.", "HSP"]),
        "District":   random.choice(["Distt", "Dist."]),
        "Primary":    "Prim.",
        "Community":  "Comm.",
        "Centre":     random.choice(["Ctr", "Center"]),
        "Private":    random.choice(["Pvt", "Pvt."]),
    }
    for full, short in replacements.items():
        if full in s:
            return s.replace(full, short, 1)
    return s


def make_messy(value, rate=0.35):
    if not value or random.random() > rate:
        return value
    choice = random.randint(0, 3)
    if choice == 0:
        return add_typo(str(value))
    elif choice == 1:
        return abbreviate(str(value))
    elif choice == 2:
        return random.choice([str(value).upper(), str(value).lower()])
    else:
        return str(value) + " " + random.choice(["(approx)", "(est.)", "* verify"])


# --- field generators ---

def make_name(ftype, district, city):
    if ftype == "PHC":
        return f"Primary Health Centre {city} {random.choice(SUFFIXES)}"
    if ftype == "CHC":
        return f"Community Health Centre {district}"
    if ftype == "Government Hospital":
        return random.choice([
            f"Government District Hospital {district}",
            f"District Hospital {district}",
            f"Civil Hospital {city}",
        ])
    if ftype == "Private Clinic":
        return f"Dr. {random.choice(SURNAMES)} Clinic"
    if ftype == "Nursing Home":
        return f"Sri {random.choice(DEITY_NAMES)} Nursing Home {city}"
    if ftype == "Diagnostic Centre":
        return f"{random.choice(SURNAMES)} Diagnostic Centre"
    return f"{random.choice(DEITY_NAMES)} Trust Hospital {district}"


def make_beds(ftype):
    ranges = {
        "PHC": (6, 30), "CHC": (30, 100), "Government Hospital": (50, 500),
        "Private Clinic": (0, 30), "Nursing Home": (10, 80),
        "Diagnostic Centre": (0, 10), "Trust Hospital": (30, 200),
    }
    lo, hi = ranges.get(ftype, (10, 100))
    n = random.randint(lo, hi)
    return random.choice([str(n), f"~{n}", f"approx {n}", f"{n} beds"])


def make_specialties(ftype):
    if ftype in ("PHC", "Dispensary"):
        return ""
    count = random.randint(1, 4 if ftype == "Government Hospital" else 2)
    picked = random.sample(SPECIALTIES, min(count, len(SPECIALTIES)))
    messy = [make_messy(s, 0.25) for s in picked]
    return random.choice([", ", " / "]).join(messy)


def make_emergency(ftype):
    probs = {
        "PHC": 0.2, "CHC": 0.5, "Government Hospital": 0.9,
        "Private Clinic": 0.3, "Nursing Home": 0.5,
        "Diagnostic Centre": 0.05, "Trust Hospital": 0.7,
    }
    if random.random() < probs.get(ftype, 0.4):
        return random.choice(["Yes", "YES", "24x7", "yes - emergency ward"])
    return random.choice(["No", "NO", "Not available"])


def make_operational():
    return random.choices(
        ["Operational", "Open", "Functioning", "Under Renovation", "Closed", "Operational"],
        weights=[40, 20, 20, 8, 5, 7], k=1
    )[0]


def make_phone():
    code = random.choice(["011", "022", "033", "044", "0522", "0141"])
    num  = random.randint(1000000, 9999999)
    return random.choice([f"{code}-{num}", f"+91-{code[1:]}-{num}", "N/A"])


def make_pincode(state):
    prefixes = {
        "Uttar Pradesh": "22", "Maharashtra": "40", "Tamil Nadu": "60",
        "West Bengal": "70",   "Karnataka": "56",   "Rajasthan": "30",
        "Madhya Pradesh": "46","Bihar": "80",        "Gujarat": "38",
        "Delhi": "11",
    }
    prefix = prefixes.get(state, str(random.randint(10, 89)))
    pin = prefix + str(random.randint(1000, 9999))
    return random.choices([pin, pin[:3]+" "+pin[3:], "000000", pin], weights=[60, 15, 5, 20], k=1)[0]


def inject_contradiction(record):
    r = record.copy()
    choice = random.randint(0, 4)
    if choice == 0:
        r["facility_type"] = "PHC"
        r["beds"] = str(random.randint(200, 500))
    elif choice == 1:
        r["facility_name"] = f"Government District Hospital {r.get('district','')}"
        r["ownership"] = "Private"
    elif choice == 2:
        r["operational_status"] = "Closed"
        r["emergency_services"] = "24x7"
    elif choice == 3:
        r["facility_type"] = "Dispensary"
        r["accreditation"] = "NABH"
    else:
        other = [s for s in INDIA_GEO if s != r.get("state")]
        r["state"] = random.choice(other)
    return r


def make_record(row_id):
    state    = weighted_choice(STATE_WEIGHTS)
    district = random.choice(list(INDIA_GEO[state].keys()))
    city     = random.choice(INDIA_GEO[state][district])
    ftype    = weighted_choice(FACILITY_TYPES)

    # Map display type to a slightly cleaner label
    type_label = {
        "PHC": "PHC", "CHC": "CHC",
        "Government Hospital": "Hospital", "Private Clinic": "Clinic",
        "Nursing Home": "Nursing Home", "Diagnostic Centre": "Diagnostic Centre",
        "Trust Hospital": "Hospital",
    }[ftype]

    name = make_name(ftype, district, city)
    addr = f"{random.randint(1,999)}, {random.choice(['Main Road','Hospital Road','MG Road'])}, {city}"

    record = {
        "row_id":             row_id,
        "facility_name":      maybe_none(make_messy(name, 0.4), 0.05),
        "facility_type":      make_messy(type_label, 0.3),
        "address_raw":        make_messy(addr, 0.2),
        "city":               make_messy(city, 0.2),
        "district":           make_messy(district, 0.15),
        "state":              make_messy(state, 0.15),
        "pincode":            maybe_none(make_pincode(state), 0.15),
        "phone":              maybe_none(make_phone(), 0.25),
        "beds":               maybe_none(make_beds(ftype), 0.20),
        "specialties":        maybe_none(make_specialties(ftype), 0.10),
        "ownership":          make_messy(OWNERSHIP_MAP.get(ftype, "private"), 0.3),
        "accreditation":      "" if ftype in ("PHC","CHC") else (
                                  random.choice(["NABH", "NABL", "ISO 9001", ""])
                                  if random.random() < 0.2 else ""
                              ),
        "operational_status": make_messy(make_operational(), 0.2),
        "emergency_services": make_messy(make_emergency(ftype), 0.2),
        "source_note":        random.choice(SOURCES),
    }

    if random.random() < 0.15:
        record = inject_contradiction(record)

    return record


def main():
    Path("data").mkdir(exist_ok=True)
    out = Path("data/raw_facilities.xlsx")

    print("Generating 10,000 records...")
    rows = [make_record(i + 1) for i in range(10_000)]
    df = pd.DataFrame(rows)

    # Punch some near-empty rows to stress-test the pipeline
    for _ in range(30):
        idx = random.randint(0, len(df) - 1)
        for col in ["facility_name", "city", "district", "beds", "phone"]:
            df.at[idx, col] = None

    df.to_excel(out, index=False, engine="openpyxl")

    meta = pd.DataFrame([{
        "generated_at": pd.Timestamp.now().isoformat(),
        "total_rows": len(df),
        "contradiction_rate": "~15%",
    }])
    with pd.ExcelWriter(out, engine="openpyxl", mode="a") as writer:
        meta.to_excel(writer, sheet_name="Metadata", index=False)

    print(f"Saved {len(df):,} rows to {out}")
    print(f"Unique raw states: {df['state'].nunique()} (includes typos)")


if __name__ == "__main__":
    main()
