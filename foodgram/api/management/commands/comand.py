import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe.models import Ingredient


class Command(BaseCommand):
    """Загрузчик данных с csv-файла."""

    def handle(self, *args, **options):
        csv_file = os.path.join(
            os.path.join(settings.BASE_DIR, 'data'), 'ingredients.csv',
        )
        with open(csv_file, 'r', encoding='utf-8') as f:
            fieldnames = ['name', 'measurement_unit']
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                print(row)
                Ingredient.objects.get_or_create(
                    name=row['name'], measurement_unit=row['measurement_unit'],
                )
        self.stdout.write(
            self.style.SUCCESS('Данные из .csv ' 'файлов загружены успешно!'),
        )
