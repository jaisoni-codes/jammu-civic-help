from typing import Dict, Any

# Configurable department, SLA (hours), and human label
CATEGORIES_CONFIG: Dict[str, Dict[str, Any]] = {
    "road_pothole": {
        "department_code": "JMC_ROADS",
        "department_name": "JMC Roads",
        "sla_hours": 72,
        "label": "Road & Pothole Repair",
        "label_hi": "सड़क एवं गड्ढा मरम्मत",
    },
    "streetlight": {
        "department_code": "JMC_ELECTRICAL",
        "department_name": "JMC Electrical",
        "sla_hours": 48,
        "label": "Streetlight / Street Electric Pole",
        "label_hi": "स्ट्रीट लाइट एवं खंभा मरम्मत",
    },
    "garbage": {
        "department_code": "JMC_SANITATION",
        "department_name": "JMC Sanitation",
        "sla_hours": 24,
        "label": "Garbage Dump / Waste Collection",
        "label_hi": "कचरा एवं सफाई",
    },
    "sewage_drain": {
        "department_code": "JMC_DRAINAGE",
        "department_name": "JMC Drainage",
        "sla_hours": 24,
        "label": "Open Drain / Sewage Overflow",
        "label_hi": "खुली नाली एवं सीवेज",
    },
    "water_supply": {
        "department_code": "JAL_SHAKTI",
        "department_name": "Jal Shakti (PHE)",
        "sla_hours": 24,
        "label": "Water Supply / Pipeline Leak",
        "label_hi": "जल आपूर्ति एवं पाइपलाइन लीकेज",
    },
    "power": {
        "department_code": "POWER_DEPT",
        "department_name": "Power Dept (JPDCL)",
        "sla_hours": 24,
        "label": "Power Cut / Hanging Live Wire",
        "label_hi": "बिजली आपूर्ति एवं खुला तार",
    },
    "stray_animal": {
        "department_code": "JMC_VET",
        "department_name": "JMC Veterinary",
        "sla_hours": 48,
        "label": "Stray Cattle / Animal Welfare",
        "label_hi": "आवारा पशु प्रबंधन",
    },
    "other": {
        "department_code": "JMC_GENERAL",
        "department_name": "JMC General",
        "sla_hours": 72,
        "label": "General Grievance",
        "label_hi": "सामान्य नागरिक शिकायत",
    },
}

# Trust Index Component Weights
TRUST_WEIGHTS = {
    "response": 0.15,      # r = clamp(1 - median_hours_to_first_response / 24, 0, 1)
    "closure": 0.25,       # c = share of due tickets closed within SLA; unverified = 0.5
    "reopen": 0.15,        # o = clamp(1 - 2 * reopen_rate, 0, 1)
    "satisfaction": 0.20,  # s = mean((rating - 1) / 4)
    "proactive": 0.10,     # p = clamp(broadcasts_30d / 4, 0, 1) * delivery_rate
    "participation": 0.15, # q = clamp(active_citizens / (subscribed * 0.20), 0, 1)
}

# Priority score weights
PRIORITY_WEIGHTS = {
    "affected": 0.30,      # min(1, ln(1+affected_count)/ln(51))
    "severity": 0.25,      # severity / 5
    "age": 0.20,           # min(1, age_days / 14)
    "safety": 0.15,        # safety_flag (0, 0.5, 1.0)
    "vulnerability": 0.10, # 1 if POI <= 300m else 0
}
