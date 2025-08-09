#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from accounts.models import VoiceConversation
import json

print("Verifying converted VoiceConversation transcription data...")
print(f"Total VoiceConversation records: {VoiceConversation.objects.count()}")
print()

for i, vc in enumerate(VoiceConversation.objects.all()[:3], 1):
    print(f"Record {i}:")
    print(f"  ID: {vc.id}")
    print(f"  Topic: {vc.topic}")
    print(f"  Transcription type: {type(vc.transcription)}")
    
    if isinstance(vc.transcription, dict):
        print(f"  JSON structure:")
        print(f"    - format: {vc.transcription.get('format', 'unknown')}")
        print(f"    - segments count: {len(vc.transcription.get('segments', []))}")
        print(f"    - has full_text: {'full_text' in vc.transcription}")
        print(f"    - metadata: {vc.transcription.get('metadata', {})}")
        
        # Show first segment if available
        segments = vc.transcription.get('segments', [])
        if segments:
            print(f"    - first segment: {segments[0]}")
    else:
        print(f"  Transcription preview: {repr(str(vc.transcription)[:100])}...")
    
    print()
