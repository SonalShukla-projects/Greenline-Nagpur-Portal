from datetime import datetime, timedelta
from backend.database import SessionLocal, engine, Base
from backend.models import User, VehicleProfile, HistoricalTraffic, SavedRoute, DeliveryOrder
from backend.auth import get_password_hash
from backend.routing import ROAD_SEGMENTS


def seed_database(force_reseed: bool = False):
    """
    Mandatory autostart seeding function that checks if the database is empty
    and injects the mock data immediately on launch.
    """
    # Ensure all tables are created
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count > 0 and not force_reseed:
            # Check if delivery orders table needs sample data
            order_count = db.query(DeliveryOrder).count()
            if order_count == 0:
                customer_user = db.query(User).filter(User.username == "shraddha").first()
                driver_user = db.query(User).filter(User.username == "laxmikant").first()
                ev_veh = db.query(VehicleProfile).filter(VehicleProfile.registration_no == "MH-31-EV-2026").first()
                if customer_user:
                    sample_orders = [
                        DeliveryOrder(
                            customer_id=customer_user.id,
                            pickup_node="mihan",
                            pickup_address="MIHAN SEZ Gate 1, Nagpur",
                            delivery_node="sitabuldi",
                            delivery_address="Sitabuldi Metro Hub, Nagpur",
                            cargo_weight=350.0,
                            package_notes="Electronics cargo - Fragile",
                            status="PENDING",
                            created_at=datetime.utcnow() - timedelta(minutes=45)
                        ),
                        DeliveryOrder(
                            customer_id=customer_user.id,
                            pickup_node="wardhaman_nagar",
                            pickup_address="Wardhaman Nagar Market, Nagpur",
                            delivery_node="vnit",
                            delivery_address="VNIT Admin Gate, South Ambazari Rd",
                            cargo_weight=180.0,
                            package_notes="Educational supplies",
                            status="ASSIGNED",
                            driver_id=driver_user.id if driver_user else None,
                            vehicle_id=ev_veh.id if ev_veh else 1,
                            standard_co2=1450.0,
                            green_co2=980.0,
                            co2_saved_percent=32.4,
                            distance_km=8.2,
                            duration_min=21.0,
                            created_at=datetime.utcnow() - timedelta(hours=2),
                            assigned_at=datetime.utcnow() - timedelta(hours=1)
                        )
                    ]
                    db.add_all(sample_orders)
                    db.commit()
                    print(f"[SEED] Injected {len(sample_orders)} sample customer delivery orders.")
            print("[SEED] Database already contains data. Skipping full seeding.")
            return

        print("[SEED] Initializing Greenline Nagpur database seeding...")

        # 1. Seed Users
        # Default password for all seeded users: greenline123
        default_pwd_hash = get_password_hash("greenline123")

        mock_users = [
            User(
                name="Sonal Shukla",
                username="sonal",
                password_hash=default_pwd_hash,
                role="Administrator"
            ),
            User(
                name="Bhavana Bambal",
                username="bhavana",
                password_hash=default_pwd_hash,
                role="Administrator"
            ),
            User(
                name="Laxmikant Rakhade",
                username="laxmikant",
                password_hash=default_pwd_hash,
                role="Dispatch Driver"
            ),
            User(
                name="Vedant Sangrame",
                username="vedant",
                password_hash=default_pwd_hash,
                role="Dispatch Driver"
            ),
            User(
                name="Shraddha Hiware",
                username="shraddha",
                password_hash=default_pwd_hash,
                role="Customer"
            ),
        ]
        db.add_all(mock_users)
        db.commit()
        print(f"[SEED] Injected {len(mock_users)} core users.")

        # 2. Seed Vehicle Profiles
        mock_vehicles = [
            VehicleProfile(
                vehicle_type="Electric Vehicle",
                age=0.0,
                max_capacity=500.0,
                registration_no="MH-31-EV-2026"
            ),
            VehicleProfile(
                vehicle_type="Diesel",
                age=6.0,
                max_capacity=1200.0,
                registration_no="MH-31-DV-4512"
            ),
            VehicleProfile(
                vehicle_type="Petrol",
                age=3.0,
                max_capacity=300.0,
                registration_no="MH-31-PV-9876"
            )
        ]
        db.add_all(mock_vehicles)
        db.commit()
        print(f"[SEED] Injected {len(mock_vehicles)} vehicle profiles.")

        # 3. Seed Sample Historical Traffic Data
        historical_entries = []
        for u, v, dist, slope, is_bn, road_name in ROAD_SEGMENTS:
            seg_id = f"{u}->{v}"
            # Peak morning
            historical_entries.append(HistoricalTraffic(
                segment_id=seg_id,
                day_of_week=2,  # Wednesday
                time_of_day="09:30",
                traffic_status="Jammed" if is_bn else "Clear",
                idle_seconds=240.0 if is_bn else 25.0
            ))
            # Afternoon off-peak
            historical_entries.append(HistoricalTraffic(
                segment_id=seg_id,
                day_of_week=2,
                time_of_day="14:00",
                traffic_status="Slow" if is_bn else "Clear",
                idle_seconds=80.0 if is_bn else 10.0
            ))
        db.add_all(historical_entries)
        db.commit()
        print(f"[SEED] Injected {len(historical_entries)} historical traffic baseline logs.")

        # 4. Seed Initial Saved Routes for Live Dashboard Aggregation
        driver_user = db.query(User).filter(User.username == "laxmikant").first()
        diesel_veh = db.query(VehicleProfile).filter(VehicleProfile.registration_no == "MH-31-DV-4512").first()
        ev_veh = db.query(VehicleProfile).filter(VehicleProfile.registration_no == "MH-31-EV-2026").first()

        sample_saved_routes = [
            SavedRoute(
                user_id=driver_user.id if driver_user else 1,
                pickup_node="mihan",
                delivery_node="sitabuldi",
                vehicle_id=diesel_veh.id if diesel_veh else 2,
                cargo_weight=650.0,
                standard_co2=3942.5,
                green_co2=2680.1,
                co2_saved_percent=32.02,
                distance_km=9.8,
                duration_min=24.5,
                created_at=datetime.utcnow() - timedelta(hours=3)
            ),
            SavedRoute(
                user_id=driver_user.id if driver_user else 1,
                pickup_node="wardhaman_nagar",
                delivery_node="kamptee_road",
                vehicle_id=diesel_veh.id if diesel_veh else 2,
                cargo_weight=800.0,
                standard_co2=2850.0,
                green_co2=1980.4,
                co2_saved_percent=30.51,
                distance_km=7.4,
                duration_min=19.2,
                created_at=datetime.utcnow() - timedelta(hours=6)
            ),
            SavedRoute(
                user_id=driver_user.id if driver_user else 1,
                pickup_node="mihan",
                delivery_node="wardhaman_nagar",
                vehicle_id=diesel_veh.id if diesel_veh else 2,
                cargo_weight=500.0,
                standard_co2=5120.0,
                green_co2=3580.0,
                co2_saved_percent=30.08,
                distance_km=14.2,
                duration_min=32.0,
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            SavedRoute(
                user_id=driver_user.id if driver_user else 1,
                pickup_node="vnit",
                delivery_node="kamptee_road",
                vehicle_id=ev_veh.id if ev_veh else 1,
                cargo_weight=200.0,
                standard_co2=0.0,
                green_co2=0.0,
                co2_saved_percent=0.0,
                distance_km=11.2,
                duration_min=26.0,
                created_at=datetime.utcnow() - timedelta(days=2)
            )
        ]
        db.add_all(sample_saved_routes)
        db.commit()
        print(f"[SEED] Injected {len(sample_saved_routes)} sample saved routes for dashboard analytics.")

        # 5. Seed Initial Delivery Orders
        customer_user = db.query(User).filter(User.username == "shraddha").first()
        if customer_user:
            sample_orders = [
                DeliveryOrder(
                    customer_id=customer_user.id,
                    pickup_node="mihan",
                    pickup_address="MIHAN SEZ Gate 1, Nagpur",
                    delivery_node="sitabuldi",
                    delivery_address="Sitabuldi Metro Hub, Nagpur",
                    cargo_weight=350.0,
                    package_notes="Electronics cargo - Fragile",
                    status="PENDING",
                    created_at=datetime.utcnow() - timedelta(minutes=45)
                ),
                DeliveryOrder(
                    customer_id=customer_user.id,
                    pickup_node="wardhaman_nagar",
                    pickup_address="Wardhaman Nagar Market, Nagpur",
                    delivery_node="vnit",
                    delivery_address="VNIT Admin Gate, South Ambazari Rd",
                    cargo_weight=180.0,
                    package_notes="Educational supplies",
                    status="ASSIGNED",
                    driver_id=driver_user.id if driver_user else None,
                    vehicle_id=ev_veh.id if ev_veh else 1,
                    standard_co2=1450.0,
                    green_co2=980.0,
                    co2_saved_percent=32.4,
                    distance_km=8.2,
                    duration_min=21.0,
                    created_at=datetime.utcnow() - timedelta(hours=2),
                    assigned_at=datetime.utcnow() - timedelta(hours=1)
                )
            ]
            db.add_all(sample_orders)
            db.commit()
            print(f"[SEED] Injected {len(sample_orders)} sample customer delivery orders.")

        print("[SEED] Auto-seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Error while seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(force_reseed=True)

