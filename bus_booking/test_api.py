import requests
import json

# Base URL for your API
BASE_URL = "http://127.0.0.1:8000"

def test_api():
    """Test all API endpoints"""
    print("🧪 Testing Bus Booking API\n")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1️⃣ Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Test 2: Register User
    print("2️⃣ Testing User Registration...")
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/users/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        user_id = response.json().get("user_id")
        print(f"✅ User registered with ID: {user_id}")
    print()
    
    # Test 3: Register Another User
    print("3️⃣ Testing Second User Registration...")
    user2_data = {
        "name": "Jane Smith",
        "email": "jane@example.com", 
        "password": "password456"
    }
    response = requests.post(f"{BASE_URL}/api/users/register", json=user2_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        user2_id = response.json().get("user_id")
        print(f"✅ Second user registered with ID: {user2_id}")
    print()
    
    # Test 4: Login User
    print("4️⃣ Testing User Login...")
    login_data = {
        "email": "john@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/users/login", json=login_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Test 5: Add Bus
    print("5️⃣ Testing Add Bus...")
    bus_data = {
        "bus_name": "Express 101",
        "route": "New York to Boston",
        "departure_time": "08:00 AM",
        "capacity": 50
    }
    response = requests.post(f"{BASE_URL}/api/buses", json=bus_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        bus_id = response.json().get("bus_id")
        print(f"✅ Bus added with ID: {bus_id}")
    print()
    
    # Test 6: Add Another Bus
    print("6️⃣ Testing Add Second Bus...")
    bus2_data = {
        "bus_name": "Comfort 202",
        "route": "Boston to Washington DC",
        "departure_time": "02:00 PM",
        "capacity": 40
    }
    response = requests.post(f"{BASE_URL}/api/buses", json=bus2_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        bus2_id = response.json().get("bus_id")
        print(f"✅ Second bus added with ID: {bus2_id}")
    print()
    
    # Test 7: Get All Buses
    print("7️⃣ Testing Get All Buses...")
    response = requests.get(f"{BASE_URL}/api/buses")
    print(f"Status: {response.status_code}")
    buses = response.json()
    print(f"Found {len(buses)} buses:")
    for bus in buses:
        print(f"  - {bus['bus_name']}: {bus['route']} ({bus['available_seats']}/{bus['capacity']} seats available)")
    print()
    
    # Test 8: Book a Seat
    print("8️⃣ Testing Book Seat...")
    booking_data = {
        "user_id": user_id,
        "bus_id": bus_id
    }
    response = requests.post(f"{BASE_URL}/api/bookings", json=booking_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        booking_id = response.json()["booking"]["booking_id"]
        seat_no = response.json()["booking"]["seat_no"]
        print(f"✅ Seat booked! Booking ID: {booking_id}, Seat: {seat_no}")
    print()
    
    # Test 9: Book Another Seat
    print("9️⃣ Testing Book Second Seat...")
    booking2_data = {
        "user_id": user2_id,
        "bus_id": bus_id
    }
    response = requests.post(f"{BASE_URL}/api/bookings", json=booking2_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        booking2_id = response.json()["booking"]["booking_id"]
        seat2_no = response.json()["booking"]["seat_no"]
        print(f"✅ Second seat booked! Booking ID: {booking2_id}, Seat: {seat2_no}")
    print()
    
    # Test 10: Get Bus Seat Details
    print("🔟 Testing Get Bus Seat Details...")
    response = requests.get(f"{BASE_URL}/api/buses/{bus_id}/seats")
    print(f"Status: {response.status_code}")
    seat_details = response.json()
    print(f"Bus: {seat_details['bus_name']}")
    print(f"Available: {seat_details['available_seats']}/{seat_details['capacity']}")
    print(f"Booked seats: {seat_details['booked_seats']}")
    print()
    
    # Test 11: Get User Booking History
    print("1️⃣1️⃣ Testing User Booking History...")
    response = requests.get(f"{BASE_URL}/api/bookings/user/{user_id}")
    print(f"Status: {response.status_code}")
    bookings = response.json()
    print(f"User has {len(bookings)} bookings:")
    for booking in bookings:
        print(f"  - Booking {booking['booking_id']}: Seat {booking['seat_no']} on {booking['bus_name']} ({booking['status']})")
    print()
    
    # Test 12: Get Specific Booking
    print("1️⃣2️⃣ Testing Get Specific Booking...")
    response = requests.get(f"{BASE_URL}/api/bookings/{booking_id}")
    print(f"Status: {response.status_code}")
    booking_details = response.json()
    print(f"Booking Details: {json.dumps(booking_details, indent=2)}")
    print()
    
    # Test 13: Cancel Booking
    print("1️⃣3️⃣ Testing Cancel Booking...")
    cancel_data = {
        "booking_id": booking2_id,
        "user_id": user2_id
    }
    response = requests.delete(f"{BASE_URL}/api/bookings", json=cancel_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Test 14: Check Buses After Cancellation
    print("1️⃣4️⃣ Testing Buses After Cancellation...")
    response = requests.get(f"{BASE_URL}/api/buses")
    buses = response.json()
    for bus in buses:
        if bus['bus_id'] == bus_id:
            print(f"Bus {bus['bus_name']} now has {bus['available_seats']}/{bus['capacity']} seats available")
    print()
    
    print("🎉 API Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server.")
        print("Make sure the server is running with: python api.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
