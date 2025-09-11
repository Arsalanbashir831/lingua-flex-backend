#!/usr/bin/env python3
"""
Quick test script to verify JSON blog creation is working
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASSWORD = "testpass123"

def test_json_blog_creation():
    """Test blog creation with JSON data"""
    print("Testing JSON Blog Creation...")
    
    # Step 1: Login to get token
    print("1. Logging in...")
    login_data = {
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        print("Please ensure you have a teacher account with these credentials")
        return
    
    token = response.json().get('token')
    print(f"✅ Login successful")
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    # Step 2: Create a category first
    print("2. Creating/Getting category...")
    category_data = {
        "name": "Test Category",
        "description": "Category for testing"
    }
    
    response = requests.post(f"{BASE_URL}/api/blogs/categories/", headers=headers, json=category_data)
    
    if response.status_code == 201:
        category_id = response.json().get('id')
        print(f"✅ Category created with ID: {category_id}")
    else:
        # Try to get existing categories
        response = requests.get(f"{BASE_URL}/api/blogs/categories/", headers=headers)
        if response.status_code == 200 and response.json().get('results'):
            category_id = response.json()['results'][0]['id']
            print(f"✅ Using existing category with ID: {category_id}")
        else:
            print(f"❌ Failed to create or get category: {response.status_code}")
            print(f"Response: {response.text}")
            return
    
    # Step 3: Test JSON blog creation
    print("3. Testing JSON blog creation...")
    
    blog_data = {
        "title": "10 Tips for Effective Language Learning",
        "content": "Language learning can be challenging, but with the right strategies, you can make significant progress. Here are 10 proven tips:\n\n1. **Practice daily**: Consistency is key to language learning success.\n2. **Immerse yourself**: Surround yourself with the language through media, music, and conversations.\n3. **Start with basics**: Master fundamental grammar and vocabulary before moving to complex topics.\n4. **Use technology**: Leverage apps, online courses, and digital tools.\n5. **Find a language partner**: Practice with native speakers or fellow learners.\n6. **Set realistic goals**: Break your learning journey into achievable milestones.\n7. **Learn through context**: Study words and phrases in real-life situations.\n8. **Don't fear mistakes**: Errors are part of the learning process.\n9. **Stay motivated**: Remember your reasons for learning the language.\n10. **Be patient**: Language acquisition takes time and dedication.\n\nRemember, everyone learns differently, so find the methods that work best for you!",
        "thumbnail": "https://example.com/language-learning-tips.jpg",
        "category": category_id,
        "tags": ["education", "language-learning", "tips", "study"],
        "status": "published",
        "meta_description": "Discover 10 proven strategies for effective language learning that will accelerate your progress and boost your confidence."
    }
    
    print(f"Sending POST request to: {BASE_URL}/api/blogs/teacher/blogs/")
    print(f"Headers: {headers}")
    print(f"Data preview: {blog_data['title']}")
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,
        json=blog_data
    )
    
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response Text: {response.text}")
    
    if response.status_code == 201:
        print("✅ Blog created successfully with JSON!")
    else:
        print(f"❌ Blog creation failed: {response.status_code}")

if __name__ == "__main__":
    try:
        test_json_blog_creation()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the Django server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Test error: {e}")
