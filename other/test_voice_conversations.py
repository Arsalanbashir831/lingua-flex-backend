"""
Test script for Voice Conversation endpoints
Tests all CRUD operations and special actions for OpenAI speech-to-speech conversations
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
VOICE_CONVERSATIONS_URL = f"{BASE_URL}/accounts/voice-conversations/"

def test_voice_conversation_endpoints():
    """Test all voice conversation endpoints"""
    
    # You'll need to provide a valid access token
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Voice Conversation Endpoints")
    print(f"Base URL: {VOICE_CONVERSATIONS_URL}")
    print("="*60)
    
    try:
        # Test 1: Create a new voice conversation
        print("\n=== Test 1: Create Voice Conversation ===")
        
        conversation_data = {
            "topic": "Ordering Food at a Restaurant",
            "transcription": "User: Hi, I'd like to make a reservation for two people tonight at 7 PM. AI: Certainly! I'd be happy to help you with that reservation. May I have your name please? User: My name is John Smith. AI: Thank you, Mr. Smith. Let me check our availability for tonight at 7 PM for two people.",
            "native_language": "English",
            "target_language": "Spanish",
            "conversation_type": "practice",
            "duration_minutes": 15,
            "ai_feedback": {
                "grammar_score": 85,
                "pronunciation_score": 78,
                "vocabulary_usage": "Good use of restaurant vocabulary",
                "areas_for_improvement": ["Practice rolling R sounds", "Work on subjunctive mood"]
            }
        }
        
        response = requests.post(VOICE_CONVERSATIONS_URL, json=conversation_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        created_conversation = None
        if response.status_code == 201:
            created_conversation = response.json()
            print("✅ Conversation created successfully!")
            print(f"ID: {created_conversation['id']}")
            print(f"Topic: {created_conversation['topic']}")
            print(f"Target Language: {created_conversation['target_language']}")
            print(f"Type: {created_conversation['conversation_type_display']}")
        else:
            print(f"❌ Failed to create conversation: {response.text}")
            return
        
        # Test 2: Get all conversations
        print(f"\n=== Test 2: Get All Conversations ===")
        response = requests.get(VOICE_CONVERSATIONS_URL, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ Retrieved {len(conversations)} conversations")
            
            if conversations:
                sample = conversations[0]
                print("Sample conversation fields:")
                for key in sample.keys():
                    print(f"  - {key}: {type(sample[key]).__name__}")
        else:
            print(f"❌ Failed to retrieve conversations: {response.text}")
        
        # Test 3: Get specific conversation
        print(f"\n=== Test 3: Get Specific Conversation ===")
        if created_conversation:
            conversation_id = created_conversation['id']
            detail_url = f"{VOICE_CONVERSATIONS_URL}{conversation_id}/"
            response = requests.get(detail_url, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                conversation = response.json()
                print("✅ Retrieved conversation details!")
                print(f"Topic: {conversation['topic']}")
                print(f"Transcription length: {len(conversation['transcription'])} characters")
                print(f"AI Feedback keys: {list(conversation['ai_feedback'].keys())}")
            else:
                print(f"❌ Failed to retrieve conversation: {response.text}")
        
        # Test 4: Update conversation (add more AI feedback)
        print(f"\n=== Test 4: Update AI Feedback ===")
        if created_conversation:
            conversation_id = created_conversation['id']
            feedback_url = f"{VOICE_CONVERSATIONS_URL}{conversation_id}/add_feedback/"
            
            additional_feedback = {
                "ai_feedback": {
                    "conversation_flow": "Natural and engaging",
                    "confidence_level": "Intermediate",
                    "suggested_next_topics": ["Describing food preferences", "Making complaints"]
                }
            }
            
            response = requests.patch(feedback_url, json=additional_feedback, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ AI feedback updated successfully!")
                print(f"Message: {result['message']}")
                print(f"Updated feedback keys: {list(result['conversation']['ai_feedback'].keys())}")
            else:
                print(f"❌ Failed to update feedback: {response.text}")
        
        # Test 5: Get conversations by language
        print(f"\n=== Test 5: Filter by Target Language ===")
        language_url = f"{VOICE_CONVERSATIONS_URL}by-language/Spanish/"
        response = requests.get(language_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            spanish_conversations = response.json()
            print(f"✅ Found {len(spanish_conversations)} Spanish conversations")
        else:
            print(f"❌ Failed to filter by language: {response.text}")
        
        # Test 6: Get conversations by type
        print(f"\n=== Test 6: Filter by Conversation Type ===")
        type_url = f"{VOICE_CONVERSATIONS_URL}by-type/practice/"
        response = requests.get(type_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            practice_conversations = response.json()
            print(f"✅ Found {len(practice_conversations)} practice conversations")
        else:
            print(f"❌ Failed to filter by type: {response.text}")
        
        # Test 7: Get summary statistics
        print(f"\n=== Test 7: Get Summary Statistics ===")
        summary_url = f"{VOICE_CONVERSATIONS_URL}summary/"
        response = requests.get(summary_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            summary = response.json()
            print("✅ Retrieved summary statistics!")
            print(f"Total conversations: {summary['total_conversations']}")
            print(f"Total duration: {summary['total_duration_minutes']} minutes")
            print(f"Languages practiced: {list(summary['conversations_by_language'].keys())}")
            print(f"Conversation types: {list(summary['conversations_by_type'].keys())}")
            print(f"Recent conversations (7 days): {summary['recent_conversations_last_7_days']}")
        else:
            print(f"❌ Failed to get summary: {response.text}")
        
        # Test 8: Create another conversation with different data
        print(f"\n=== Test 8: Create Another Conversation ===")
        
        conversation_data_2 = {
            "topic": "Job Interview Preparation",
            "transcription": "User: Tell me about yourself. AI: That's a great question to start with. When answering this question, you should focus on your professional background and relevant skills. User: I have worked in marketing for three years and I'm passionate about digital campaigns.",
            "native_language": "English", 
            "target_language": "French",
            "conversation_type": "lesson",
            "duration_minutes": 20
        }
        
        response = requests.post(VOICE_CONVERSATIONS_URL, json=conversation_data_2, headers=headers)
        
        if response.status_code == 201:
            print("✅ Second conversation created successfully!")
            # Get updated summary
            response = requests.get(summary_url, headers=headers)
            if response.status_code == 200:
                updated_summary = response.json()
                print(f"Updated total conversations: {updated_summary['total_conversations']}")
                print(f"Updated total duration: {updated_summary['total_duration_minutes']} minutes")
        
        # Test 9: Test validation errors
        print(f"\n=== Test 9: Test Validation Errors ===")
        
        invalid_data = {
            "topic": "",  # Empty topic
            "transcription": "",  # Empty transcription
            "native_language": "English",
            "target_language": "Spanish",
            "conversation_type": "practice"
        }
        
        response = requests.post(VOICE_CONVERSATIONS_URL, json=invalid_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            errors = response.json()
            print("✅ Validation working correctly!")
            print(f"Validation errors: {errors}")
        else:
            print(f"⚠️  Expected validation error, got: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_conversation_types():
    """Test all available conversation types"""
    
    print("\n" + "="*60)
    print("=== Available Conversation Types ===")
    
    conversation_types = [
        ("practice", "Language Practice"),
        ("lesson", "Language Lesson"),
        ("conversation", "Free Conversation"),
        ("assessment", "Language Assessment"),
        ("pronunciation", "Pronunciation Practice"),
        ("vocabulary", "Vocabulary Building"),
        ("grammar", "Grammar Practice")
    ]
    
    for value, label in conversation_types:
        print(f"'{value}': {label}")
    
    print("\n=== Sample Request Bodies ===")
    
    samples = [
        {
            "name": "Language Practice Session",
            "data": {
                "topic": "Talking about hobbies and interests",
                "transcription": "Full conversation transcription here...",
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "practice",
                "duration_minutes": 10
            }
        },
        {
            "name": "Pronunciation Practice",
            "data": {
                "topic": "Practicing difficult sounds in Spanish",
                "transcription": "Pronunciation practice session transcription...",
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "pronunciation",
                "duration_minutes": 8,
                "ai_feedback": {
                    "pronunciation_score": 75,
                    "sounds_to_practice": ["rr", "ñ", "ll"]
                }
            }
        }
    ]
    
    for sample in samples:
        print(f"\n{sample['name']}:")
        print(json.dumps(sample['data'], indent=2))

if __name__ == "__main__":
    print("=== Voice Conversation Endpoints Testing ===")
    
    print("\nThis test suite covers:")
    print("- Creating voice conversations")
    print("- Retrieving conversations (all, by language, by type)")
    print("- Updating AI feedback")
    print("- Getting summary statistics")
    print("- Validation testing")
    
    print("\n" + "="*60)
    print("Setup Instructions:")
    print("1. Update the access_token variable with a valid token")
    print("2. Ensure Django server is running: python manage.py runserver")
    print("3. Ensure VoiceConversation migration has been applied")
    print("="*60)
    
    # Show conversation types and examples
    test_conversation_types()
    
    print(f"\n{'='*60}")
    print("To run the actual tests, uncomment the function call below:")
    print("# test_voice_conversation_endpoints()")
    
    # Uncomment to run actual tests (after setting token)
    # test_voice_conversation_endpoints()
