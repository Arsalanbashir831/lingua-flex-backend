#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from accounts.models import Gig

print("Checking existing Gig data...")
print("=" * 50)

gigs = Gig.objects.all()
print(f"Total gigs: {gigs.count()}")

for gig in gigs:
    print(f"\nGig ID: {gig.id}")
    print(f"Service Title: {gig.service_title}")
    print(f"What you provide: '{gig.what_you_provide_in_session}'")
    print(f"Type: {type(gig.what_you_provide_in_session)}")
    print("-" * 30)

print("\nData check complete!")
