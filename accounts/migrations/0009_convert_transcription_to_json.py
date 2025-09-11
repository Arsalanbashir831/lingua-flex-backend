from django.db import migrations
import json


def convert_text_to_json(apps, schema_editor):
    """Convert existing text transcriptions to JSON format"""
    VoiceConversation = apps.get_model('accounts', 'VoiceConversation')
    
    for conversation in VoiceConversation.objects.all():
        # Convert text transcription to JSON format
        if isinstance(conversation.transcription, str):
            # Create a JSON structure from the existing text
            json_transcription = {
                "full_text": conversation.transcription,
                "format": "text",
                "segments": [],
                "metadata": {
                    "converted_from_text": True,
                    "original_format": "string"
                }
            }
            
            # Try to parse simple dialog format if it exists
            try:
                lines = conversation.transcription.strip().split('\n')
                segments = []
                for line in lines:
                    line = line.strip()
                    if line and ':' in line:
                        speaker, text = line.split(':', 1)
                        segments.append({
                            "speaker": speaker.strip(),
                            "text": text.strip(),
                            "timestamp": None
                        })
                
                if segments:
                    json_transcription["segments"] = segments
                    json_transcription["format"] = "dialog"
                    
            except Exception:
                # If parsing fails, just keep the full text
                pass
            
            # Update the field as a JSON string for now (before field type change)
            conversation.transcription = json.dumps(json_transcription)
            conversation.save()


def reverse_json_to_text(apps, schema_editor):
    """Reverse the conversion - extract full_text from JSON"""
    VoiceConversation = apps.get_model('accounts', 'VoiceConversation')
    
    for conversation in VoiceConversation.objects.all():
        try:
            # Parse JSON and extract full_text
            json_data = json.loads(conversation.transcription)
            conversation.transcription = json_data.get('full_text', conversation.transcription)
            conversation.save()
        except (json.JSONDecodeError, TypeError):
            # If it's already text or invalid JSON, leave as is
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_alter_voiceconversation_conversation_type'),
    ]

    operations = [
        migrations.RunPython(convert_text_to_json, reverse_json_to_text),
    ]
