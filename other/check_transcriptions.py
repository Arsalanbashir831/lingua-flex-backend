#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from accounts.models import VoiceConversation

print("Checking existing VoiceConversation transcription data...")
print(f"Total VoiceConversation records: {VoiceConversation.objects.count()}")
print()

for i, vc in enumerate(VoiceConversation.objects.all()[:5], 1):
    print(f"Record {i}:")
    print(f"  ID: {vc.id}")
    print(f"  Topic: {vc.topic}")
    print(f"  Transcription type: {type(vc.transcription)}")
    print(f"  Transcription preview: {repr(vc.transcription[:100])}...")
    print()
