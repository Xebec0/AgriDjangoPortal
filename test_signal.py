"""
Quick test to see if signals are working
Run: python manage.py shell < test_signal.py
"""
from django.contrib.auth.models import User
from core.models import Profile, UploadedFile

# Get a user
user = User.objects.first()
print(f"Testing with user: {user.username}")

# Get their profile
profile = user.profile
print(f"Profile ID: {profile.pk}")

# Check if profile has files
print(f"\nProfile files:")
print(f"  TOR: {profile.tor.name if profile.tor else 'None'}")
print(f"  NC2: {profile.nc2_tesda.name if profile.nc2_tesda else 'None'}")

# Check UploadedFile records
print(f"\nUploadedFile records for this user:")
records = UploadedFile.objects.filter(user=user)
print(f"  Total: {records.count()}")
print(f"  Active: {records.filter(is_active=True).count()}")

if records.exists():
    for r in records[:5]:
        print(f"    - {r.document_type}: {r.file_name} (active={r.is_active})")
else:
    print("  NO RECORDS FOUND - Signal is not working!")

# Try to manually trigger the signal
print(f"\n--- Manually triggering signal ---")
from core.signals import track_profile_files
from django.db.models.signals import post_save

# Manually call the signal
print("Calling track_profile_files manually...")
try:
    track_profile_files(sender=Profile, instance=profile, created=False)
    print("Signal executed!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Check records again
print(f"\nAfter manual trigger:")
records = UploadedFile.objects.filter(user=user)
print(f"  Total: {records.count()}")
print(f"  Active: {records.filter(is_active=True).count()}")
