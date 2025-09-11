"""
Test script for Weekly Teacher Availability Endpoint
Tests the new endpoint for getting teacher's complete weekly availability schedule
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
WEEKLY_AVAILABILITY_URL = f"{BASE_URL}/api/bookings/availability/weekly/"
BULK_CREATE_URL = f"{BASE_URL}/api/bookings/availability/bulk/"

def test_weekly_availability_endpoint():
    """Test weekly availability endpoint for both students and teachers"""
    
    # Test with both student and teacher tokens
    test_scenarios = [
        {
            "name": "Student accessing teacher availability",
            "token": "YOUR_STUDENT_ACCESS_TOKEN_HERE",  # Replace with actual student token
            "description": "Student should be able to view teacher's weekly schedule"
        },
        {
            "name": "Teacher accessing own availability", 
            "token": "YOUR_TEACHER_ACCESS_TOKEN_HERE",  # Replace with actual teacher token
            "description": "Teacher should be able to view their own weekly schedule"
        },
        {
            "name": "Teacher accessing another teacher's availability",
            "token": "YOUR_TEACHER_ACCESS_TOKEN_HERE",  # Replace with actual teacher token
            "description": "Teacher should be able to view other teachers' schedules"
        }
    ]
    
    # Teacher ID to test with (replace with actual teacher ID)
    test_teacher_id = "YOUR_TEST_TEACHER_ID_HERE"
    
    print("Testing Weekly Teacher Availability Endpoint")
    print(f"URL: {WEEKLY_AVAILABILITY_URL}")
    print("="*60)
    
    for scenario in test_scenarios:
        print(f"\n=== {scenario['name']} ===")
        print(f"Description: {scenario['description']}")
        
        headers = {
            "Authorization": f"Bearer {scenario['token']}",
            "Content-Type": "application/json"
        }
        
        try:
            # Test getting weekly availability
            params = {"teacher_id": test_teacher_id}
            response = requests.get(WEEKLY_AVAILABILITY_URL, params=params, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Successfully retrieved weekly availability!")
                
                # Display teacher info
                teacher = data['teacher']
                print(f"\nTeacher Info:")
                print(f"  - Name: {teacher['name']}")
                print(f"  - Email: {teacher['email']}")
                if 'hourly_rate' in teacher:
                    print(f"  - Hourly Rate: ${teacher['hourly_rate']}")
                if 'experience_years' in teacher:
                    print(f"  - Experience: {teacher['experience_years']} years")
                
                # Display weekly schedule
                weekly_schedule = data['weekly_schedule']
                print(f"\nWeekly Schedule:")
                for day_name, day_data in weekly_schedule.items():
                    if day_data['available']:
                        print(f"\n  {day_name}:")
                        for slot in day_data['slots']:
                            duration = slot['duration_hours']
                            print(f"    - {slot['start_time']} to {slot['end_time']} ({duration:.1f} hours)")
                    else:
                        print(f"  {day_name}: Not available")
                
                # Display summary
                summary = data['summary']
                print(f"\nSummary:")
                print(f"  - Total availability slots: {summary['total_availability_slots']}")
                print(f"  - Available days: {summary['available_days_count']}/7")
                print(f"  - Total weekly hours: {summary['total_weekly_hours']}")
                print(f"  - Days with availability: {', '.join(summary['days_with_availability'])}")
                
            elif response.status_code == 400:
                error = response.json()
                print(f"❌ Bad Request: {error.get('error', 'Unknown error')}")
            elif response.status_code == 404:
                error = response.json()
                print(f"❌ Not Found: {error.get('error', 'Teacher not found')}")
            elif response.status_code == 401:
                print("❌ Unauthorized: Invalid or missing token")
            else:
                print(f"❌ Unexpected error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure Django server is running.")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_weekly_availability_with_sample_data():
    """Test with creating sample data first"""
    
    teacher_token = "YOUR_TEACHER_ACCESS_TOKEN_HERE"  # Replace with actual teacher token
    
    headers = {
        "Authorization": f"Bearer {teacher_token}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "="*60)
    print("=== Testing with Sample Data Creation ===")
    
    try:
        # Step 1: Create sample weekly availability
        print("\nStep 1: Creating sample weekly availability...")
        
        sample_schedule = [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00", "is_recurring": True},  # Monday morning
            {"day_of_week": 0, "start_time": "14:00:00", "end_time": "18:00:00", "is_recurring": True},  # Monday afternoon
            {"day_of_week": 1, "start_time": "10:00:00", "end_time": "16:00:00", "is_recurring": True},  # Tuesday
            {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},  # Wednesday
            {"day_of_week": 4, "start_time": "13:00:00", "end_time": "19:00:00", "is_recurring": True},  # Friday
            {"day_of_week": 5, "start_time": "08:00:00", "end_time": "14:00:00", "is_recurring": True},  # Saturday
        ]
        
        response = requests.post(BULK_CREATE_URL, json=sample_schedule, headers=headers)
        print(f"Create Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Created {len(result['availabilities'])} availability slots")
            
            # Get the teacher ID from the created data
            teacher_id = result['availabilities'][0]['teacher']
            
            # Step 2: Test weekly availability endpoint
            print(f"\nStep 2: Getting weekly availability for teacher {teacher_id}...")
            
            params = {"teacher_id": teacher_id}
            response = requests.get(WEEKLY_AVAILABILITY_URL, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Successfully retrieved weekly availability!")
                
                # Show formatted weekly schedule
                print(f"\n📅 Weekly Schedule for {data['teacher']['name']}:")
                print("-" * 50)
                
                for day_name, day_data in data['weekly_schedule'].items():
                    print(f"{day_name:12} ", end="")
                    if day_data['available']:
                        time_ranges = []
                        for slot in day_data['slots']:
                            start = slot['start_time'][:5]  # Remove seconds
                            end = slot['end_time'][:5]
                            time_ranges.append(f"{start}-{end}")
                        print(f"Available: {', '.join(time_ranges)}")
                    else:
                        print("Not available")
                
                summary = data['summary']
                print(f"\n📊 Summary:")
                print(f"   Total slots: {summary['total_availability_slots']}")
                print(f"   Available days: {summary['available_days_count']}/7")
                print(f"   Total hours/week: {summary['total_weekly_hours']}")
                
            else:
                print(f"❌ Failed to get weekly availability: {response.text}")
        else:
            print(f"❌ Failed to create sample data: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_error_scenarios():
    """Test various error scenarios"""
    
    print("\n" + "="*60)
    print("=== Testing Error Scenarios ===")
    
    # Test without token
    print("\n1. Testing without authentication:")
    response = requests.get(WEEKLY_AVAILABILITY_URL, params={"teacher_id": "123"})
    print(f"Status: {response.status_code} (Expected: 401 Unauthorized)")
    
    # Test with valid token but missing teacher_id
    print("\n2. Testing without teacher_id parameter:")
    headers = {"Authorization": "Bearer YOUR_TOKEN_HERE"}
    response = requests.get(WEEKLY_AVAILABILITY_URL, headers=headers)
    print(f"Status: {response.status_code} (Expected: 400 Bad Request)")
    if response.status_code == 400:
        error = response.json()
        print(f"Error: {error.get('error')}")
    
    # Test with non-existent teacher
    print("\n3. Testing with non-existent teacher:")
    params = {"teacher_id": "99999999-9999-9999-9999-999999999999"}
    response = requests.get(WEEKLY_AVAILABILITY_URL, params=params, headers=headers)
    print(f"Status: {response.status_code} (Expected: 404 Not Found)")
    if response.status_code == 404:
        error = response.json()
        print(f"Error: {error.get('error')}")

def show_api_usage_examples():
    """Show various ways to use the weekly availability API"""
    
    print("\n" + "="*60)
    print("=== API Usage Examples ===")
    
    print("\n1. JavaScript/Fetch API:")
    print("""
// Get teacher's weekly availability
const getTeacherWeeklyAvailability = async (teacherId) => {
    try {
        const response = await fetch(`/api/bookings/availability/weekly/?teacher_id=${teacherId}`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data;
        } else {
            const error = await response.json();
            throw new Error(error.error);
        }
    } catch (error) {
        console.error('Error fetching weekly availability:', error);
        throw error;
    }
};

// Usage
getTeacherWeeklyAvailability('teacher-uuid-here')
    .then(data => {
        console.log('Teacher:', data.teacher.name);
        console.log('Available days:', data.summary.available_days_count);
        console.log('Total hours:', data.summary.total_weekly_hours);
        
        // Display weekly schedule
        Object.entries(data.weekly_schedule).forEach(([day, schedule]) => {
            if (schedule.available) {
                console.log(`${day}: ${schedule.slots.length} slots`);
            }
        });
    })
    .catch(error => console.error('Failed to load availability:', error));
""")
    
    print("\n2. React Component Example:")
    print("""
import React, { useState, useEffect } from 'react';

const TeacherWeeklySchedule = ({ teacherId }) => {
    const [schedule, setSchedule] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchWeeklySchedule = async () => {
            try {
                const response = await fetch(
                    `/api/bookings/availability/weekly/?teacher_id=${teacherId}`,
                    {
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    setSchedule(data);
                } else {
                    const errorData = await response.json();
                    setError(errorData.error);
                }
            } catch (err) {
                setError('Failed to load teacher schedule');
            } finally {
                setLoading(false);
            }
        };

        if (teacherId) {
            fetchWeeklySchedule();
        }
    }, [teacherId]);

    if (loading) return <div>Loading teacher schedule...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!schedule) return <div>No schedule data available</div>;

    return (
        <div className="teacher-weekly-schedule">
            <div className="teacher-info">
                <h2>{schedule.teacher.name}</h2>
                <p>📧 {schedule.teacher.email}</p>
                {schedule.teacher.hourly_rate && (
                    <p>💰 ${schedule.teacher.hourly_rate}/hour</p>
                )}
                {schedule.teacher.experience_years && (
                    <p>🎓 {schedule.teacher.experience_years} years experience</p>
                )}
            </div>

            <div className="schedule-summary">
                <h3>Schedule Summary</h3>
                <p>📅 Available {schedule.summary.available_days_count} days per week</p>
                <p>⏰ {schedule.summary.total_weekly_hours} total hours</p>
                <p>📊 {schedule.summary.total_availability_slots} time slots</p>
            </div>

            <div className="weekly-grid">
                <h3>Weekly Availability</h3>
                {Object.entries(schedule.weekly_schedule).map(([day, dayData]) => (
                    <div key={day} className={`day-card ${dayData.available ? 'available' : 'unavailable'}`}>
                        <h4>{day}</h4>
                        {dayData.available ? (
                            <div className="time-slots">
                                {dayData.slots.map((slot, index) => (
                                    <div key={index} className="time-slot">
                                        {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                                        <span className="duration">
                                            ({slot.duration_hours.toFixed(1)}h)
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-availability">Not available</p>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TeacherWeeklySchedule;
""")
    
    print("\n3. Python Client Example:")
    print("""
import requests

class BookingClient:
    def __init__(self, base_url, access_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_teacher_weekly_availability(self, teacher_id):
        \"\"\"Get teacher's complete weekly availability\"\"\"
        response = requests.get(
            f'{self.base_url}/api/bookings/availability/weekly/',
            params={'teacher_id': teacher_id},
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def display_teacher_schedule(self, teacher_id):
        \"\"\"Display formatted teacher schedule\"\"\"
        try:
            data = self.get_teacher_weekly_availability(teacher_id)
            
            teacher = data['teacher']
            print(f"\\n👨‍🏫 Teacher: {teacher['name']}")
            print(f"📧 Email: {teacher['email']}")
            
            if 'hourly_rate' in teacher:
                print(f"💰 Rate: ${teacher['hourly_rate']}/hour")
            
            print(f"\\n📅 Weekly Schedule:")
            print("-" * 40)
            
            for day, schedule in data['weekly_schedule'].items():
                print(f"{day:12} ", end="")
                if schedule['available']:
                    slots = []
                    for slot in schedule['slots']:
                        start = slot['start_time'][:5]
                        end = slot['end_time'][:5]
                        slots.append(f"{start}-{end}")
                    print(f"✅ {', '.join(slots)}")
                else:
                    print("❌ Not available")
            
            summary = data['summary']
            print(f"\\n📊 Summary:")
            print(f"   Available days: {summary['available_days_count']}/7")
            print(f"   Total hours: {summary['total_weekly_hours']}")
            print(f"   Total slots: {summary['total_availability_slots']}")
            
        except requests.HTTPError as e:
            print(f"Error: {e.response.json()}")

# Usage
client = BookingClient('http://localhost:8000', 'your-token-here')
client.display_teacher_schedule('teacher-id-here')
""")

if __name__ == "__main__":
    print("=== Weekly Teacher Availability Testing ===")
    
    print("\nThis test suite covers:")
    print("- Getting teacher's complete weekly availability")
    print("- Access from both student and teacher perspectives")
    print("- Teacher profile information included")
    print("- Weekly schedule breakdown by day")
    print("- Summary statistics and availability overview")
    print("- Error handling for various scenarios")
    
    print("\n" + "="*60)
    print("New Endpoint:")
    print("GET /api/bookings/availability/weekly/?teacher_id={teacher_id}")
    print("- Accessible by both students and teachers")
    print("- Returns complete weekly schedule with teacher info")
    print("- Includes summary statistics")
    print("="*60)
    
    # Show examples and usage
    show_api_usage_examples()
    
    print(f"\n{'='*60}")
    print("Setup Instructions:")
    print("1. Update the access tokens with valid tokens")
    print("2. Update the teacher ID with a real teacher ID")
    print("3. Ensure Django server is running: python manage.py runserver")
    print("4. Ensure teacher has some availability slots created")
    print("="*60)
    
    print(f"\n{'='*60}")
    print("To run the actual tests, uncomment the function calls below:")
    print("# test_weekly_availability_endpoint()")
    print("# test_weekly_availability_with_sample_data()")
    print("# test_error_scenarios()")
    
    # Uncomment to run actual tests (after setting tokens and teacher ID)
    # test_weekly_availability_endpoint()
    # test_weekly_availability_with_sample_data()
    # test_error_scenarios()
