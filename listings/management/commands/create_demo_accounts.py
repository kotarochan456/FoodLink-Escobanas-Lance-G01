"""Opt-in accounts for a disposable development database, never auto-created."""
import getpass
import os
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import User

class Command(BaseCommand):
    help = 'Create three PD2 test accounts in a development database. Refuses to overwrite users.'

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true')

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Demo accounts are only allowed with DJANGO_DEBUG=True.')
        password = os.environ.get('FOODLINK_DEMO_PASSWORD')
        if not password and not options['noinput']:
            password = getpass.getpass('Test password for the three demo accounts: ')
            if password != getpass.getpass('Confirm test password: '):
                raise CommandError('Passwords do not match.')
        if not password:
            raise CommandError('Provide a password interactively or set FOODLINK_DEMO_PASSWORD.')
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError(' '.join(exc.messages)) from exc
        roles = [('pd2_donor',User.Role.DONOR),('pd2_recipient',User.Role.RECIPIENT),('pd2_admin',User.Role.ADMIN)]
        with transaction.atomic():
            if User.objects.filter(username__in=[name for name, _ in roles]).exists():
                raise CommandError('A PD2 demo username already exists. No accounts were changed.')
            for name, role in roles:
                if User.objects.filter(email__iexact=name+'@example.com').exists():
                    raise CommandError('A PD2 demo email already exists. No accounts were changed.')
                User.objects.create_user(username=name,email=name+'@example.com',password=password,
                    first_name='Demo',last_name=role.title(),contact_number='09900000000',
                    location='Demo community hall',role=role)
        self.stdout.write(self.style.SUCCESS('Created pd2_donor, pd2_recipient and pd2_admin. None has Django staff access.'))
