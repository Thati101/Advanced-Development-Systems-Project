from database import Base, engine, SessionLocal
from models import User, Bus, Booking
import services

# Global variable to store current logged-in user
current_user = None

def get_db():
    """Create a database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, let the caller handle it

def setup_database():
    """Create all tables and add sample data"""
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    try:
        # Add some sample buses if they don't exist
        existing_buses = services.get_all_buses(db)
        if existing_buses["success"] and len(existing_buses["buses"]) == 0:
            services.add_bus(db, "Express 101", "New York → Boston", "08:00 AM", 30)
            services.add_bus(db, "Comfort 202", "Boston → Philadelphia", "02:00 PM", 25)
            services.add_bus(db, "Luxury 303", "Philadelphia → Washington DC", "06:00 PM", 20)
            services.add_bus(db, "Economy 404", "Washington DC → Miami", "10:00 PM", 40)
            print("✅ Sample buses added!")
    finally:
        db.close()
    
    print("✅ Database initialized!\n")

def print_header():
    print("\n" + "=" * 50)
    print("🚍 WELCOME TO BUS BOOKING SYSTEM")
    print("=" * 50)

def print_menu():
    if current_user:
        print(f"\n👋 Welcome back, {current_user['name']}!")
        print("\n📋 MAIN MENU:")
        print("1. View Available Buses")
        print("2. Book a Seat")
        print("3. My Bookings")
        print("4. Cancel Booking")
        print("5. Logout")
        print("6. Exit")
    else:
        print("\n📋 MAIN MENU:")
        print("1. Register")
        print("2. Login")
        print("3. View Available Buses (Guest)")
        print("4. Exit")

def register_flow():
    print("\n📝 USER REGISTRATION")
    print("-" * 20)
    name = input("Enter your full name: ")
    email = input("Enter your email: ")
    password = input("Enter password: ")
    
    db = SessionLocal()
    try:
        result = services.register_user(db, name, email, password)
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    finally:
        db.close()

def login_flow():
    global current_user
    print("\n🔐 USER LOGIN")
    print("-" * 15)
    email = input("Enter your email: ")
    password = input("Enter password: ")
    
    db = SessionLocal()
    try:
        result = services.login_user(db, email, password)
        if result["success"]:
            current_user = {
                "user_id": result["user_id"],
                "name": result["message"].replace("Welcome ", "").replace("!", "")
            }
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    finally:
        db.close()

def view_buses():
    print("\n🚌 AVAILABLE BUSES")
    print("-" * 40)
    
    db = SessionLocal()
    try:
        result = services.get_all_buses(db)
        
        if result["success"]:
            if not result["buses"]:
                print("No buses available.")
                return
                
            print(f"{'ID':<3} {'Bus Name':<12} {'Route':<25} {'Departure':<10} {'Available':<10}")
            print("-" * 70)
            
            for bus in result["buses"]:
                print(f"{bus['bus_id']:<3} {bus['bus_name']:<12} {bus['route']:<25} {bus['departure_time']:<10} {bus['available_seats']}/{bus['capacity']}")
        else:
            print(f"❌ {result['message']}")
    finally:
        db.close()

def book_seat_flow():
    if not current_user:
        print("❌ Please login first!")
        return
    
    print("\n🎫 BOOK A SEAT")
    print("-" * 15)
    
    # Show available buses first
    view_buses()
    
    try:
        bus_id = int(input("\nEnter Bus ID to book: "))
        
        db = SessionLocal()
        try:
            result = services.book_seat(db, current_user["user_id"], bus_id)
            
            if result["success"]:
                print(f"✅ {result['message']}")
                print(f"🎫 Booking Details:")
                print(f"   Booking ID: {result['booking_id']}")
                print(f"   Seat Number: {result['seat_no']}")
                print(f"   Bus: {result['bus_name']}")
                print(f"   Route: {result['route']}")
            else:
                print(f"❌ {result['message']}")
        finally:
            db.close()
    except ValueError:
        print("❌ Please enter a valid Bus ID number!")

def view_my_bookings():
    if not current_user:
        print("❌ Please login first!")
        return
    
    print(f"\n📋 {current_user['name']}'s BOOKINGS")
    print("-" * 30)
    
    db = SessionLocal()
    try:
        result = services.get_user_bookings(db, current_user["user_id"])
        
        if result["success"]:
            if not result["bookings"]:
                print("You have no bookings yet.")
                return
                
            print(f"{'ID':<5} {'Bus':<12} {'Route':<25} {'Seat':<5} {'Status':<10} {'Date':<15}")
            print("-" * 80)
            
            for booking in result["bookings"]:
                print(f"{booking['booking_id']:<5} {booking['bus_name']:<12} {booking['route']:<25} {booking['seat_no']:<5} {booking['status']:<10} {booking['created_at']:<15}")
        else:
            print(f"❌ {result['message']}")
    finally:
        db.close()

def cancel_booking_flow():
    if not current_user:
        print("❌ Please login first!")
        return
    
    print("\n❌ CANCEL BOOKING")
    print("-" * 18)
    
    # Show user's bookings first
    view_my_bookings()
    
    try:
        booking_id = int(input("\nEnter Booking ID to cancel: "))
        
        db = SessionLocal()
        try:
            result = services.cancel_booking(db, booking_id, current_user["user_id"])
            
            if result["success"]:
                print(f"✅ {result['message']}")
            else:
                print(f"❌ {result['message']}")
        finally:
            db.close()
    except ValueError:
        print("❌ Please enter a valid Booking ID number!")

def logout():
    global current_user
    if current_user:
        print(f"👋 Goodbye, {current_user['name']}!")
        current_user = None
    else:
        print("❌ You are not logged in!")

def main():
    print_header()
    setup_database()
    
    while True:
        print_menu()
        
        try:
            choice = input("\n👉 Enter your choice: ")
            
            if current_user:
                # Logged-in user menu
                if choice == "1":
                    view_buses()
                elif choice == "2":
                    book_seat_flow()
                elif choice == "3":
                    view_my_bookings()
                elif choice == "4":
                    cancel_booking_flow()
                elif choice == "5":
                    logout()
                elif choice == "6":
                    print("👋 Thank you for using Bus Booking System!")
                    break
                else:
                    print("❌ Invalid choice! Please try again.")
            else:
                # Guest menu
                if choice == "1":
                    register_flow()
                elif choice == "2":
                    login_flow()
                elif choice == "3":
                    view_buses()
                elif choice == "4":
                    print("👋 Thank you for using Bus Booking System!")
                    break
                else:
                    print("❌ Invalid choice! Please try again.")
            
            # Pause before showing menu again
            input("\n⏸️  Press Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Thank you for using Bus Booking System!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
