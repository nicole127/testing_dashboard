from django.core.management import BaseCommand

from dashboard import views


class Command(BaseCommand):
    def handle(self, *args, **options):
        views.sync()
