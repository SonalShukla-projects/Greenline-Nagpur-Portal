from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # Administrator, Dispatch Driver, Customer

    routes = relationship("SavedRoute", back_populates="user")
    orders_created = relationship("DeliveryOrder", foreign_keys="DeliveryOrder.customer_id", back_populates="customer")
    orders_assigned = relationship("DeliveryOrder", foreign_keys="DeliveryOrder.driver_id", back_populates="driver")


class VehicleProfile(Base):
    __tablename__ = "vehicle_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_type = Column(String(50), nullable=False)  # Electric Vehicle, Diesel, Petrol
    age = Column(Float, nullable=False, default=0.0)    # in years
    max_capacity = Column(Float, nullable=False)       # in kg
    registration_no = Column(String(50), unique=True, index=True, nullable=False)

    routes = relationship("SavedRoute", back_populates="vehicle")
    orders = relationship("DeliveryOrder", back_populates="vehicle")


class HistoricalTraffic(Base):
    __tablename__ = "historical_traffic"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    segment_id = Column(String(100), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    time_of_day = Column(String(10), nullable=False)  # e.g., "09:30"
    traffic_status = Column(String(20), nullable=False)  # Clear, Slow, Jammed
    idle_seconds = Column(Float, nullable=False, default=0.0)


class SavedRoute(Base):
    __tablename__ = "saved_routes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pickup_node = Column(String(100), nullable=False)
    delivery_node = Column(String(100), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle_profiles.id"), nullable=True)
    cargo_weight = Column(Float, nullable=False)
    standard_co2 = Column(Float, nullable=False)
    green_co2 = Column(Float, nullable=False)
    co2_saved_percent = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_min = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="routes")
    vehicle = relationship("VehicleProfile", back_populates="routes")


class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pickup_node = Column(String(100), nullable=False)
    pickup_address = Column(String(255), nullable=True)
    delivery_node = Column(String(100), nullable=False)
    delivery_address = Column(String(255), nullable=True)
    cargo_weight = Column(Float, nullable=False, default=10.0)
    package_notes = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, ASSIGNED, IN_TRANSIT, DELIVERED, CANCELLED

    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_profiles.id"), nullable=True)

    standard_co2 = Column(Float, nullable=True)
    green_co2 = Column(Float, nullable=True)
    co2_saved_percent = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    duration_min = Column(Float, nullable=True)
    route_coords = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    customer = relationship("User", foreign_keys=[customer_id], back_populates="orders_created")
    driver = relationship("User", foreign_keys=[driver_id], back_populates="orders_assigned")
    vehicle = relationship("VehicleProfile", back_populates="orders")

