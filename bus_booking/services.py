from sqlalchemy.orm import Session
from models import User, Bus, Booking
from database import SessionLocal
from datetime import datetime

# ==========================================
# DATABASE SESSION HELPER
# ==========================================
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# USER MANAGEMENT
# ==========================================

def register_user(db: Session, name: str, email: str, password: str):
    """Register a new user"""
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {"success": False, "message": "Email already registered"}
        
        # Create new user
        new_user = User(name=name, email=email, password=password)  # Note: In production, hash the password
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"success": True, "message": f"User  {name} registered successfully!", "user_id": new_user.user_id}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}

def login_user(db: Session, email: str, password: str):
    """Login user"""
    try:
        user = db.query(User).filter(User.email == email, User.password == password).first()
        if user:
            return {"success": True, "message": f"Welcome {user.name}!", "user_id": user.user_id}
        else:
            return {"success": False, "message": "Invalid email or password"}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# ==========================================
# BUS MANAGEMENT
# ==========================================

def add_bus(db: Session, bus_name: str, route: str, departure_time: str, capacity: int):
    """Add a new bus"""
    try:
        new_bus = Bus(bus_name=bus_name, route=route, departure_time=departure_time, capacity=capacity)
        db.add(new_bus)
        db.commit()
        db.refresh(new_bus)
        
        return {"success": True, "message": f"Bus {bus_name} added successfully!", "bus_id": new_bus.bus_id}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}

def get_all_buses(db: Session):
    """Get all available buses"""
    try:
        buses = db.query(Bus).all()
        bus_list = []
        
        for bus in buses:
            # Count booked seats
            booked_seats = db.query(Booking).filter(Booking.bus_id == bus.bus_id, Booking.status == "booked").count()
            available_seats = bus.capacity - booked_seats
            
            bus_list.append({
                "bus_id": bus.bus_id,
                "bus_name": bus.bus_name,
                "route": bus.route,
                "departure_time": bus.departure_time,
                "capacity": bus.capacity,
                "available_seats": available_seats,
                "booked_seats": booked_seats
            })
        
        return {"success": True, "buses": bus_list}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# ==========================================
# BOOKING MANAGEMENT
# ==========================================

def book_seat(db: Session, user_id: int, bus_id: int):
    """Book a seat on a bus"""
    try:
        # Check if bus exists
        bus = db.query(Bus).filter(Bus.bus_id == bus_id).first()
        if not bus:
            return {"success": False, "message": "Bus not found"}
        
        # Check available seats
        booked_seats = db.query(Booking).filter(Booking.bus_id == bus_id, Booking.status == "booked").count()
        if booked_seats >= bus.capacity:
            return {"success": False, "message": "No seats available"}
        
        # Find next available seat number
        taken_seats = db.query(Booking.seat_no).filter(Booking.bus_id == bus_id, Booking.status == "booked").all()
        taken_seat_numbers = [seat[0] for seat in taken_seats]
        
        # Assign next available seat
        seat_no = 1
        while seat_no in taken_seat_numbers:
            seat_no += 1
        
        # Create booking
        new_booking = Booking(user_id=user_id, bus_id=bus_id, seat_no=seat_no, status="booked")
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        
        return {
            "success": True, 
            "message": f"Seat {seat_no} booked successfully on {bus.bus_name}!", 
            "booking_id": new_booking.booking_id,
            "seat_no": seat_no,
            "bus_name": bus.bus_name,
            "route": bus.route
        }
    
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}

def cancel_booking(db: Session, booking_id: int, user_id: int):
    """Cancel a booking"""
    try:
        # Find the booking
        booking = db.query(Booking).filter(Booking.booking_id == booking_id, Booking.user_id == user_id).first()
        if not booking:
            return {"success": False, "message": "Booking not found"}
        
        if booking.status == "cancelled":
            return {"success": False, "message": "Booking already cancelled"}
        
        # Cancel booking
        booking.status = "cancelled"
        db.commit()
        
        return {"success": True, "message": f"Booking {booking_id} cancelled successfully"}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error: {str(e)}"}

def get_user_bookings(db: Session, user_id: int):
    """Get all bookings for a user"""
    try:
        bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
        booking_list = []
        
        for booking in bookings:
            bus = db.query(Bus).filter(Bus.bus_id == booking.bus_id).first()
            booking_list.append({
                "booking_id": booking.booking_id,
                "bus_name": bus.bus_name if bus else "Unknown",
                "route": bus.route if bus else "Unknown",
                "departure_time": bus.departure_time if bus else "Unknown",
                "seat_no": booking.seat_no,
                "status": booking.status,
                "created_at": booking.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {"success": True, "bookings": booking_list}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def get_bus_details(db: Session, bus_id: int):
    """Get detailed info about a specific bus"""
    try:
        bus = db.query(Bus).filter(Bus.bus_id == bus_id).first()
        if not bus:
            return {"success": False, "message": "Bus not found"}
        
        # Get all bookings for this bus
        bookings = db.query(Booking).filter(Booking.bus_id == bus_id, Booking.status == "booked").all()
        booked_seats = [booking.seat_no for booking in bookings]
        
        return {
            "success": True,
            "bus": {
                "bus_id": bus.bus_id,
                "bus_name": bus.bus_name,
                "route": bus.route,
                "departure_time": bus.departure_time,
                "capacity": bus.capacity,
                "booked_seats": sorted(booked_seats),
                "available_seats": bus.capacity - len(booked_seats)
            }
        }
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
