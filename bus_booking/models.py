from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # (later: hash this)

    bookings = relationship("Booking", back_populates="user")

class Bus(Base):
    __tablename__ = "buses"
    bus_id = Column(Integer, primary_key=True, index=True)
    bus_name = Column(String, nullable=False)
    route = Column(String, nullable=False)
    departure_time = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)

    bookings = relationship("Booking", back_populates="bus")

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    bus_id = Column(Integer, ForeignKey("buses.bus_id"))
    seat_no = Column(Integer, nullable=False)
    status = Column(String, default="booked")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    bus = relationship("Bus", back_populates="bookings")
