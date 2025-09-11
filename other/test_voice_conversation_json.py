"""
Test script for VoiceConversation API with JSON transcription
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
VOICE_CONVERSATIONS_URL = f"{BASE_URL}/api/accounts/voice-conversations/"

def test_voice_conversation_with_json_transcription():
    """Test creating a voice conversation with JSON transcription"""
    
    # Your access token here
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    test_data = {
        "topic": "Ordering Food at a Restaurant",
        "transcription": {
            "full_text": "Complete conversation transcription...",
            "segments": [
                {
                    "speaker": "user", 
                    "text": "Hello, how are you?",
                    "timestamp": "00:00:05",
                    "confidence": 0.95
                },
                {
                    "speaker": "ai", 
                    "text": "I'm doing well, thank you!",
                    "timestamp": "00:00:08",
                    "confidence": 0.98
                }
            ],
            "language_analysis": {
                "detected_language": "en",
                "confidence": 0.99,
                "accent": "american"
            },
            "metadata": {
                "audio_quality": "high",
                "background_noise": "low",
                "total_words": 145
            }
        },
        "native_language": "English",
        "target_language": "Spanish",
        "conversation_type": "astrological",
        "duration_minutes": 15,
        "ai_feedback": {
            "grammar_score": 85,
            "pronunciation_score": 78,
            "vocabulary_usage": "Good use of restaurant vocabulary"
        }
    }
    
    print("Testing VoiceConversation API with JSON transcription...")
    print(f"URL: {VOICE_CONVERSATIONS_URL}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(VOICE_CONVERSATIONS_URL, json=test_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Successfully created voice conversation!")
            print(f"Created conversation ID: {result.get('id')}")
            print(f"Topic: {result.get('topic')}")
            print(f"Conversation Type: {result.get('conversation_type')}")
            print(f"Duration: {result.get('duration_minutes')} minutes")
            
            # Check transcription structure
            transcription = result.get('transcription', {})
            print(f"\nTranscription structure:")
            print(f"  - Format: {transcription.get('format', 'N/A')}")
            print(f"  - Segments count: {len(transcription.get('segments', []))}")
            print(f"  - Has full_text: {'full_text' in transcription}")
            print(f"  - Language analysis: {'language_analysis' in transcription}")
            print(f"  - Metadata: {'metadata' in transcription}")
            
        elif response.status_code == 400:
            error_data = response.json()
            print("❌ Validation Error:")
            for field, errors in error_data.items():
                print(f"  {field}: {errors}")
                
        elif response.status_code == 401:
            print("❌ Unauthorized: Invalid or missing token")
            
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_various_transcription_formats():
    """Test different transcription formats"""
    
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    test_cases = [
        {
            "name": "Minimal JSON transcription",
            "data": {
                "topic": "Test Conversation 1",
                "transcription": {
                    "full_text": "Hello, this is a test conversation."
                },
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "language"
            }
        },
        {
            "name": "Segments-only transcription",
            "data": {
                "topic": "Test Conversation 2",
                "transcription": {
                    "segments": [
                        {"speaker": "user", "text": "How do you say hello?"},
                        {"speaker": "ai", "text": "Hola"}
                    ]
                },
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "language"
            }
        },
        {
            "name": "String transcription (should be converted)",
            "data": {
                "topic": "Test Conversation 3",
                "transcription": "User: Hello!\nAI: Hi there!",
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "language"
            }
        }
    ]
    
    print("\n" + "="*60)
    print("Testing various transcription formats...")
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        try:
            response = requests.post(VOICE_CONVERSATIONS_URL, json=test_case['data'], headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Success! ID: {result.get('id')}")
                
                # Show transcription structure
                transcription = result.get('transcription', {})
                if isinstance(transcription, dict):
                    print(f"  Transcription type: dict")
                    print(f"  Keys: {list(transcription.keys())}")
                else:
                    print(f"  Transcription type: {type(transcription)}")
                    
            elif response.status_code == 400:
                error_data = response.json()
                print(f"❌ Validation errors: {error_data}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

def test_validation_errors():
    """Test validation error cases"""
    
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    error_cases = [
        {
            "name": "Empty transcription object",
            "data": {
                "topic": "Test",
                "transcription": {},
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "language"
            }
        },
        {
            "name": "Invalid segment format",
            "data": {
                "topic": "Test",
                "transcription": {
                    "segments": [
                        {"speaker": "user"}  # Missing 'text' field
                    ]
                },
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "language"
            }
        },
        {
            "name": "Empty string transcription",
            "data": {
                "topic": "Test",
                "transcription": "",
                "native_language": "English",
                "target_language": "Spanish",
                "conversation_type": "language"
            }
        }
    ]
    
    print("\n" + "="*60)
    print("Testing validation error cases...")
    
    for test_case in error_cases:
        print(f"\n--- {test_case['name']} ---")
        
        try:
            response = requests.post(VOICE_CONVERSATIONS_URL, json=test_case['data'], headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 400:
                error_data = response.json()
                print(f"✅ Expected validation error: {error_data}")
            else:
                print(f"❓ Unexpected response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("VoiceConversation API Test Suite")
    print("Update the access_token variable with a valid token before running")
    print("="*60)
    
    # Uncomment to run tests (after setting access token)
    # test_voice_conversation_with_json_transcription()
    # test_various_transcription_formats()
    # test_validation_errors()
    
    print("\nTo run tests:")
    print("1. Set valid access token in the test functions")
    print("2. Ensure Django server is running")
    print("3. Uncomment the test function calls at the bottom")
