import math
import numpy as np
import networkx as nx
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# ---------------------------------------------------------
# 1. NAGPUR ROAD NETWORK GRAPH DEFINITIONS
# Bounded in Nagpur: Lat: 21.0500 to 21.2000, Lon: 79.0000 to 79.1800
# ---------------------------------------------------------

NAGPUR_NODES = {
    "sitabuldi": {
        "name": "Sitabuldi Interchange (Central Hub)",
        "lat": 21.1466,
        "lon": 79.0888,
        "elevation": 314.0,
        "zone": "Central Hub",
        "description": "Primary multimodal central interchange, high peak-hour congestion."
    },
    "mihan": {
        "name": "MIHAN / SEZ Cargo Hub (South Zone)",
        "lat": 21.0664,
        "lon": 79.0534,
        "elevation": 310.0,
        "zone": "South Zone",
        "description": "Multi-modal International Cargo Hub and Airport SEZ."
    },
    "vnit": {
        "name": "VNIT Campus (West Zone)",
        "lat": 21.1227,
        "lon": 79.0494,
        "elevation": 320.0,
        "zone": "West Zone",
        "description": "Visvesvaraya National Institute of Technology western perimeter."
    },
    "wardhaman_nagar": {
        "name": "Wardhaman Nagar / Kalamna Market (East Freight Zone)",
        "lat": 21.1578,
        "lon": 79.1350,
        "elevation": 310.0,
        "zone": "East Freight Zone",
        "description": "Major commercial and wholesale transit corridor in East Nagpur."
    },
    "kamptee_road": {
        "name": "Kamptee Road Logistics Corridor (North Zone)",
        "lat": 21.1925,
        "lon": 79.1120,
        "elevation": 312.0,
        "zone": "North Zone",
        "description": "Heavy freight logistics entry corridor connecting North Nagpur."
    },
    "seminary_hills": {
        "name": "Seminary Hills Elevation Node (Steep Terrain)",
        "lat": 21.1702,
        "lon": 79.0661,
        "elevation": 375.0,
        "zone": "North-West Ridge",
        "description": "Elevated ridge profile with steep gradients exceeding 5% incline."
    },
    # Intermediate realistic arterial intersection nodes
    "airport": {
        "name": "Nagpur Airport Wardha Road",
        "lat": 21.0922,
        "lon": 79.0625,
        "elevation": 312.0,
        "zone": "South Corridor",
        "description": "Wardha Road arterial near Dr. Ambedkar International Airport."
    },
    "chhatrapati_sq": {
        "name": "Chhatrapati Square Junction",
        "lat": 21.1135,
        "lon": 79.0740,
        "elevation": 314.0,
        "zone": "South-Central",
        "description": "Major ring road & Wardha Road interchange."
    },
    "rahate_colony": {
        "name": "Rahate Colony / Wardha Rd Core",
        "lat": 21.1290,
        "lon": 79.0810,
        "elevation": 315.0,
        "zone": "Central Spine",
        "description": "Dense urban corridor leading into central bottlenecks."
    },
    "dhantoli_eco": {
        "name": "Dhantoli Green Bypass",
        "lat": 21.1340,
        "lon": 79.0760,
        "elevation": 315.0,
        "zone": "Eco Bypass",
        "description": "Smooth-flowing corridor avoiding main transit bottlenecks."
    },
    "shankar_nagar": {
        "name": "Shankar Nagar Square",
        "lat": 21.1350,
        "lon": 79.0620,
        "elevation": 322.0,
        "zone": "West Corridor",
        "description": "Arterial connector linking West Nagpur to Civil Lines."
    },
    "dharampeth": {
        "name": "Dharampeth Commercial Node",
        "lat": 21.1440,
        "lon": 79.0680,
        "elevation": 325.0,
        "zone": "West-Central",
        "description": "Smooth flowing avenue bypassing core market bottlenecks."
    },
    "civil_lines": {
        "name": "Civil Lines Green Corridor",
        "lat": 21.1540,
        "lon": 79.0760,
        "elevation": 322.0,
        "zone": "Central-North Eco Corridor",
        "description": "Low-density canopy shaded corridor with synchronized traffic flow."
    },
    "law_college_sq": {
        "name": "Law College Square",
        "lat": 21.1495,
        "lon": 79.0605,
        "elevation": 328.0,
        "zone": "West-North Transition",
        "description": "Approach junction leading upwards into Seminary Hills ridge."
    },
    "sadar": {
        "name": "Sadar Residency Road",
        "lat": 21.1620,
        "lon": 79.0840,
        "elevation": 320.0,
        "zone": "North-Central",
        "description": "Connecting node between central zone, Seminary Hills, and Mankapur."
    },
    "mankapur": {
        "name": "Mankapur Ring Road Junction",
        "lat": 21.1850,
        "lon": 79.0850,
        "elevation": 318.0,
        "zone": "North Outer",
        "description": "Bypass connector towards Kamptee Road freight artery."
    },
    "cotton_market": {
        "name": "Cotton Market / Central Station",
        "lat": 21.1420,
        "lon": 79.0950,
        "elevation": 313.0,
        "zone": "East-Central Hub",
        "description": "Very high density freight & market zone with extreme standstill idling."
    },
    "central_avenue": {
        "name": "Central Avenue Spine",
        "lat": 21.1490,
        "lon": 79.1080,
        "elevation": 312.0,
        "zone": "East Commercial Spine",
        "description": "Primary commercial east-west spine subject to bottleneck congestion."
    },
    "automotive_sq": {
        "name": "Automotive Square (Ring Road East)",
        "lat": 21.1870,
        "lon": 79.1220,
        "elevation": 311.0,
        "zone": "North-East Hub",
        "description": "Heavy industrial logistics bypass linking Kamptee and Kalamna."
    },
    "kalamna_mkt": {
        "name": "Kalamna Wholesale Agro Hub",
        "lat": 21.1690,
        "lon": 79.1450,
        "elevation": 309.0,
        "zone": "East Freight Outer",
        "description": "Agricultural terminal with dedicated freight corridors."
    },
    "ring_road_east": {
        "name": "Eastern Bypass Corridor",
        "lat": 21.1350,
        "lon": 79.1380,
        "elevation": 308.0,
        "zone": "East Perimeter",
        "description": "High-speed free-flow bypass avoiding Central Avenue bottlenecks."
    },
    "subhash_road_eco": {
        "name": "Subhash Road Eco Transit Way",
        "lat": 21.1510,
        "lon": 79.1120,
        "elevation": 312.0,
        "zone": "East Eco Arterial",
        "description": "Low emission transit link avoiding Central Avenue market congestion."
    },
    "seminary_hills_gentle": {
        "name": "Seminary Hills Gentle Ridge Bypass",
        "lat": 21.1620,
        "lon": 79.0690,
        "elevation": 345.0,
        "zone": "Ridge Eco Approach",
        "description": "Gradual gradient ascent under 4% slope avoiding the steep 6.8% incline."
    }
}


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 3)


# Edge definitions: (from_node, to_node, distance_km, slope_percent, is_bottleneck, road_name)
# High-slope values (>5% grade) explicitly mapped towards Seminary Hills.
# Flat grades (0% to 1%) mapped along MIHAN to Sitabuldi Wardha Road corridors.
ROAD_SEGMENTS = [
    # South Corridor (MIHAN -> Sitabuldi via Wardha Road - Flat grade 0.3% - 0.5%)
    ("mihan", "airport", 3.1, 0.4, False, "Wardha Road South"),
    ("airport", "mihan", 3.1, -0.4, False, "Wardha Road South"),
    ("airport", "chhatrapati_sq", 2.5, 0.5, False, "Wardha Road Express"),
    ("chhatrapati_sq", "airport", 2.5, -0.5, False, "Wardha Road Express"),
    
    # Direct Wardha Road route to Sitabuldi (Shortest distance, but heavy standstill bottleneck at Rahate Colony/Sitabuldi flyover)
    ("chhatrapati_sq", "rahate_colony", 1.7, 0.4, True, "Wardha Road Arterial (Chokepoint)"),
    ("rahate_colony", "chhatrapati_sq", 1.7, -0.4, True, "Wardha Road Arterial (Chokepoint)"),
    ("rahate_colony", "sitabuldi", 1.8, 0.4, True, "Sitabuldi Central Spine (Severe Jammed Bottleneck)"),
    ("sitabuldi", "rahate_colony", 1.8, -0.4, True, "Sitabuldi Central Spine (Severe Jammed Bottleneck)"),

    # Eco Green Bypass via Dhantoli (Free-flowing, synchronized signals, low carbon)
    ("chhatrapati_sq", "dhantoli_eco", 1.8, 0.1, False, "Dhantoli Green Transit Bypass"),
    ("dhantoli_eco", "chhatrapati_sq", 1.8, -0.1, False, "Dhantoli Green Transit Bypass"),
    ("dhantoli_eco", "sitabuldi", 1.85, 0.1, False, "Temple Road Eco Corridor"),
    ("sitabuldi", "dhantoli_eco", 1.85, -0.1, False, "Temple Road Eco Corridor"),

    # West Zone Connections (VNIT, Shankar Nagar, Dharampeth)
    ("chhatrapati_sq", "vnit", 1.8, 0.6, False, "South Ambazari Road"),
    ("vnit", "chhatrapati_sq", 1.8, -0.6, False, "South Ambazari Road"),
    ("vnit", "shankar_nagar", 1.5, 0.5, False, "North Ambazari Road"),
    ("shankar_nagar", "vnit", 1.5, -0.5, False, "North Ambazari Road"),
    ("shankar_nagar", "dharampeth", 1.2, 0.4, False, "West High Court Road"),
    ("dharampeth", "shankar_nagar", 1.2, -0.4, False, "West High Court Road"),
    ("dharampeth", "sitabuldi", 1.9, 0.2, False, "Amravati Road Connector"),
    ("sitabuldi", "dharampeth", 1.9, -0.2, False, "Amravati Road Connector"),

    # Seminary Hills Ridge (>5% STEEP GRADE - Explicit Topography Profile)
    # Direct short climb with steep incline > 5% grade (6.8% slope -> S_i = 1.8 penalty!)
    ("law_college_sq", "seminary_hills", 1.8, 6.8, False, "Seminary Hills Direct Incline (Steep 6.8% Grade)"),
    ("seminary_hills", "law_college_sq", 1.8, -6.8, False, "Seminary Hills Direct Descent (Downhill -6.8%)"),
    ("dharampeth", "law_college_sq", 0.8, 0.7, False, "Ravindranath Tagore Marg"),
    ("law_college_sq", "dharampeth", 0.8, -0.7, False, "Ravindranath Tagore Marg"),

    # Gentle Gradient Eco Approach (Slightly longer distance, but slope 3.2% < 5% -> S_i = 1.0, saves carbon)
    ("dharampeth", "seminary_hills_gentle", 1.4, 1.8, False, "West Hill Gentle Avenue"),
    ("seminary_hills_gentle", "dharampeth", 1.4, -1.8, False, "West Hill Gentle Avenue"),
    ("seminary_hills_gentle", "seminary_hills", 1.3, 3.2, False, "Ridge Crest Eco Gradient Approach"),
    ("seminary_hills", "seminary_hills_gentle", 1.3, -3.2, False, "Ridge Crest Eco Gradient Descent"),

    ("sadar", "seminary_hills", 1.9, 6.2, False, "Katol Road Hill Approach (Steep 6.2% Grade)"),
    ("seminary_hills", "sadar", 1.9, -6.2, False, "Katol Road Hill Descent (Downhill -6.2%)"),
    ("seminary_hills", "mankapur", 2.0, -4.8, False, "Gorewada Link Descent"),
    ("mankapur", "seminary_hills", 2.0, 4.8, False, "Gorewada Link Incline (4.8% Grade)"),

    # Flat Eco Corridor bypassing Seminary Hills ridge
    ("dharampeth", "civil_lines", 1.8, 0.2, False, "Civil Lines Shaded Avenue"),
    ("civil_lines", "dharampeth", 1.8, -0.2, False, "Civil Lines Shaded Avenue"),
    ("civil_lines", "sadar", 1.5, 0.2, False, "Residency Road Arterial"),
    ("sadar", "civil_lines", 1.5, -0.2, False, "Residency Road Arterial"),
    ("sadar", "mankapur", 2.6, 0.3, False, "Koradi Road Northway"),
    ("mankapur", "sadar", 2.6, -0.3, False, "Koradi Road Northway"),

    # North Corridor (Sadar, Mankapur, Kamptee Road)
    ("sitabuldi", "sadar", 1.8, 0.4, True, "Mount Road Bottleneck"),
    ("sadar", "sitabuldi", 1.8, -0.4, True, "Mount Road Bottleneck"),
    ("mankapur", "kamptee_road", 2.8, 0.1, False, "Outer Ring Road North Segment"),
    ("kamptee_road", "mankapur", 2.8, -0.1, False, "Outer Ring Road North Segment"),
    ("sitabuldi", "kamptee_road", 5.0, 0.2, True, "Old Kamptee Road Freight Bottleneck"),
    ("kamptee_road", "sitabuldi", 5.0, -0.2, True, "Old Kamptee Road Freight Bottleneck"),

    # East Freight Zone & Central Bottlenecks (Cotton Market, Central Avenue, Wardhaman Nagar)
    ("sitabuldi", "cotton_market", 1.0, 0.1, True, "Cotton Market Wholesale Chokepoint"),
    ("cotton_market", "sitabuldi", 1.0, -0.1, True, "Cotton Market Wholesale Chokepoint"),
    ("cotton_market", "central_avenue", 1.5, 0.2, True, "Central Avenue Wholesale Bottleneck"),
    ("central_avenue", "cotton_market", 1.5, -0.2, True, "Central Avenue Wholesale Bottleneck"),
    ("central_avenue", "wardhaman_nagar", 2.8, 0.1, True, "Central Avenue East Freight Spine"),
    ("wardhaman_nagar", "central_avenue", 2.8, -0.1, True, "Central Avenue East Freight Spine"),

    # East Eco Arterial Bypass via Subhash Road (Slightly longer distance, but 0 idle bottlenecks)
    ("wardhaman_nagar", "subhash_road_eco", 2.7, 0.1, False, "Subhash Road Eco Bypass"),
    ("subhash_road_eco", "wardhaman_nagar", 2.7, -0.1, False, "Subhash Road Eco Bypass"),
    ("subhash_road_eco", "sitabuldi", 2.8, 0.1, False, "Subhash Transit Link to Central Hub"),
    ("sitabuldi", "subhash_road_eco", 2.8, -0.1, False, "Subhash Transit Link to Central Hub"),

    # East Outer Low-Carbon Logistics Bypass (Kalamna, Automotive Sq, Eastern Ring Rd)
    ("kamptee_road", "automotive_sq", 1.5, 0.1, False, "Automotive Square Express"),
    ("automotive_sq", "kamptee_road", 1.5, -0.1, False, "Automotive Square Express"),
    ("automotive_sq", "kalamna_mkt", 3.0, 0.2, False, "Kalamna Wholesale Freight Arterial"),
    ("kalamna_mkt", "automotive_sq", 3.0, -0.2, False, "Kalamna Wholesale Freight Arterial"),
    ("kalamna_mkt", "wardhaman_nagar", 1.6, 0.1, False, "Old Bhandara Road Connector"),
    ("wardhaman_nagar", "kalamna_mkt", 1.6, -0.1, False, "Old Bhandara Road Connector"),
    ("wardhaman_nagar", "ring_road_east", 2.5, 0.2, False, "Pardi Ring Road Bypass"),
    ("ring_road_east", "wardhaman_nagar", 2.5, -0.2, False, "Pardi Ring Road Bypass"),
    ("ring_road_east", "chhatrapati_sq", 6.5, 0.1, False, "Outer Ring Road South-East Express Bypass"),
    ("chhatrapati_sq", "ring_road_east", 6.5, -0.1, False, "Outer Ring Road South-East Express Bypass")
]


# ---------------------------------------------------------
# 2. MACHINE LEARNING ENGINE (RANDOM FOREST FOR TRAFFIC & IDLE TIME)
# Maps segment_id, day_of_week, and time_of_day to:
# - Traffic Status (Clear, Slow, Jammed)
# - T_idle (Stationary Standstill Idle Duration in Seconds)
# ---------------------------------------------------------

class TrafficMLPredictor:
    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=30, random_state=42, max_depth=8)
        self.classifier = RandomForestClassifier(n_estimators=30, random_state=42, max_depth=8)
        self.segment_map = {}
        self.unique_segments = []
        self._train_models()

    def _train_models(self):
        """Generates synthetic historical training data grounded in Nagpur traffic patterns and fits models."""
        self.unique_segments = sorted(list(set([f"{u}->{v}" for u, v, _, _, _, _ in ROAD_SEGMENTS])))
        self.segment_map = {seg: idx for idx, seg in enumerate(self.unique_segments)}

        bottleneck_set = set([
            f"{u}->{v}" for u, v, _, _, is_bn, _ in ROAD_SEGMENTS if is_bn
        ])

        X_train = []
        y_idle = []
        y_status = []

        # Synthetic training data across 7 days, 24 hours
        for seg in self.unique_segments:
            seg_idx = self.segment_map[seg]
            is_bn = seg in bottleneck_set

            for dow in range(7):  # 0: Monday .. 6: Sunday
                is_weekend = dow >= 5
                for hour in range(24):
                    for minute in [0, 30]:
                        time_val = hour + (minute / 60.0)
                        is_morning_rush = (8.5 <= time_val <= 11.5)
                        is_evening_rush = (17.5 <= time_val <= 20.5)
                        is_peak = (is_morning_rush or is_evening_rush) and not is_weekend

                        if is_bn:
                            if is_peak:
                                # Bottlenecks (Sitabuldi, Central Ave, Cotton Mkt) during rush hour: 280-480s idle
                                idle = 280.0 + (time_val * 9.0) % 150.0 + (seg_idx % 40.0)
                                status = 2  # Jammed
                            elif 12.0 <= time_val <= 17.0:
                                idle = 110.0 + (seg_idx % 30.0)
                                status = 1  # Slow
                            else:
                                idle = 30.0 + (seg_idx % 15.0)
                                status = 0  # Clear
                        else:
                            if is_peak:
                                idle = 25.0 + (seg_idx % 20.0)
                                status = 1  # Slow
                            else:
                                idle = 5.0 + (seg_idx % 10.0)
                                status = 0  # Clear

                        X_train.append([seg_idx, dow, hour, minute, 1 if is_peak else 0])
                        y_idle.append(float(idle))
                        y_status.append(status)

        X_arr = np.array(X_train)
        self.regressor.fit(X_arr, np.array(y_idle))
        self.classifier.fit(X_arr, np.array(y_status))

    def predict_batch(self, edge_list: list, day_of_week: int, hour: int, minute: int):
        """Ultra-fast vectorized prediction for all edges simultaneously under 10ms."""
        time_val = hour + (minute / 60.0)
        is_peak = 1 if ((8.5 <= time_val <= 11.5) or (17.5 <= time_val <= 20.5)) and (day_of_week < 5) else 0

        feats = []
        for u, v in edge_list:
            seg_id = f"{u}->{v}"
            seg_idx = self.segment_map.get(seg_id, 0)
            feats.append([seg_idx, day_of_week, hour, minute, is_peak])

        X_test = np.array(feats)
        pred_idles = self.regressor.predict(X_test)
        pred_statuses = self.classifier.predict(X_test)

        status_map = {0: "Clear", 1: "Slow", 2: "Jammed"}
        results = {}
        for (u, v), idle, st in zip(edge_list, pred_idles, pred_statuses):
            results[(u, v)] = (max(0.0, round(float(idle), 1)), status_map.get(int(st), "Clear"))
        return results


# Global ML Engine Instance
traffic_ml = TrafficMLPredictor()


# ---------------------------------------------------------
# 3. MATHEMATICAL MODELING & CORE EQUATIONS
# ---------------------------------------------------------

# Base Emission Factors EF_v (g CO2 / km)
EMISSION_FACTORS = {
    "Electric Vehicle": 0.0,
    "EV": 0.0,
    "Diesel": 190.0,
    "Petrol": 150.0
}

# Standstill Idling Constant factor IF_v (g CO2 / sec)
IDLE_FACTORS = {
    "Electric Vehicle": 0.0,
    "EV": 0.0,
    "Diesel": 0.25,
    "Petrol": 0.25
}


def calculate_weight_multiplier(cargo_load_kg: float, max_capacity_kg: float) -> float:
    """W_m = Weight Multiplier = 1 + (Active Cargo Load / Max Capacity)"""
    if max_capacity_kg <= 0:
        return 1.0
    load_ratio = max(0.0, cargo_load_kg) / float(max_capacity_kg)
    return round(1.0 + load_ratio, 4)


def calculate_age_multiplier(vehicle_age_years: float) -> float:
    """A_m = Engine Age Penalty = 1 + (Vehicle Age * 0.02)"""
    return round(1.0 + (max(0.0, vehicle_age_years) * 0.02), 4)


def calculate_slope_factor(slope_percent: float) -> float:
    """
    S_i = Topography Slope Factor:
    - If segment incline slope > 5%, set to 1.8
    - If downhill (< -2%), set to 0.4
    - Otherwise 1.0
    """
    if slope_percent > 5.0:
        return 1.8
    elif slope_percent < -2.0:
        return 0.4
    else:
        return 1.0


def calculate_segment_carbon_cost(
    distance_km: float,
    vehicle_type: str,
    cargo_load_kg: float,
    max_capacity_kg: float,
    vehicle_age_years: float,
    slope_percent: float,
    idle_seconds: float
) -> dict:
    """
    Exact Multi-Variable Carbon Footprint per Segment Cost Equation:
    C_uv = (D_i * EF_v * W_m * A_m * S_i) + (T_idle * IF_v)
    """
    v_type = "Electric Vehicle" if "electric" in vehicle_type.lower() or vehicle_type.upper() == "EV" else (
        "Diesel" if "diesel" in vehicle_type.lower() else "Petrol"
    )

    EF_v = EMISSION_FACTORS.get(v_type, 150.0)
    IF_v = IDLE_FACTORS.get(v_type, 0.25)
    W_m = calculate_weight_multiplier(cargo_load_kg, max_capacity_kg)
    A_m = calculate_age_multiplier(vehicle_age_years)
    S_i = calculate_slope_factor(slope_percent)
    D_i = float(distance_km)
    T_idle = float(idle_seconds)

    motion_carbon = D_i * EF_v * W_m * A_m * S_i
    idle_carbon = T_idle * IF_v
    C_uv = motion_carbon + idle_carbon

    return {
        "D_i": D_i,
        "EF_v": EF_v,
        "W_m": W_m,
        "A_m": A_m,
        "S_i": S_i,
        "slope_percent": slope_percent,
        "T_idle": T_idle,
        "IF_v": IF_v,
        "motion_carbon_g": round(motion_carbon, 3),
        "idle_carbon_g": round(idle_carbon, 3),
        "C_uv": round(C_uv, 3)
    }


# ---------------------------------------------------------
# 4. NETWORKX GRAPH BUILDER & TOPOGRAPHY-AWARE A* ROUTER
# ---------------------------------------------------------

def build_nagpur_graph():
    """Initializes the internal NetworkX system representing Nagpur urban corridors."""
    G = nx.DiGraph()

    for node_id, data in NAGPUR_NODES.items():
        G.add_node(
            node_id,
            name=data["name"],
            lat=data["lat"],
            lon=data["lon"],
            elevation=data["elevation"],
            zone=data["zone"],
            description=data["description"]
        )

    for u, v, dist, slope, is_bn, road_name in ROAD_SEGMENTS:
        G.add_edge(
            u, v,
            distance_km=dist,
            slope_percent=slope,
            is_bottleneck=is_bn,
            road_name=road_name,
            segment_id=f"{u}->{v}"
        )

    return G


# Cached Graph instance
NAGPUR_GRAPH = build_nagpur_graph()


def solve_routes(
    pickup_node: str,
    delivery_node: str,
    vehicle_type: str,
    cargo_load_kg: float,
    max_capacity_kg: float,
    vehicle_age_years: float,
    dispatch_time_str: str = "09:30",
    day_of_week: int = 2  # Wednesday default
):
    """
    Computes BOTH:
    1. Baseline shortest-distance route (Standard route)
    2. Optimal green route using NetworkX A* with C_uv as the objective edge weight:
       P* = arg min_P sum_{e_uv in P} C_uv

    Returns route coordinates, segment-by-segment math proof breakdown, and symmetrical Delta CO2% comparison.
    """
    if pickup_node not in NAGPUR_GRAPH:
        raise ValueError(f"Pickup node '{pickup_node}' is not in the Nagpur road network.")
    if delivery_node not in NAGPUR_GRAPH:
        raise ValueError(f"Delivery node '{delivery_node}' is not in the Nagpur road network.")
    if pickup_node == delivery_node:
        raise ValueError("Pickup node and delivery destination cannot be the same location.")

    # Parse dispatch time
    try:
        if "T" in dispatch_time_str:
            dt = datetime.fromisoformat(dispatch_time_str.replace("Z", ""))
            hour, minute = dt.hour, dt.minute
            dow = dt.weekday()
        elif ":" in dispatch_time_str:
            parts = dispatch_time_str.split(":")
            hour, minute = int(parts[0]), int(parts[1])
            dow = day_of_week
        else:
            hour, minute = 9, 30
            dow = day_of_week
    except Exception:
        hour, minute = 9, 30
        dow = day_of_week

    # Vectorized batch prediction for ultra-fast response (<15ms)
    edge_pairs = list(NAGPUR_GRAPH.edges())
    traffic_predictions = traffic_ml.predict_batch(edge_pairs, dow, hour, minute)

    eval_graph = NAGPUR_GRAPH.copy()

    for u, v, data in eval_graph.edges(data=True):
        dist = data["distance_km"]
        slope = data["slope_percent"]
        t_idle, traffic_status = traffic_predictions[(u, v)]

        cost_dict = calculate_segment_carbon_cost(
            distance_km=dist,
            vehicle_type=vehicle_type,
            cargo_load_kg=cargo_load_kg,
            max_capacity_kg=max_capacity_kg,
            vehicle_age_years=vehicle_age_years,
            slope_percent=slope,
            idle_seconds=t_idle
        )

        data["carbon_cost"] = cost_dict["C_uv"]
        data["idle_seconds"] = t_idle
        data["traffic_status"] = traffic_status
        data["math_details"] = cost_dict

    # 1. BASELINE SHORTEST-DISTANCE ROUTE (Standard Navigation)
    try:
        standard_path = nx.shortest_path(eval_graph, source=pickup_node, target=delivery_node, weight="distance_km")
    except nx.NetworkXNoPath:
        raise ValueError(f"No valid navigable route between {pickup_node} and {delivery_node}")

    # 2. OPTIMAL GREEN ROUTE (Custom A* with C_uv Carbon Cost Objective Function)
    target_lat = NAGPUR_GRAPH.nodes[delivery_node]["lat"]
    target_lon = NAGPUR_GRAPH.nodes[delivery_node]["lon"]

    v_type_clean = "Electric Vehicle" if "electric" in vehicle_type.lower() or vehicle_type.upper() == "EV" else (
        "Diesel" if "diesel" in vehicle_type.lower() else "Petrol"
    )
    base_ef = EMISSION_FACTORS.get(v_type_clean, 150.0)

    def astar_heuristic(u, target):
        u_lat = NAGPUR_GRAPH.nodes[u]["lat"]
        u_lon = NAGPUR_GRAPH.nodes[u]["lon"]
        d = haversine_distance_km(u_lat, u_lon, target_lat, target_lon)
        return d * base_ef * 0.4

    try:
        green_path = nx.astar_path(
            eval_graph,
            source=pickup_node,
            target=delivery_node,
            heuristic=astar_heuristic,
            weight="carbon_cost"
        )
    except nx.NetworkXNoPath:
        green_path = standard_path

    # Extract detailed metrics for both routes
    def extract_route_metrics(path):
        segments = []
        total_dist = 0.0
        total_carbon = 0.0
        total_idle_sec = 0.0
        total_motion_carbon = 0.0
        total_idle_carbon = 0.0
        coords = []

        first_node = NAGPUR_GRAPH.nodes[path[0]]
        coords.append({"lat": first_node["lat"], "lon": first_node["lon"], "name": first_node["name"]})

        for i in range(len(path) - 1):
            u_node = path[i]
            v_node = path[i + 1]
            edge_data = eval_graph[u_node][v_node]
            math_info = edge_data["math_details"]

            seg_dist = edge_data["distance_km"]
            seg_carbon = edge_data["carbon_cost"]
            seg_idle = edge_data["idle_seconds"]
            status = edge_data["traffic_status"]
            road_name = edge_data["road_name"]

            total_dist += seg_dist
            total_carbon += seg_carbon
            total_idle_sec += seg_idle
            total_motion_carbon += math_info["motion_carbon_g"]
            total_idle_carbon += math_info["idle_carbon_g"]

            v_info = NAGPUR_GRAPH.nodes[v_node]
            coords.append({"lat": v_info["lat"], "lon": v_info["lon"], "name": v_info["name"]})

            segments.append({
                "from_id": u_node,
                "to_id": v_node,
                "from_name": NAGPUR_GRAPH.nodes[u_node]["name"],
                "to_name": NAGPUR_GRAPH.nodes[v_node]["name"],
                "road_name": road_name,
                "distance_km": seg_dist,
                "slope_percent": edge_data["slope_percent"],
                "traffic_status": status,
                "idle_seconds": seg_idle,
                "math_breakdown": math_info
            })

        cruise_time_min = (total_dist / 35.0) * 60.0
        duration_min = round(cruise_time_min + (total_idle_sec / 60.0), 1)

        return {
            "path_nodes": path,
            "coordinates": coords,
            "total_distance_km": round(total_dist, 2),
            "total_duration_min": duration_min,
            "total_idle_seconds": round(total_idle_sec, 1),
            "total_carbon_g": round(total_carbon, 2),
            "total_carbon_kg": round(total_carbon / 1000.0, 4),
            "motion_carbon_g": round(total_motion_carbon, 2),
            "idle_carbon_g": round(total_idle_carbon, 2),
            "segments": segments
        }

    std_metrics = extract_route_metrics(standard_path)
    green_metrics = extract_route_metrics(green_path)

    # Symmetrical Comparison Metric Equation:
    # Delta CO2% = ((Standard Route Carbon - Green Route Carbon) / Standard Route Carbon) * 100
    std_co2 = std_metrics["total_carbon_g"]
    grn_co2 = green_metrics["total_carbon_g"]

    if std_co2 > 0:
        delta_co2_pct = round(((std_co2 - grn_co2) / std_co2) * 100.0, 2)
    else:
        delta_co2_pct = 0.0

    co2_saved_g = max(0.0, round(std_co2 - grn_co2, 2))
    distance_diff_km = round(green_metrics["total_distance_km"] - std_metrics["total_distance_km"], 2)
    time_saved_min = round(std_metrics["total_duration_min"] - green_metrics["total_duration_min"], 1)

    w_m = calculate_weight_multiplier(cargo_load_kg, max_capacity_kg)
    a_m = calculate_age_multiplier(vehicle_age_years)
    ef_v = EMISSION_FACTORS.get(v_type_clean, 150.0)
    if_v = IDLE_FACTORS.get(v_type_clean, 0.25)

    return {
        "standard_route": std_metrics,
        "green_route": green_metrics,
        "comparison": {
            "delta_co2_percent": delta_co2_pct,
            "co2_saved_grams": co2_saved_g,
            "co2_saved_kg": round(co2_saved_g / 1000.0, 4),
            "distance_difference_km": distance_diff_km,
            "time_saved_minutes": time_saved_min,
            "is_optimal_identical": (standard_path == green_path)
        },
        "formula_constants": {
            "vehicle_type": v_type_clean,
            "EF_v": ef_v,
            "IF_v": if_v,
            "W_m": w_m,
            "A_m": a_m,
            "active_cargo_kg": cargo_load_kg,
            "max_capacity_kg": max_capacity_kg,
            "vehicle_age_years": vehicle_age_years,
            "formula_string": "C_uv = (D_i * EF_v * W_m * A_m * S_i) + (T_idle * IF_v)",
            "comparison_formula_string": "ΔCO2% = ((Standard Carbon - Green Carbon) / Standard Carbon) * 100"
        }
    }
