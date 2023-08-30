import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipe.models import Ingredient, Tag

MODEL_CSV = {
    'ingredients.csv': Ingredient,
    'tags.csv': Tag,
}


class Command(BaseCommand):
    """Загрузчик данных с csv-файла."""

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.HTTP_INFO('Загрузка в базы данных началась'),
        )
        for file, model in MODEL_CSV.items():
            csv_file = os.path.join(
                os.path.join(settings.BASE_DIR, 'data'),
                file,
            )
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    if model == Ingredient:
                        for row in reader:
                            name, measurement_unit = row
                            model.objects.get_or_create(
                                name=name,
                                measurement_unit=measurement_unit,
                            )
                    else:
                        for row in reader:
                            name, color, slug = row
                            model.objects.get_or_create(
                                name=name,
                                color=color,
                                slug=slug,
                            )
            except FileNotFoundError:
                raise CommandError('Не найден файл с данными!')
        self.stdout.write(
            self.style.SUCCESS('Данные из .csv ' 'файлов загружены успешно!'),
        )
