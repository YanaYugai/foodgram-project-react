import csv
from django.core.management.base import BaseCommand
from api.models import Ingridient
from pathlib import Path
import os
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        csv_file = os.path.join(os.path.join(settings.BASE_DIR, 'data'), 'ingredients.csv')
        """
        if not os.path.isfile(csv_file):
            print('file not found!')
            print(settings.BASE_DIR)
            print(csv_file)
            return
        """
        with open(csv_file, 'r', encoding='utf-8') as f:
            fieldnames = ['name', 'measurement_unit']
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                print(row)
                Ingridient.objects.get_or_create(name=row['name'], measurement_unit=row['measurement_unit'])
        self.stdout.write(self.style.SUCCESS('Данные из .csv '
                                             'файлов загружены успешно!'))
