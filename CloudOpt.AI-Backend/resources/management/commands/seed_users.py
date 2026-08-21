from typing import TypedDict
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from resources.permissions import (
    ROLE_ADMIN,
    ROLE_DEVOPS,
    ROLE_FINOPS,
    ROLE_SRE,
    ROLE_VIEWER,
    VALID_ROLES,
    assign_user_role
)


class DemoUser(TypedDict):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    role: str
    is_superuser: bool
    is_staff: bool


DEMO_USERS: list[DemoUser] = [
    {
        "username": "admin",
        "email": "admin@cloudopt.ai",
        "password": "Admin@CloudOpt2026",
        "first_name": "Cloud",
        "last_name": "Administrator",
        "role": ROLE_ADMIN,
        "is_superuser": True,
        "is_staff": True,
    },
    {
        "username": "devops",
        "email": "devops@cloudopt.ai",
        "password": "DevOps@CloudOpt2026",
        "first_name": "DevOps",
        "last_name": "Lead",
        "role": ROLE_DEVOPS,
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "username": "finops",
        "email": "finops@cloudopt.ai",
        "password": "FinOps@CloudOpt2026",
        "first_name": "FinOps",
        "last_name": "Analyst",
        "role": ROLE_FINOPS,
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "username": "sre",
        "email": "sre@cloudopt.ai",
        "password": "Sre@CloudOpt2026",
        "first_name": "SRE",
        "last_name": "Specialist",
        "role": ROLE_SRE,
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "username": "viewer",
        "email": "viewer@cloudopt.ai",
        "password": "Viewer@CloudOpt2026",
        "first_name": "Auditor",
        "last_name": "Manager",
        "role": ROLE_VIEWER,
        "is_superuser": False,
        "is_staff": False,
    },
]


class Command(BaseCommand):
    help = 'Seeds initial demonstration users and RBAC groups for CloudOpt.AI.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing RBAC groups..."))

        # 1. Ensure all RBAC groups exist
        for role_name in VALID_ROLES:
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created Group: {role_name}"))
            else:
                self.stdout.write(f"  Group exists: {role_name}")

        # 2. Create or update demo users
        self.stdout.write(self.style.NOTICE("\nProvisioning demo users with secure password hashing..."))

        for udata in DEMO_USERS:
            username = udata["username"]
            email = udata["email"]
            password = udata["password"]
            role = udata["role"]

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": udata["first_name"],
                    "last_name": udata["last_name"],
                    "is_active": True,
                    "is_staff": udata["is_staff"],
                    "is_superuser": udata["is_superuser"]
                }
            )

            # Update password securely
            user.set_password(password)
            user.email = email
            user.first_name = udata["first_name"]
            user.last_name = udata["last_name"]
            user.is_active = True
            user.is_staff = udata["is_staff"]
            user.is_superuser = udata["is_superuser"]
            user.save()

            assign_user_role(user, role)

            action_desc = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {action_desc} User: {username} (Role: {role}, Email: {email})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS("\nSuccessfully seeded all demo users and RBAC groups for CloudOpt.AI!")
        )
