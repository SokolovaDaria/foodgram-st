import json
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Loads ingredients from a JSON or CSV file into the database'

    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
    DATA_DIR = BASE_DIR / 'data'
    DEFAULT_JSON_FILE = DATA_DIR / 'ingredients.json'
    DEFAULT_CSV_FILE = DATA_DIR / 'ingredients.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jsonfile',
            type=str,
            default=str(self.DEFAULT_JSON_FILE),
            help='Path to the JSON file containing ingredients',
        )
        parser.add_argument(
            '--csvfile',
            type=str,
            default=str(self.DEFAULT_CSV_FILE),
            help='Path to the CSV file containing ingredients',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default=None, 
            help='Specify file format (json or csv)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        json_file_path = Path(options['jsonfile'])
        csv_file_path = Path(options['csvfile'])
        file_format = options['format']

        file_path = None
        actual_format = None

        if file_format == 'json' or (not file_format and json_file_path.exists()):
            file_path = json_file_path
            actual_format = 'json'
        elif file_format == 'csv' or (not file_format and csv_file_path.exists()):
            file_path = csv_file_path
            actual_format = 'csv'
        elif not file_format and not json_file_path.exists() and not csv_file_path.exists():
             raise CommandError(f"Neither JSON ({json_file_path}) nor CSV ({csv_file_path}) file found.")
        elif file_format and not file_path.exists():
             raise CommandError(f"Specified {file_format.upper()} file not found at: {file_path}")


        if not file_path or not actual_format:
             raise CommandError("Could not determine the data file to load.")


        self.stdout.write(self.style.SUCCESS(f'Starting to load ingredients from {file_path} (Format: {actual_format})...'))

        ingredients_to_create = []
        loaded_count = 0
        skipped_count = 0

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                if actual_format == 'json':
                    data = json.load(f)
                     
                    if not isinstance(data, list):
                        raise CommandError("JSON file should contain a list of ingredient objects.")

                    for item in data:
                        name = item.get('name')
                        unit = item.get('measurement_unit')
                        if name and unit:
                           
                            if not Ingredient.objects.filter(name__iexact=name, measurement_unit__iexact=unit).exists():
                                ingredients_to_create.append(Ingredient(name=name, measurement_unit=unit))
                                loaded_count += 1
                            else:
                                skipped_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"Skipping invalid JSON item: {item}"))

                elif actual_format == 'csv':
                    reader = csv.reader(f)
                  
                    for row in reader:
                        if len(row) >= 2:
                            name = row[0].strip()
                            unit = row[1].strip()
                            if name and unit:
                                
                                if not Ingredient.objects.filter(name__iexact=name, measurement_unit__iexact=unit).exists():
                                    ingredients_to_create.append(Ingredient(name=name, measurement_unit=unit))
                                    loaded_count += 1
                                else:
                                     skipped_count += 1
                            else:
                                 self.stdout.write(self.style.WARNING(f"Skipping invalid CSV row: {row}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"Skipping incomplete CSV row: {row}"))

            
            Ingredient.objects.bulk_create(ingredients_to_create)

            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {loaded_count} new ingredients.'))
            if skipped_count > 0:
                 self.stdout.write(self.style.WARNING(f'Skipped {skipped_count} ingredients that already exist.'))

        except FileNotFoundError:
            raise CommandError(f'Error: File not found at {file_path}')
        except json.JSONDecodeError:
            raise CommandError(f'Error: Could not decode JSON from {file_path}')
        except IntegrityError as e:
            
            self.stdout.write(self.style.ERROR(f'Database integrity error during loading: {e}'))
            self.stdout.write(self.style.WARNING('Consider running again or checking data for duplicates (case-sensitive).'))
        except Exception as e:
            raise CommandError(f'An unexpected error occurred: {e}')