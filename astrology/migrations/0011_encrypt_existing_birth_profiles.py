from django.db import migrations

def encrypt_existing_birth_profiles(apps, schema_editor):
    BirthProfile = apps.get_model('astrology', 'BirthProfile')
    # Fetching and saving each profile will trigger the 'get_prep_value' 
    # logic of the new Encrypted fields, effectively encrypting the raw
    # data that was converted to Text/Varchar during migrate 0010.
    for profile in BirthProfile.objects.all():
        profile.save()

class Migration(migrations.Migration):
    dependencies = [
        ('astrology', '0010_alter_birthprofile_birth_day_and_more'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing_birth_profiles, reverse_code=migrations.RunPython.noop),
    ]
