import time
from backend.routing import solve_routes

pairs = [
    ('mihan', 'sitabuldi'),
    ('wardhaman_nagar', 'sitabuldi'),
    ('mihan', 'wardhaman_nagar'),
    ('kamptee_road', 'sitabuldi'),
    ('vnit', 'wardhaman_nagar'),
    ('dharampeth', 'seminary_hills')
]

for p, d in pairs:
    t0 = time.perf_counter()
    res = solve_routes(p, d, 'Diesel', 600.0, 1200.0, 6.0, '09:30')
    ms = (time.perf_counter() - t0) * 1000
    std = res['standard_route']
    grn = res['green_route']
    cmp = res['comparison']
    print(f"\nRoute: {p} -> {d} ({ms:.2f} ms)")
    print(f"  Standard: {std['total_distance_km']} km | {std['total_carbon_g']} g | Idle: {std['total_idle_seconds']}s")
    print(f"  Green   : {grn['total_distance_km']} km | {grn['total_carbon_g']} g | Idle: {grn['total_idle_seconds']}s")
    print(f"  Savings : {cmp['delta_co2_percent']}% ({cmp['co2_saved_grams']} g)")
    print(f"  Std Path: {std['path_nodes']}")
    print(f"  Grn Path: {grn['path_nodes']}")
