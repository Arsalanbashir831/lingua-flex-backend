"""
Test script for Blogs API
Tests CRUD operations for teacher blogs
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEACHER_BLOGS_URL = f"{BASE_URL}/api/teacher/blogs/"
PUBLIC_BLOGS_URL = f"{BASE_URL}/api/blogs/"
CATEGORIES_URL = f"{BASE_URL}/api/categories/"
STATS_URL = f"{BASE_URL}/api/teacher/blogs/stats/"

def test_blog_crud_operations():
    """Test complete CRUD operations for teacher blogs"""
    
    # Teacher access token
    teacher_token = "YOUR_TEACHER_ACCESS_TOKEN_HERE"  # Replace with actual teacher token
    
    headers = {
        "Authorization": f"Bearer {teacher_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Teacher Blog CRUD Operations...")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    try:
        # Step 1: Create a blog category
        print("\n=== Step 1: Create Blog Category ===")
        category_data = {
            "name": "Language Learning Tips",
            "description": "Tips and tricks for effective language learning"
        }
        
        response = requests.post(CATEGORIES_URL, json=category_data, headers=headers)
        print(f"Category Creation Status: {response.status_code}")
        
        if response.status_code == 201:
            category = response.json()
            category_id = category['id']
            print(f"✅ Category created: {category['name']} (ID: {category_id})")
        else:
            print(f"❌ Category creation failed: {response.text}")
            category_id = None
        
        # Step 2: Create a new blog
        print("\n=== Step 2: Create New Blog ===")
        blog_data = {
            "title": "10 Effective Ways to Learn a New Language",
            "content": """
            Learning a new language can be an exciting and rewarding journey. Here are 10 proven methods that can help accelerate your language learning process:

            1. **Immerse Yourself Daily**: Try to use the language for at least 30 minutes every day. This could be through reading, listening to music, or watching videos.

            2. **Practice Speaking from Day One**: Don't wait until you feel "ready" to start speaking. Practice pronunciation and simple phrases from the beginning.

            3. **Use Spaced Repetition**: Review vocabulary and grammar rules at increasing intervals to improve long-term retention.

            4. **Find a Language Exchange Partner**: Connect with native speakers who are learning your language for mutual practice.

            5. **Set Specific, Measurable Goals**: Instead of "I want to be fluent," set goals like "I want to have a 10-minute conversation about hobbies."

            6. **Learn in Context**: Study phrases and sentences rather than isolated words to understand how the language flows naturally.

            7. **Make Mistakes Confidently**: Embrace errors as learning opportunities rather than reasons to feel embarrassed.

            8. **Use Multiple Learning Resources**: Combine apps, books, podcasts, videos, and real conversations for a well-rounded approach.

            9. **Focus on High-Frequency Words**: Learn the most commonly used words first to quickly improve your comprehension.

            10. **Stay Consistent**: Regular, shorter study sessions are more effective than occasional long cramming sessions.

            Remember, language learning is a marathon, not a sprint. Be patient with yourself and celebrate small victories along the way!
            """,
            "thumbnail": "https://example.com/language-learning-tips.jpg",
            "category": category_id,
            "tags": ["language learning", "education", "tips", "study methods", "polyglot"],
            "status": "draft",
            "meta_description": "Discover 10 proven methods to accelerate your language learning journey and achieve fluency faster."
        }
        
        response = requests.post(TEACHER_BLOGS_URL, json=blog_data, headers=headers)
        print(f"Blog Creation Status: {response.status_code}")
        
        if response.status_code == 201:
            blog = response.json()
            blog_id = blog['id']
            print(f"✅ Blog created: {blog['title']} (ID: {blog_id})")
            print(f"   Slug: {blog['slug']}")
            print(f"   Status: {blog['status']}")
            print(f"   Read Time: {blog['read_time']} minutes")
        else:
            print(f"❌ Blog creation failed: {response.text}")
            return
        
        # Step 3: Get teacher's blogs
        print("\n=== Step 3: Get Teacher's Blogs ===")
        response = requests.get(TEACHER_BLOGS_URL, headers=headers)
        print(f"Get Blogs Status: {response.status_code}")
        
        if response.status_code == 200:
            blogs_data = response.json()
            print(f"✅ Retrieved {blogs_data['count']} blogs")
            if blogs_data['results']:
                print("   Recent blogs:")
                for blog in blogs_data['results'][:3]:
                    print(f"     - {blog['title']} ({blog['status']})")
        
        # Step 4: Update the blog
        print("\n=== Step 4: Update Blog ===")
        update_data = {
            "title": "10 Effective Ways to Learn a New Language - Updated",
            "status": "published",
            "tags": ["language learning", "education", "tips", "study methods", "polyglot", "fluency"]
        }
        
        response = requests.patch(f"{TEACHER_BLOGS_URL}{blog_id}/", json=update_data, headers=headers)
        print(f"Blog Update Status: {response.status_code}")
        
        if response.status_code == 200:
            updated_blog = response.json()
            print(f"✅ Blog updated: {updated_blog['title']}")
            print(f"   New Status: {updated_blog['status']}")
            print(f"   Tags: {updated_blog['tag_list']}")
        
        # Step 5: Get blog statistics
        print("\n=== Step 5: Get Blog Statistics ===")
        response = requests.get(STATS_URL, headers=headers)
        print(f"Stats Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Blog Statistics:")
            print(f"   Total blogs: {stats['total_blogs']}")
            print(f"   Published: {stats['published_blogs']}")
            print(f"   Drafts: {stats['draft_blogs']}")
            print(f"   Total views: {stats['total_views']}")
        
        # Step 6: Test public blog access
        print("\n=== Step 6: Test Public Blog Access ===")
        response = requests.get(PUBLIC_BLOGS_URL)  # No auth required
        print(f"Public Blogs Status: {response.status_code}")
        
        if response.status_code == 200:
            public_blogs = response.json()
            print(f"✅ Public blogs available: {public_blogs['count']}")
            if public_blogs['results']:
                print("   Published blogs:")
                for blog in public_blogs['results'][:3]:
                    print(f"     - {blog['title']} by {blog['author_name']}")
        
        # Step 7: View specific blog (public)
        if blog['status'] == 'published':
            print(f"\n=== Step 7: View Specific Blog ===")
            response = requests.get(f"{PUBLIC_BLOGS_URL}{updated_blog['slug']}/")
            print(f"Blog Detail Status: {response.status_code}")
            
            if response.status_code == 200:
                blog_detail = response.json()
                print(f"✅ Blog viewed: {blog_detail['title']}")
                print(f"   Views: {blog_detail['view_count']}")
                print(f"   Author: {blog_detail['author_name']}")
        
        # Step 8: Delete the blog (cleanup)
        print("\n=== Step 8: Delete Blog (Cleanup) ===")
        response = requests.delete(f"{TEACHER_BLOGS_URL}{blog_id}/", headers=headers)
        print(f"Blog Deletion Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_blog_filtering_and_search():
    """Test blog filtering and search functionality"""
    
    print("\n" + "="*60)
    print("=== Testing Blog Filtering and Search ===")
    
    # Test public blog filtering
    test_params = [
        {"search": "language"},
        {"category": "1"},
        {"tags": "education,tips"},
    ]
    
    for params in test_params:
        print(f"\n--- Testing filter: {params} ---")
        response = requests.get(PUBLIC_BLOGS_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} blogs")
        else:
            print(f"❌ Filter failed: {response.status_code}")

def show_api_endpoints():
    """Show all available blog API endpoints"""
    
    print("\n" + "="*60)
    print("=== Available Blog API Endpoints ===")
    
    endpoints = [
        ("POST", "/api/teacher/blogs/", "Create new blog"),
        ("GET", "/api/teacher/blogs/", "List teacher's blogs"),
        ("GET", "/api/teacher/blogs/{id}/", "Get specific blog"),
        ("PUT/PATCH", "/api/teacher/blogs/{id}/", "Update blog"),
        ("DELETE", "/api/teacher/blogs/{id}/", "Delete blog"),
        ("GET", "/api/teacher/blogs/stats/", "Get blog statistics"),
        ("POST", "/api/teacher/blogs/{id}/duplicate/", "Duplicate blog"),
        ("POST", "/api/teacher/blogs/bulk-update/", "Bulk update blog status"),
        ("GET", "/api/blogs/", "List published blogs (public)"),
        ("GET", "/api/blogs/{slug}/", "View blog by slug (public)"),
        ("GET", "/api/categories/", "List categories"),
        ("POST", "/api/categories/", "Create category"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"{method:10} {endpoint:35} - {description}")

def show_example_blog_data():
    """Show example data formats for blog creation"""
    
    print("\n" + "="*60)
    print("=== Example Blog Data Format ===")
    
    example_blog = {
        "title": "Your Blog Title Here",
        "content": "Your detailed blog content here...",
        "thumbnail": "https://example.com/image.jpg",
        "category": 1,  # Category ID
        "tags": ["tag1", "tag2", "tag3"],
        "status": "draft",  # or "published" or "archived"
        "meta_description": "SEO description for your blog"
    }
    
    print(json.dumps(example_blog, indent=2))
    
    print("\n=== Blog Status Options ===")
    print("- draft: Blog is not visible to public")
    print("- published: Blog is visible to everyone")
    print("- archived: Blog is hidden but kept for reference")

if __name__ == "__main__":
    print("Blog Management System - Test Suite")
    print("Update the teacher_token variable with a valid teacher token before running")
    print("="*60)
    
    # Show available endpoints
    show_api_endpoints()
    
    # Show example data
    show_example_blog_data()
    
    print(f"\n{'='*60}")
    print("Setup Instructions:")
    print("1. Update the teacher_token with a valid teacher access token")
    print("2. Ensure Django server is running: python manage.py runserver")
    print("3. Ensure you have a teacher profile in the system")
    print("4. Uncomment the test function calls below to run tests")
    print("="*60)
    
    # Uncomment to run actual tests (after setting teacher token)
    # test_blog_crud_operations()
    # test_blog_filtering_and_search()
