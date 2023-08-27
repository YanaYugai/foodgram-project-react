import os
from csv import DictReader

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe.models import Ingredient, Tag

MODEL_CSV = {
    'ingredients.csv': Ingredient,
    'tags.csv': Tag,
}


class Command(BaseCommand):
    """Загрузчик данных с csv-файла."""

    def handle(self, *args, **options):
        for csv, model in MODEL_CSV.items():
            csv_file = os.path.join(
                os.path.join(settings.BASE_DIR, 'data'),
                csv,
            )
            if model == Ingredient:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    fieldnames = ['name', 'measurement_unit']
                    reader = DictReader(f, fieldnames=fieldnames)
                    for row in reader:
                        model.objects.get_or_create(
                            name=row['name'],
                            measurement_unit=row['measurement_unit'],
                        )
            else:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    fieldnames = ['name', 'color', 'slug']
                    reader = DictReader(f, fieldnames=fieldnames)
                    for row in reader:
                        model.objects.get_or_create(
                            name=row['name'],
                            color=row['color'],
                            slug=row['slug'],
                        )
        self.stdout.write(
            self.style.SUCCESS('Данные из .csv ' 'файлов загружены успешно!'),
        )
