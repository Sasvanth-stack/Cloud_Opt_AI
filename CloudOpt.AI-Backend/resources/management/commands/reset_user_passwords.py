"""
Django management command: reset_user_passwords
Safely sets or resets passwords for users using Django's built-in user.set_password() and user.save().
Ensures all passwords in PostgreSQL auth_user are valid, standard Django password hashes (e.g. pbkdf2_sha256).
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import identify_hasher


class Command(BaseCommand):
    help = "Safely sets a valid Django password hash for a user using user.set_password()."

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the user whose password should be updated.'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user whose password should be updated.'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Password2026!',
            help='New password to set (defaults to Password2026!).'
        )
        parser.add_argument(
            '--fix-invalid',
            action='store_true',
            help='Automatically detect all users with invalid password hashes and update them to a valid Django hash.'
        )
        parser.add_argument(
            '--trim-whitespace',
            action='store_true',
            help='Trim leading and trailing whitespace from all usernames and emails in auth_user.'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        password = options.get('password') or 'Password2026!'
        fix_invalid = options.get('fix_invalid')
        trim_whitespace = options.get('trim_whitespace')

        if trim_whitespace:
            self.stdout.write("Trimming whitespace from usernames and emails...")
            trimmed_count = 0
            for u in User.objects.all():
                clean_username = u.username.strip()
                clean_email = (u.email or '').strip().lower()
                if clean_username != u.username or clean_email != (u.email or ''):
                    self.stdout.write(f"Trimmed User ID {u.id}: '{u.username}' -> '{clean_username}', '{u.email}' -> '{clean_email}'")
                    u.username = clean_username
                    u.email = clean_email
                    u.save(update_fields=['username', 'email'])
                    trimmed_count += 1
            self.stdout.write(self.style.SUCCESS(f"Finished trimming. Updated {trimmed_count} user(s)."))
            return

        if fix_invalid:
            self.stdout.write("Scanning for users with invalid or unhashed passwords...")
            fixed_count = 0
            for user in User.objects.all():
                is_invalid = False
                pw = user.password or ''
                if not pw:
                    is_invalid = True
                else:
                    try:
                        identify_hasher(pw)
                    except Exception:
                        is_invalid = True

                if is_invalid:
                    user.set_password(password)
                    user.save()
                    fixed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Fixed user '{user.username}' ({user.email}): Set valid Django password hash using set_password()."
                        )
                    )

            if fixed_count == 0:
                self.stdout.write(self.style.SUCCESS("All users already have valid Django password hashes."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Successfully fixed {fixed_count} user(s)."))
            return

        if not username and not email:
            self.stdout.write(
                self.style.ERROR("Please provide either --username, --email, or --fix-invalid.")
            )
            return

        user = None
        if username:
            user = User.objects.filter(username__iexact=username).first()
        if not user and email:
            user = User.objects.filter(email__iexact=email).first()

        if not user:
            self.stdout.write(self.style.ERROR(f"User not found with username='{username}' or email='{email}'."))
            return

        # Safely set password using Django ORM
        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Password for user '{user.username}' ({user.email}) successfully updated with valid Django hash."
            )
        )
