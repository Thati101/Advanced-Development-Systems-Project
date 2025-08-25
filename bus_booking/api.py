from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import services
from models import User, Bus, Booking
from database import SessionLocal

# Initialize FastAPI app
app = FastAPI(
    title="Bus Booking System API",
    description="A complete bus booking system with user management and seat reservations",
    version="1.0.0"
)

# ==========================================
# DATABASE DEPENDENCY
# ==========================================
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# PYDANTIC MODELS (Request/Response schemas)
# ==========================================

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True

class BusCreate(BaseModel):
    bus_name: str
    route: str
    departure_time: str
    capacity: int

class BusResponse(BaseModel):
    bus_id: int
    bus_name: str
    route: str
    departure_time: str
    capacity: int
    available_seats: int
    booked_seats: int
    
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    user_id: int
    bus_id: int

class BookingResponse(BaseModel):
    booking_id: int
    bus_name: str
    route: str
    departure_time: str
    seat_no: int
    status: str
    created_at: str
    
    class Config:
        from_attributes = True

class BookingCancel(BaseModel):
    booking_id: int
    user_id: int

# ==========================================
# USER ENDPOINTS
# ==========================================

@app.post("/api/users/register", response_model=dict, tags=["Users"])
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        result = services.register_user(db, user_data.name, user_data.email, user_data.password)
        if result["success"]:
            return {"success": True, "message": result["message"], "user_id": result["user_id"]}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/login", response_model=dict, tags=["Users"])
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    try:
        result = services.login_user(db, login_data.email, login_data.password)
        if result["success"]:
            # Get full user details
            user = db.query(User).filter(User.email == login_data.email).first()
            return {
                "success": True, 
                "message": result["message"], 
                "user": {
                    "user_id": user.user_id,
                    "name": user.name,
                    "email": user.email
                }
            }
        else:
            raise HTTPException(status_code=401, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            return UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email
            )
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# BUS ENDPOINTS
# ==========================================

@app.post("/api/buses", response_model=dict, tags=["Buses"])
async def add_bus(bus_data: BusCreate, db: Session = Depends(get_db)):
    """Add a new bus"""
    try:
        result = services.add_bus(
            db,
            bus_data.bus_name, 
            bus_data.route, 
            bus_data.departure_time, 
            bus_data.capacity
        )
        if result["success"]:
            return {"success": True, "message": result["message"], "bus_id": result["bus_id"]}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/buses", response_model=List[BusResponse], tags=["Buses"])
async def get_all_buses(db: Session = Depends(get_db)):
    """Get all available buses with seat availability"""
    try:
        result = services.get_all_buses(db)
        if result["success"]:
            bus_list = []
            for bus_data in result["buses"]:
                bus_list.append(BusResponse(
                    bus_id=bus_data["bus_id"],
                    bus_name=bus_data["bus_name"],
                    route=bus_data["route"],
                    departure_time=bus_data["departure_time"],
                    capacity=bus_data["capacity"],
                    available_seats=bus_data["available_seats"],
                    booked_seats=bus_data["booked_seats"]
                ))
            return bus_list
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/buses/{bus_id}", response_model=dict, tags=["Buses"])
async def get_bus(bus_id: int, db: Session = Depends(get_db)):
    """Get specific bus details"""
    try:
        result = services.get_bus_details(db, bus_id)
        if result["success"]:
            return {
                "success": True,
                "bus": result["bus"]
            }
        else:
            raise HTTPException(status_code=404, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/buses/{bus_id}/seats", response_model=dict, tags=["Buses"])
async def get_bus_seat_details(bus_id: int, db: Session = Depends(get_db)):
    """Get detailed seat information for a specific bus"""
    try:
        result = services.get_bus_details(db, bus_id)
        if result["success"]:
            bus_info = result["bus"]
            return {
                "success": True,
                "bus_id": bus_info["bus_id"],
                "bus_name": bus_info["bus_name"],
                "route": bus_info["route"],
                "departure_time": bus_info["departure_time"],
                "capacity": bus_info["capacity"],
                "available_seats": bus_info["available_seats"],
                "booked_seats": bus_info["booked_seats"]
            }
        else:
            raise HTTPException(status_code=404, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# BOOKING ENDPOINTS
# ==========================================

@app.post("/api/bookings", response_model=dict, tags=["Bookings"])
async def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    """Book a seat on a bus"""
    try:
        result = services.book_seat(db, booking_data.user_id, booking_data.bus_id)
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "booking": {
                    "booking_id": result["booking_id"],
                    "seat_no": result["seat_no"],
                    "bus_name": result["bus_name"],
                    "route": result["route"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookings/user/{user_id}", response_model=List[BookingResponse], tags=["Bookings"])
async def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    """Get booking history for a specific user"""
    try:
        result = services.get_user_bookings(db, user_id)
        if result["success"]:
            booking_list = []
            for booking_data in result["bookings"]:
                booking_list.append(BookingResponse(
                    booking_id=booking_data["booking_id"],
                    bus_name=booking_data["bus_name"],
                    route=booking_data["route"],
                    departure_time=booking_data["departure_time"],
                    seat_no=booking_data["seat_no"],
                    status=booking_data["status"],
                    created_at=booking_data["created_at"]
                ))
            return booking_list
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookings/{booking_id}", response_model=dict, tags=["Bookings"])
async def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Get specific booking details"""
    try:
        booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if booking:
            user = db.query(User).filter(User.user_id == booking.user_id).first()
            bus = db.query(Bus).filter(Bus.bus_id == booking.bus_id).first()
            
            return {
                "success": True,
                "booking": {
                    "booking_id": booking.booking_id,
                    "user_id": booking.user_id,
                    "bus_id": booking.bus_id,
                    "seat_no": booking.seat_no,
                    "status": booking.status,
                    "created_at": str(booking.created_at),
                    "user_name": user.name if user else "Unknown",
                    "bus_name": bus.bus_name if bus else "Unknown",
                    "route": bus.route if bus else "Unknown"
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Booking not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bookings", response_model=dict, tags=["Bookings"])
async def cancel_booking(cancel_data: BookingCancel, db: Session = Depends(get_db)):
    """Cancel a booking"""
    try:
        result = services.cancel_booking(db, cancel_data.booking_id, cancel_data.user_id)
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# HEALTH CHECK & ROOT
# ==========================================

@app.get("/", tags=["Root"])
async def root():
    """API Root - Welcome message"""
    return {
        "message": "Welcome to Bus Booking System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Bus Booking API is running",
        "timestamp": str(services.datetime.utcnow())
    }

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Bus Booking API Server...")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("📖 ReDoc Documentation: http://127.0.0.1:8000/redoc")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
