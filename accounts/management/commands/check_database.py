from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = 'Verify PostgreSQL connectivity and the private foodlink schema before migrations.'
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_schema()')
            schema = cursor.fetchone()[0]
        if schema != 'foodlink':
            raise CommandError('Run supabase_setup.sql in Supabase SQL Editor first. Expected foodlink schema.')
        self.stdout.write(self.style.SUCCESS('PostgreSQL connected. foodlink schema is ready.'))
