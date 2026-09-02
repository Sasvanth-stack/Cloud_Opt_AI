"""
Management command to safely check Google OAuth configuration status without leaking credentials.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from resources.google_auth_service import (
    get_google_client_id,
    get_google_client_secret,
    get_google_redirect_uri,
    reload_credentials_if_needed
)


class Command(BaseCommand):
    help = 'Safely checks Google OAuth configuration status without revealing secrets.'

    def handle(self, *args, **options):
        reload_credentials_if_needed()
        cid = get_google_client_id()
        csec = get_google_client_secret()
        uri = get_google_redirect_uri()

        self.stdout.write(self.style.NOTICE("Checking Google OAuth configuration in backend/.env:"))
        self.stdout.write(f"  GOOGLE_CLIENT_ID: {'CONFIGURED' if cid else 'MISSING'}")
        self.stdout.write(f"  GOOGLE_CLIENT_SECRET: {'CONFIGURED' if csec else 'MISSING'}")
        self.stdout.write(f"  GOOGLE_OAUTH_REDIRECT_URI: {'CONFIGURED' if uri else 'MISSING'}")
        self.stdout.write(f"  Redirect URI: {uri}")

        if cid and csec:
            self.stdout.write(self.style.SUCCESS("\n[OK] Google OAuth is fully configured and ready!"))
        else:
            self.stdout.write(self.style.WARNING("\n[WARNING] Please ensure GOOGLE_CLIENT_SECRET is set in backend/.env."))
