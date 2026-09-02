"""
Django management command: check_auth_users
Safely audits and reports all users in the PostgreSQL auth_user table.
Reports username, email, is_active, has_usable_password, and password hasher algorithm.
DOES NOT print raw passwords or password hashes.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import identify_hasher
from django.db import connection


class Command(BaseCommand):
    help = "Safely checks and reports authentication readiness of all users in PostgreSQL auth_user table."

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.MIGRATE_HEADING("CLOUDOpt.AI — PostgreSQL Authentication & User Diagnostic"))
        self.stdout.write("=" * 80)

        # Database Connection Info
        db_settings = connection.settings_dict
        self.stdout.write(f"Database Engine: {db_settings.get('ENGINE')}")
        self.stdout.write(f"Database Name:   {db_settings.get('NAME')}")
        self.stdout.write(f"Database Host:   {db_settings.get('HOST') or 'localhost'}")
        self.stdout.write(f"Database Port:   {db_settings.get('PORT') or '5432'}")
        self.stdout.write(f"Database User:   {db_settings.get('USER')}")
        self.stdout.write("-" * 80)

        users = User.objects.all().order_by('id')
        total_count = users.count()
        self.stdout.write(f"Total Users Found in auth_user: {total_count}\n")

        if total_count == 0:
            self.stdout.write(self.style.WARNING("No users found in the database."))
            return

        header = f"{'ID':<4} | {'Username':<22} | {'Email':<30} | {'Active':<6} | {'Usable PW':<9} | {'Password Hasher':<20}"
        self.stdout.write(self.style.SUCCESS(header))
        self.stdout.write("-" * len(header))

        valid_count = 0
        invalid_count = 0

        for user in users:
            pw = user.password or ''
            hasher_name = 'NONE'
            is_valid_hasher = False

            if pw:
                try:
                    hasher = identify_hasher(pw)
                    hasher_name = hasher.algorithm
                    is_valid_hasher = True
                except Exception as err:
                    hasher_name = f"INVALID ({type(err).__name__})"
                    is_valid_hasher = False

            usable = user.has_usable_password()

            if usable and is_valid_hasher:
                valid_count += 1
                status_color = self.style.SUCCESS
            else:
                invalid_count += 1
                status_color = self.style.ERROR

            line = f"{user.id:<4} | {user.username:<22} | {user.email or '(none)':<30} | {str(user.is_active):<6} | {str(usable):<9} | {hasher_name:<20}"
            self.stdout.write(status_color(line))

        self.stdout.write("-" * 80)
        self.stdout.write(f"Summary: {valid_count} ready to authenticate, {invalid_count} need password reset.")
        self.stdout.write("=" * 80)
