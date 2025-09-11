"""
Test script for Teacher Availability Update Operations
Tests all CRUD operations for teacher availability slots including individual and bulk updates
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
AVAILABILITY_URL = f"{BASE_URL}/api/bookings/availability/"
BULK_CREATE_URL = f"{BASE_URL}/api/bookings/availability/bulk/"
BULK_UPDATE_URL = f"{BASE_URL}/api/bookings/availability/bulk/update/"
BULK_DELETE_URL = f"{BASE_URL}/api/bookings/availability/bulk/delete/"
REPLACE_SCHEDULE_URL = f"{BASE_URL}/api/bookings/availability/replace/"

def test_availability_update_operations():
    """Test all availability update operations"""
    
    # You'll need to provide a valid teacher access token
    access_token = "YOUR_TEACHER_ACCESS_TOKEN_HERE"  # Replace with actual teacher token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Teacher Availability Update Operations")
    print("="*60)
    
    try:
        # Step 1: Create initial availability slots to work with
        print("\n=== Step 1: Create Initial Availability Slots ===")
        
        initial_schedule = [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
            {"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
            {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True}
        ]
        
        response = requests.post(BULK_CREATE_URL, json=initial_schedule, headers=headers)
        print(f"Create Status: {response.status_code}")
        
        if response.status_code == 201:
            created_data = response.json()
            print(f"✅ Created {len(created_data['availabilities'])} initial slots")
            created_slots = created_data['availabilities']
            slot_ids = [slot['id'] for slot in created_slots]
            print(f"Created slot IDs: {slot_ids}")
        else:
            print(f"❌ Failed to create initial slots: {response.text}")
            return
        
        # Step 2: Test individual availability update (PUT/PATCH)
        print(f"\n=== Step 2: Update Individual Availability Slot ===")
        
        if created_slots:
            slot_to_update = created_slots[0]
            slot_id = slot_to_update['id']
            
            update_data = {
                "day_of_week": 0,  # Monday
                "start_time": "08:00:00",  # Earlier start
                "end_time": "18:00:00",    # Later end
                "is_recurring": True
            }
            
            # Test PATCH (partial update)
            individual_url = f"{AVAILABILITY_URL}{slot_id}/"
            response = requests.patch(individual_url, json=update_data, headers=headers)
            print(f"Individual Update Status: {response.status_code}")
            
            if response.status_code == 200:
                updated_slot = response.json()
                print("✅ Individual slot updated successfully!")
                print(f"Updated Monday: {updated_slot['start_time']} - {updated_slot['end_time']}")
            else:
                print(f"❌ Failed to update individual slot: {response.text}")
        
        # Step 3: Test bulk update
        print(f"\n=== Step 3: Bulk Update Multiple Slots ===")
        
        # Get current availabilities to get their IDs
        response = requests.get(AVAILABILITY_URL, headers=headers)
        if response.status_code == 200:
            current_slots = response.json()
            
            # Prepare bulk update data (update Tuesday and Wednesday)
            bulk_update_data = []
            for slot in current_slots:
                if slot['day_of_week'] in [1, 2]:  # Tuesday and Wednesday
                    bulk_update_data.append({
                        "id": slot['id'],
                        "day_of_week": slot['day_of_week'],
                        "start_time": "10:00:00",  # Later start
                        "end_time": "16:00:00",    # Earlier end
                        "is_recurring": True
                    })
            
            if bulk_update_data:
                response = requests.put(BULK_UPDATE_URL, json=bulk_update_data, headers=headers)
                print(f"Bulk Update Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Bulk update successful!")
                    print(f"Message: {result['message']}")
                    
                    for slot in result['availabilities']:
                        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        day_name = day_names[slot['day_of_week']]
                        print(f"  - {day_name}: {slot['start_time']} - {slot['end_time']}")
                else:
                    print(f"❌ Bulk update failed: {response.text}")
        
        # Step 4: Test adding new slots to existing schedule
        print(f"\n=== Step 4: Add New Slots to Existing Schedule ===")
        
        new_slots = [
            {"day_of_week": 3, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
            {"day_of_week": 4, "start_time": "09:00:00", "end_time": "15:00:00", "is_recurring": True}
        ]
        
        response = requests.post(BULK_CREATE_URL, json=new_slots, headers=headers)
        print(f"Add New Slots Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ New slots added successfully!")
            print(f"Message: {result['message']}")
        else:
            print(f"❌ Failed to add new slots: {response.text}")
        
        # Step 5: Test replace entire weekly schedule
        print(f"\n=== Step 5: Replace Entire Weekly Schedule ===")
        
        new_weekly_schedule = [
            {"day_of_week": 0, "start_time": "08:00:00", "end_time": "12:00:00", "is_recurring": True},
            {"day_of_week": 1, "start_time": "14:00:00", "end_time": "18:00:00", "is_recurring": True},
            {"day_of_week": 2, "start_time": "10:00:00", "end_time": "16:00:00", "is_recurring": True},
            {"day_of_week": 5, "start_time": "09:00:00", "end_time": "13:00:00", "is_recurring": True},
            {"day_of_week": 6, "start_time": "11:00:00", "end_time": "15:00:00", "is_recurring": True}
        ]
        
        response = requests.put(REPLACE_SCHEDULE_URL, json=new_weekly_schedule, headers=headers)
        print(f"Replace Schedule Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Weekly schedule replaced successfully!")
            print(f"Message: {result['message']}")
            
            print("\nNew weekly schedule:")
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for slot in result['availabilities']:
                day_name = day_names[slot['day_of_week']]
                print(f"  - {day_name}: {slot['start_time']} - {slot['end_time']}")
        else:
            print(f"❌ Failed to replace schedule: {response.text}")
        
        # Step 6: Test bulk delete
        print(f"\n=== Step 6: Bulk Delete Specific Slots ===")
        
        # Get current availabilities
        response = requests.get(AVAILABILITY_URL, headers=headers)
        if response.status_code == 200:
            current_slots = response.json()
            
            # Delete weekend slots (Saturday and Sunday)
            weekend_slot_ids = [
                slot['id'] for slot in current_slots 
                if slot['day_of_week'] in [5, 6]
            ]
            
            if weekend_slot_ids:
                delete_data = weekend_slot_ids  # Array of IDs format
                
                response = requests.delete(BULK_DELETE_URL, json=delete_data, headers=headers)
                print(f"Bulk Delete Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Weekend slots deleted successfully!")
                    print(f"Message: {result['message']}")
                    print(f"Deleted IDs: {result['deleted_ids']}")
                else:
                    print(f"❌ Bulk delete failed: {response.text}")
            else:
                print("No weekend slots found to delete")
        
        # Step 7: Verify final state
        print(f"\n=== Step 7: Verify Final Schedule ===")
        
        response = requests.get(AVAILABILITY_URL, headers=headers)
        print(f"Get Final Schedule Status: {response.status_code}")
        
        if response.status_code == 200:
            final_slots = response.json()
            print(f"✅ Final schedule has {len(final_slots)} slots")
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            print("\nFinal weekly schedule:")
            for day_num, day_name in enumerate(day_names):
                day_slots = [slot for slot in final_slots if slot['day_of_week'] == day_num]
                if day_slots:
                    for slot in day_slots:
                        print(f"  - {day_name}: {slot['start_time']} - {slot['end_time']} (ID: {slot['id']})")
                else:
                    print(f"  - {day_name}: No availability")
        else:
            print(f"❌ Failed to get final schedule: {response.text}")
        
        # Step 8: Test error cases
        print(f"\n=== Step 8: Test Error Cases ===")
        
        # Test updating non-existent slot
        invalid_update_data = [
            {"id": 99999, "start_time": "09:00:00", "end_time": "17:00:00"}
        ]
        
        response = requests.put(BULK_UPDATE_URL, json=invalid_update_data, headers=headers)
        print(f"Invalid Update Status: {response.status_code}")
        
        if response.status_code == 400:
            error = response.json()
            print("✅ Error handling working correctly!")
            print(f"Error details: {error.get('details', error)}")
        else:
            print(f"⚠️  Expected validation error, got: {response.status_code}")
        
        # Test deleting non-existent slots
        response = requests.delete(BULK_DELETE_URL, json=[99999, 99998], headers=headers)
        print(f"Invalid Delete Status: {response.status_code}")
        
        if response.status_code == 400:
            error = response.json()
            print("✅ Delete error handling working correctly!")
            print(f"Missing IDs: {error.get('missing_ids', [])}")
        else:
            print(f"⚠️  Expected delete error, got: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_update_api_examples():
    """Show various ways to use the update APIs"""
    
    print("\n" + "="*60)
    print("=== Update API Usage Examples ===")
    
    print("\n1. Individual Slot Update (PATCH):")
    print("""
// Update a single availability slot
const updateSlot = async (slotId, updateData) => {
    const response = await fetch(`/api/bookings/availability/${slotId}/`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${teacherToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    });
    return response.json();
};

// Example: Update Monday to start earlier
updateSlot(42, {
    start_time: "08:00:00",
    end_time: "18:00:00"
});
""")
    
    print("\n2. Bulk Update Multiple Slots:")
    print("""
// Update multiple slots at once
const bulkUpdate = async (updates) => {
    const response = await fetch('/api/bookings/availability/bulk/update/', {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${teacherToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
    });
    return response.json();
};

// Example: Update Tuesday and Wednesday
bulkUpdate([
    {id: 43, start_time: "10:00:00", end_time: "16:00:00"},
    {id: 44, start_time: "10:00:00", end_time: "16:00:00"}
]);
""")
    
    print("\n3. Replace Entire Weekly Schedule:")
    print("""
// Replace entire weekly schedule
const replaceSchedule = async (newSchedule) => {
    const response = await fetch('/api/bookings/availability/replace/', {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${teacherToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newSchedule)
    });
    return response.json();
};

// Example: Set new flexible schedule
replaceSchedule([
    {day_of_week: 0, start_time: "08:00:00", end_time: "12:00:00", is_recurring: true},
    {day_of_week: 2, start_time: "14:00:00", end_time: "18:00:00", is_recurring: true},
    {day_of_week: 4, start_time: "10:00:00", end_time: "16:00:00", is_recurring: true}
]);
""")
    
    print("\n4. Bulk Delete Slots:")
    print("""
// Delete multiple slots by ID
const bulkDelete = async (slotIds) => {
    const response = await fetch('/api/bookings/availability/bulk/delete/', {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${teacherToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(slotIds)
    });
    return response.json();
};

// Example: Delete weekend availability
bulkDelete([45, 46]); // Array of slot IDs

// Alternative formats:
bulkDelete([{id: 45}, {id: 46}]); // Array of objects
bulkDelete({ids: [45, 46]});       // Wrapped format
""")

def show_common_update_scenarios():
    """Show common update scenarios teachers might need"""
    
    print("\n" + "="*60)
    print("=== Common Update Scenarios ===")
    
    scenarios = [
        {
            "name": "Extend Working Hours",
            "description": "Teacher wants to start earlier and end later",
            "method": "PATCH",
            "url": "/api/bookings/availability/{slot_id}/",
            "data": {
                "start_time": "08:00:00",  # Earlier start
                "end_time": "19:00:00"     # Later end
            }
        },
        {
            "name": "Change Mid-Week Schedule", 
            "description": "Update Tuesday, Wednesday, Thursday to different hours",
            "method": "PUT",
            "url": "/api/bookings/availability/bulk/update/",
            "data": [
                {"id": 43, "start_time": "10:00:00", "end_time": "14:00:00"},
                {"id": 44, "start_time": "10:00:00", "end_time": "14:00:00"},
                {"id": 45, "start_time": "10:00:00", "end_time": "14:00:00"}
            ]
        },
        {
            "name": "Switch to Weekend Teaching",
            "description": "Remove weekdays, add weekend availability",
            "method": "PUT",
            "url": "/api/bookings/availability/replace/",
            "data": [
                {"day_of_week": 5, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
                {"day_of_week": 6, "start_time": "10:00:00", "end_time": "16:00:00", "is_recurring": True}
            ]
        },
        {
            "name": "Remove Specific Days",
            "description": "Teacher no longer available on certain days",
            "method": "DELETE",
            "url": "/api/bookings/availability/bulk/delete/",
            "data": [47, 48]  # IDs of slots to remove
        },
        {
            "name": "Vacation Mode",
            "description": "Temporarily remove all availability",
            "method": "PUT", 
            "url": "/api/bookings/availability/replace/",
            "data": []  # Empty schedule
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"Description: {scenario['description']}")
        print(f"Method: {scenario['method']} {scenario['url']}")
        print(f"Data: {json.dumps(scenario['data'], indent=2)}")

if __name__ == "__main__":
    print("=== Teacher Availability Update Testing ===")
    
    print("\nThis test suite covers:")
    print("- Individual availability slot updates (PATCH)")
    print("- Bulk updates of multiple slots")
    print("- Adding new slots to existing schedule")
    print("- Replacing entire weekly schedule")
    print("- Bulk deletion of slots")
    print("- Error handling and validation")
    
    print("\n" + "="*60)
    print("Available Update Endpoints:")
    print("- PATCH /api/bookings/availability/{id}/          - Update single slot")
    print("- PUT   /api/bookings/availability/bulk/update/    - Update multiple slots")
    print("- PUT   /api/bookings/availability/replace/        - Replace entire schedule")
    print("- DELETE /api/bookings/availability/bulk/delete/   - Delete multiple slots")
    print("- DELETE /api/bookings/availability/{id}/          - Delete single slot")
    print("="*60)
    
    # Show examples and scenarios
    show_update_api_examples()
    show_common_update_scenarios()
    
    print(f"\n{'='*60}")
    print("To run the actual tests, uncomment the function call below:")
    print("# test_availability_update_operations()")
    
    # Uncomment to run actual tests (after setting token)
    # test_availability_update_operations()
