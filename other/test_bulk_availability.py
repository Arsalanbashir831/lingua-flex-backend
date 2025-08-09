"""
Test script for Bulk Teacher Availability Creation
Tests the new endpoint for setting teacher availability for the whole week at once
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
BULK_AVAILABILITY_URL = f"{BASE_URL}/api/bookings/availability/bulk/"
AVAILABILITY_URL = f"{BASE_URL}/api/bookings/availability/"

def test_bulk_availability_creation():
    """Test bulk creation of teacher availability slots"""
    
    # You'll need to provide a valid teacher access token
    access_token = "YOUR_TEACHER_ACCESS_TOKEN_HERE"  # Replace with actual teacher token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Bulk Teacher Availability Creation")
    print(f"Bulk URL: {BULK_AVAILABILITY_URL}")
    print("="*60)
    
    try:
        # Test 1: Create availability for full week (array format)
        print("\n=== Test 1: Create Full Week Availability (Array Format) ===")
        
        full_week_data = [
            {
                "day_of_week": 0,  # Monday
                "start_time": "09:00:00",
                "end_time": "17:00:00", 
                "is_recurring": True
            },
            {
                "day_of_week": 1,  # Tuesday
                "start_time": "09:00:00",
                "end_time": "17:00:00", 
                "is_recurring": True
            },
            {
                "day_of_week": 2,  # Wednesday
                "start_time": "10:00:00",
                "end_time": "16:00:00", 
                "is_recurring": True
            },
            {
                "day_of_week": 3,  # Thursday
                "start_time": "09:00:00",
                "end_time": "17:00:00", 
                "is_recurring": True
            },
            {
                "day_of_week": 4,  # Friday
                "start_time": "09:00:00",
                "end_time": "15:00:00", 
                "is_recurring": True
            }
        ]
        
        response = requests.post(BULK_AVAILABILITY_URL, json=full_week_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Full week availability created successfully!")
            print(f"Message: {result['message']}")
            print(f"Created {len(result['availabilities'])} availability slots")
            
            # Show created slots
            for slot in result['availabilities']:
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_name = day_names[slot['day_of_week']]
                print(f"  - {day_name}: {slot['start_time']} - {slot['end_time']}")
        else:
            print(f"❌ Failed to create availability: {response.text}")
        
        # Test 2: Create availability with wrapped format
        print(f"\n=== Test 2: Create Availability (Wrapped Format) ===")
        
        wrapped_data = {
            "availabilities": [
                {
                    "day_of_week": 5,  # Saturday
                    "start_time": "10:00:00",
                    "end_time": "14:00:00", 
                    "is_recurring": True
                },
                {
                    "day_of_week": 6,  # Sunday
                    "start_time": "12:00:00",
                    "end_time": "16:00:00", 
                    "is_recurring": True
                }
            ]
        }
        
        response = requests.post(BULK_AVAILABILITY_URL, json=wrapped_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Weekend availability created successfully!")
            print(f"Message: {result['message']}")
        else:
            print(f"❌ Failed to create weekend availability: {response.text}")
        
        # Test 3: Update existing availability
        print(f"\n=== Test 3: Update Existing Availability ===")
        
        update_data = [
            {
                "day_of_week": 0,  # Monday - update existing
                "start_time": "08:00:00",  # Earlier start time
                "end_time": "18:00:00",    # Later end time
                "is_recurring": True
            }
        ]
        
        response = requests.post(BULK_AVAILABILITY_URL, json=update_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Monday availability updated successfully!")
            print(f"Message: {result['message']}")
            updated_slot = result['availabilities'][0]
            print(f"Updated Monday: {updated_slot['start_time']} - {updated_slot['end_time']}")
        else:
            print(f"❌ Failed to update availability: {response.text}")
        
        # Test 4: Get all teacher's availability to verify
        print(f"\n=== Test 4: Verify All Availability Slots ===")
        
        response = requests.get(AVAILABILITY_URL, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            availabilities = response.json()
            print(f"✅ Retrieved {len(availabilities)} availability slots")
            
            # Group by day and display
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day_num, day_name in enumerate(day_names):
                day_slots = [slot for slot in availabilities if slot['day_of_week'] == day_num]
                if day_slots:
                    print(f"\n{day_name}:")
                    for slot in day_slots:
                        print(f"  - {slot['start_time']} to {slot['end_time']} (Recurring: {slot['is_recurring']})")
                else:
                    print(f"\n{day_name}: No availability")
        else:
            print(f"❌ Failed to retrieve availability: {response.text}")
        
        # Test 5: Validation errors
        print(f"\n=== Test 5: Test Validation Errors ===")
        
        invalid_data = [
            {
                "day_of_week": 0,
                "start_time": "18:00:00",  # Start time after end time
                "end_time": "09:00:00",
                "is_recurring": True
            },
            {
                "day_of_week": 8,  # Invalid day (should be 0-6)
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "is_recurring": True
            }
        ]
        
        response = requests.post(BULK_AVAILABILITY_URL, json=invalid_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            errors = response.json()
            print("✅ Validation working correctly!")
            print(f"Error details: {json.dumps(errors, indent=2)}")
        else:
            print(f"⚠️  Expected validation error, got: {response.status_code}")
        
        # Test 6: Empty data
        print(f"\n=== Test 6: Test Empty Data ===")
        
        response = requests.post(BULK_AVAILABILITY_URL, json=[], headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            error = response.json()
            print("✅ Empty data validation working!")
            print(f"Error: {error['error']}")
        else:
            print(f"⚠️  Expected validation error for empty data")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_different_availability_patterns():
    """Test various availability patterns that teachers might use"""
    
    print("\n" + "="*60)
    print("=== Different Availability Patterns ===")
    
    patterns = [
        {
            "name": "Full-time Teacher (Monday-Friday, 9-5)",
            "data": [
                {"day_of_week": i, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True}
                for i in range(5)  # Monday to Friday
            ]
        },
        {
            "name": "Part-time Teacher (Tuesday/Thursday evenings)",
            "data": [
                {"day_of_week": 1, "start_time": "18:00:00", "end_time": "21:00:00", "is_recurring": True},
                {"day_of_week": 3, "start_time": "18:00:00", "end_time": "21:00:00", "is_recurring": True}
            ]
        },
        {
            "name": "Weekend Teacher (Saturday/Sunday mornings)",
            "data": [
                {"day_of_week": 5, "start_time": "08:00:00", "end_time": "12:00:00", "is_recurring": True},
                {"day_of_week": 6, "start_time": "09:00:00", "end_time": "13:00:00", "is_recurring": True}
            ]
        },
        {
            "name": "Flexible Teacher (Different hours each day)",
            "data": [
                {"day_of_week": 0, "start_time": "08:00:00", "end_time": "12:00:00", "is_recurring": True},
                {"day_of_week": 1, "start_time": "14:00:00", "end_time": "18:00:00", "is_recurring": True},
                {"day_of_week": 2, "start_time": "10:00:00", "end_time": "16:00:00", "is_recurring": True},
                {"day_of_week": 3, "start_time": "09:00:00", "end_time": "13:00:00", "is_recurring": True},
                {"day_of_week": 4, "start_time": "15:00:00", "end_time": "19:00:00", "is_recurring": True}
            ]
        }
    ]
    
    for pattern in patterns:
        print(f"\n{pattern['name']}:")
        print(json.dumps(pattern['data'], indent=2))

def show_api_usage_examples():
    """Show various ways to use the bulk availability API"""
    
    print("\n" + "="*60)
    print("=== API Usage Examples ===")
    
    print("\n1. JavaScript/Fetch API:")
    print("""
const createWeeklyAvailability = async (availabilityData) => {
    const response = await fetch('/api/bookings/availability/bulk/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(availabilityData)
    });
    
    if (response.ok) {
        const result = await response.json();
        console.log('Availability created:', result.message);
        return result.availabilities;
    } else {
        const error = await response.json();
        throw new Error(error.error);
    }
};

// Usage - Set Monday to Friday, 9 AM to 5 PM
const weekdaySchedule = [
    {day_of_week: 0, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 1, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 2, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 3, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 4, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true}
];

createWeeklyAvailability(weekdaySchedule);
""")
    
    print("\n2. Python/requests:")
    print("""
import requests

def set_teacher_availability(access_token, schedule):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'http://localhost:8000/api/bookings/availability/bulk/',
        json=schedule,
        headers=headers
    )
    
    return response.json()

# Set availability for the whole week
weekly_schedule = [
    {"day_of_week": i, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True}
    for i in range(7)  # All 7 days
]

result = set_teacher_availability(token, weekly_schedule)
""")
    
    print("\n3. cURL:")
    print("""
curl -X POST http://localhost:8000/api/bookings/availability/bulk/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '[
    {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true}
  ]'
""")

if __name__ == "__main__":
    print("=== Bulk Teacher Availability Testing ===")
    
    print("\nThis test suite covers:")
    print("- Creating availability for multiple days at once")
    print("- Both array and wrapped data formats")
    print("- Updating existing availability slots")
    print("- Validation testing")
    print("- Retrieving and verifying created slots")
    
    print("\n" + "="*60)
    print("Setup Instructions:")
    print("1. Update the access_token variable with a valid TEACHER token")
    print("2. Ensure Django server is running: python manage.py runserver")
    print("3. Ensure user has TEACHER role")
    print("="*60)
    
    # Show usage examples and patterns
    test_different_availability_patterns()
    show_api_usage_examples()
    
    print(f"\n{'='*60}")
    print("To run the actual tests, uncomment the function call below:")
    print("# test_bulk_availability_creation()")
    
    # Uncomment to run actual tests (after setting token)
    # test_bulk_availability_creation()
