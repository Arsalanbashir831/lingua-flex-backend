#!/usr/bin/env python3
"""
Test Public Gigs API with Search Parameters
Tests the enhanced /accounts/gigs/public/ endpoint with filtering
"""

import requests
import json
import sys

def test_public_gigs_filtering():
    """Test all the filtering options for public gigs"""
    print("🔍 Testing Public Gigs API with Search Parameters")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test cases for different filtering options
    test_cases = [
        {
            "name": "Get All Active Gigs",
            "url": f"{base_url}/api/accounts/gigs/public/",
            "description": "Default - all active gigs"
        },
        {
            "name": "Filter by Teacher ID",
            "url": f"{base_url}/api/accounts/gigs/public/?teacher_id=ad3d5ac9-9578-4229-a1f5-b80750e22fbc",
            "description": "Get gigs for specific teacher"
        },
        {
            "name": "Filter by Category",
            "url": f"{base_url}/api/accounts/gigs/public/?category=astrological",
            "description": "Get gigs in specific category"
        },
        {
            "name": "Filter by Service Type",
            "url": f"{base_url}/api/accounts/gigs/public/?service_type=Language Consultation",
            "description": "Get gigs with specific service type"
        },
        {
            "name": "Filter by Price Range",
            "url": f"{base_url}/api/accounts/gigs/public/?min_price=20&max_price=30",
            "description": "Get gigs between $20-$30"
        },
        {
            "name": "Filter by Duration",
            "url": f"{base_url}/api/accounts/gigs/public/?min_duration=30&max_duration=90",
            "description": "Get gigs between 30-90 minutes"
        },
        {
            "name": "Search by Title/Description",
            "url": f"{base_url}/api/accounts/gigs/public/?search=English",
            "description": "Search for 'English' in title/description"
        },
        {
            "name": "Order by Price (Low to High)",
            "url": f"{base_url}/api/accounts/gigs/public/?ordering=price_per_session",
            "description": "Sort by price ascending"
        },
        {
            "name": "Order by Price (High to Low)",
            "url": f"{base_url}/api/accounts/gigs/public/?ordering=-price_per_session",
            "description": "Sort by price descending"
        },
        {
            "name": "Combined Filters",
            "url": f"{base_url}/api/accounts/gigs/public/?teacher_id=ad3d5ac9-9578-4229-a1f5-b80750e22fbc&min_price=20&search=English",
            "description": "Multiple filters: specific teacher + price + search"
        }
    ]
    
    print("🧪 Testing Different Filter Combinations:")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}️⃣  {test_case['name']}")
        print(f"   📋 Description: {test_case['description']}")
        print(f"   🌐 URL: {test_case['url']}")
        
        try:
            response = requests.get(test_case['url'])
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's the new format with metadata
                if isinstance(data, dict) and 'results' in data:
                    print(f"   ✅ Status: {response.status_code}")
                    print(f"   📊 Count: {data.get('count', 'N/A')} gigs found")
                    print(f"   🔍 Filters: {json.dumps(data.get('filters_applied', {}), indent=6)}")
                    if data['results']:
                        first_gig = data['results'][0]
                        print(f"   📋 Sample Gig: {first_gig.get('service_title', 'N/A')} - ${first_gig.get('price_per_session', 'N/A')}")
                        if 'teacher_details' in first_gig:
                            teacher = first_gig['teacher_details']
                            print(f"   👨‍🏫 Teacher: {teacher.get('full_name', 'N/A')} (ID: {teacher.get('id', 'N/A')})")
                else:
                    # Old format (array)
                    print(f"   ✅ Status: {response.status_code}")
                    print(f"   📊 Count: {len(data)} gigs found")
                    if data:
                        first_gig = data[0]
                        print(f"   📋 Sample Gig: {first_gig.get('service_title', 'N/A')}")
                        
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📋 Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    return True

def demonstrate_api_usage():
    """Show examples of how to use the API"""
    print("📚 API Usage Examples")
    print("=" * 40)
    
    examples = {
        "Get all active gigs": {
            "endpoint": "GET /api/accounts/gigs/public/",
            "curl": "curl http://localhost:8000/api/accounts/gigs/public/"
        },
        "Get gigs by specific teacher": {
            "endpoint": "GET /api/accounts/gigs/public/?teacher_id=USER_UUID",
            "curl": "curl 'http://localhost:8000/api/accounts/gigs/public/?teacher_id=ad3d5ac9-9578-4229-a1f5-b80750e22fbc'",
            "javascript": """
fetch('/api/accounts/gigs/public/?teacher_id=ad3d5ac9-9578-4229-a1f5-b80750e22fbc')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.count} gigs for teacher`);
    data.results.forEach(gig => console.log(gig.service_title));
  });
            """.strip()
        },
        "Search with multiple filters": {
            "endpoint": "GET /api/accounts/gigs/public/?category=language&min_price=20&max_price=50&search=conversation",
            "curl": "curl 'http://localhost:8000/api/accounts/gigs/public/?category=language&min_price=20&max_price=50&search=conversation'",
            "javascript": """
const params = new URLSearchParams({
  category: 'language',
  min_price: '20',
  max_price: '50',
  search: 'conversation'
});

fetch(`/api/accounts/gigs/public/?${params}`)
  .then(response => response.json())
  .then(data => console.log(data));
            """.strip()
        }
    }
    
    for title, example in examples.items():
        print(f"📋 {title}:")
        print(f"   Endpoint: {example['endpoint']}")
        print(f"   cURL: {example['curl']}")
        if 'javascript' in example:
            print(f"   JavaScript:")
            for line in example['javascript'].split('\n'):
                print(f"     {line}")
        print()

def show_available_parameters():
    """Show all available query parameters"""
    print("🔧 Available Query Parameters")
    print("=" * 40)
    
    parameters = {
        "teacher_id": {
            "type": "UUID string",
            "description": "Filter by teacher user ID (from teacher_details.id)",
            "example": "teacher_id=ad3d5ac9-9578-4229-a1f5-b80750e22fbc"
        },
        "category": {
            "type": "string",
            "description": "Filter by gig category (case-insensitive partial match)",
            "example": "category=language"
        },
        "service_type": {
            "type": "string", 
            "description": "Filter by service type (case-insensitive partial match)",
            "example": "service_type=consultation"
        },
        "min_price": {
            "type": "decimal",
            "description": "Minimum price per session",
            "example": "min_price=20.00"
        },
        "max_price": {
            "type": "decimal",
            "description": "Maximum price per session", 
            "example": "max_price=50.00"
        },
        "min_duration": {
            "type": "integer",
            "description": "Minimum session duration in minutes",
            "example": "min_duration=30"
        },
        "max_duration": {
            "type": "integer",
            "description": "Maximum session duration in minutes",
            "example": "max_duration=120"
        },
        "search": {
            "type": "string",
            "description": "Search in title, short_description, and full_description",
            "example": "search=English conversation"
        },
        "ordering": {
            "type": "string",
            "description": "Sort results by field (prefix with - for descending)",
            "example": "ordering=-price_per_session",
            "options": ["created_at", "-created_at", "price_per_session", "-price_per_session", "session_duration", "-session_duration"]
        }
    }
    
    for param, details in parameters.items():
        print(f"📋 {param}:")
        print(f"   Type: {details['type']}")
        print(f"   Description: {details['description']}")
        print(f"   Example: {details['example']}")
        if 'options' in details:
            print(f"   Options: {', '.join(details['options'])}")
        print()

def main():
    print("🚀 Enhanced Public Gigs API - Complete Guide")
    print("Testing search parameters and filtering options")
    print("=" * 60)
    
    # Show available parameters first
    show_available_parameters()
    
    # Test the filtering functionality
    if test_public_gigs_filtering():
        print("✅ All filter tests completed!")
    else:
        print("❌ Some tests failed!")
    
    # Show usage examples
    print()
    demonstrate_api_usage()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY - Enhanced Public Gigs API:")
    print()
    print("✅ ADDED: teacher_id filter (your main request)")
    print("✅ ADDED: category, service_type, price range filters")
    print("✅ ADDED: duration range filters")
    print("✅ ADDED: full-text search in title/description")
    print("✅ ADDED: sorting/ordering options") 
    print("✅ ADDED: response metadata with count and applied filters")
    print()
    print("🔍 KEY FEATURE:")
    print("GET /api/accounts/gigs/public/?teacher_id=USER_UUID")
    print("Returns all gigs for the specified teacher!")
    print()
    print("📊 NEW RESPONSE FORMAT:")
    print("{")
    print('  "count": 5,')
    print('  "results": [...gigs...],')
    print('  "filters_applied": {...}')
    print("}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
