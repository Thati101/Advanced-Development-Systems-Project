from database import Base, engine
from models import User, Bus, Booking
import services

def setup_database():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database and tables created!\n")

def test_system():
    """Test all core functions"""
    print("🚍 TESTING BUS BOOKING SYSTEM")
    print("=" * 40)
    
    # 1. REGISTER USERS
    print("\n1. REGISTERING USERS...")
    user1 = services.register_user("Alice Johnson", "alice@email.com", "password123")
    user2 = services.register_user("Bob Smith", "bob@email.com", "password456")
    print(f"User 1: {user1}")
    print(f"User 2: {user2}")
    
    # Try duplicate email
    duplicate = services.register_user("Charlie Brown", "alice@email.com", "password789")
    print(f"Duplicate email test: {duplicate}")
    
    # 2. LOGIN USERS
    print("\n2. TESTING LOGIN...")
    login1 = services.login_user("alice@email.com", "password123")
    login2 = services.login_user("bob@email.com", "wrong_password")
    print(f"Alice login: {login1}")
    print(f"Bob wrong password: {login2}")
    
    # 3. ADD BUSES
    print("\n3. ADDING BUSES...")
    bus1 = services.add_bus("Express 101", "New York → Boston", "08:00 AM", 30)
    bus2 = services.add_bus("Comfort 202", "Boston → Philadelphia", "02:00 PM", 25)
    bus3 = services.add_bus("Luxury 303", "Philadelphia → Washington DC", "06:00 PM", 20)
    print(f"Bus 1: {bus1}")
    print(f"Bus 2: {bus2}")
    print(f"Bus 3: {bus3}")
    
    # 4. VIEW ALL BUSES
    print("\n4. VIEWING ALL BUSES...")
    all_buses = services.get_all_buses()
    if all_buses["success"]:
        for bus in all_buses["buses"]:
            print(f"🚌 {bus['bus_name']} | Route: {bus['route']} | Departure: {bus['departure_time']} | Available: {bus['available_seats']}/{bus['capacity']}")
    
    # 5. BOOK SEATS
    print("\n5. BOOKING SEATS...")
    # Alice books on bus 1
    booking1 = services.book_seat(user1["user_id"], bus1["bus_id"])
    print(f"Alice booking: {booking1}")
    
    # Bob books on same bus
    booking2 = services.book_seat(user2["user_id"], bus1["bus_id"])
    print(f"Bob booking: {booking2}")
    
    # Alice books another seat on bus 2
    booking3 = services.book_seat(user1["user_id"], bus2["bus_id"])
    print(f"Alice second booking: {booking3}")
    
    # 6. VIEW UPDATED BUSES
    print("\n6. BUSES AFTER BOOKINGS...")
    all_buses = services.get_all_buses()
    if all_buses["success"]:
        for bus in all_buses["buses"]:
            print(f"🚌 {bus['bus_name']} | Available: {bus['available_seats']}/{bus['capacity']} | Booked: {bus['booked_seats']}")
    
    # 7. VIEW USER BOOKINGS
    print("\n7. USER BOOKING HISTORY...")
    alice_bookings = services.get_user_bookings(user1["user_id"])
    print(f"Alice's bookings:")
    if alice_bookings["success"]:
        for booking in alice_bookings["bookings"]:
            print(f"  🎫 {booking['bus_name']} | Seat {booking['seat_no']} | Status: {booking['status']} | Route: {booking['route']}")
    
    # 8. CANCEL BOOKING
    print("\n8. CANCELLING BOOKING...")
    if booking1["success"]:
        cancel_result = services.cancel_booking(booking1["booking_id"], user1["user_id"])
        print(f"Cancel result: {cancel_result}")
        
        # Check Alice's bookings again
        alice_bookings = services.get_user_bookings(user1["user_id"])
        print(f"Alice's bookings after cancellation:")
        if alice_bookings["success"]:
            for booking in alice_bookings["bookings"]:
                print(f"  🎫 {booking['bus_name']} | Seat {booking['seat_no']} | Status: {booking['status']}")
    
    # 9. BUS DETAILS
    print("\n9. DETAILED BUS INFO...")
    bus_details = services.get_bus_details(bus1["bus_id"])
    if bus_details["success"]:
        bus = bus_details["bus"]
        print(f"🚌 {bus['bus_name']}")
        print(f"   Route: {bus['route']}")
        print(f"   Departure: {bus['departure_time']}")
        print(f"   Capacity: {bus['capacity']}")
        print(f"   Available: {bus['available_seats']}")
        print(f"   Booked seats: {bus['booked_seats']}")
    
    print("\n🎉 ALL TESTS COMPLETED!")

if __name__ == "__main__":
    # Setup database
    setup_database()
    
    # Run tests
    test_system()
