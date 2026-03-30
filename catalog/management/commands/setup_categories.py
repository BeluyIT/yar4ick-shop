"""
Management command to set up Yar4ick Technology categories.
Clears old categories and creates new ones with subcategories.
Usage: python manage.py setup_categories
"""

from django.core.management.base import BaseCommand
from catalog.models import Category


CATEGORIES = [
    {
        'name': 'Смартфони',
        'slug': 'smartphones',
        'description': 'Смартфони провідних світових брендів',
        'children': [
            {'name': 'iPhone', 'slug': 'iphone', 'description': 'Apple iPhone всіх поколінь'},
            {'name': 'Samsung', 'slug': 'samsung', 'description': 'Samsung Galaxy серії S, A, Z'},
            {'name': 'Xiaomi', 'slug': 'xiaomi', 'description': 'Xiaomi, Redmi, POCO'},
            {'name': 'Інші бренди', 'slug': 'smartphones-other', 'description': 'OnePlus, Google Pixel, Realme та інші'},
        ]
    },
    {
        'name': 'Ноутбуки / ПК',
        'slug': 'laptops-pk',
        'description': 'Ноутбуки, настільні комп\'ютери та комплектуючі',
        'children': [
            {'name': 'Ноутбуки', 'slug': 'laptops', 'description': 'MacBook, ASUS, MSI, Lenovo, Dell та інші'},
            {'name': 'Комп\'ютери', 'slug': 'computers', 'description': 'Настільні ПК та моноблоки'},
            {'name': 'Комплектуючі', 'slug': 'components', 'description': 'Процесори, відеокарти, оперативна пам\'ять'},
        ]
    },
    {
        'name': 'Планшети',
        'slug': 'tablets',
        'description': 'Планшети для роботи, навчання та розваг',
        'children': [
            {'name': 'iPad', 'slug': 'ipad', 'description': 'Apple iPad всіх моделей'},
            {'name': 'Galaxy Tab', 'slug': 'galaxy-tab', 'description': 'Samsung Galaxy Tab серії S та A'},
            {'name': 'Інші планшети', 'slug': 'tablets-other', 'description': 'Lenovo, Xiaomi Pad та інші'},
        ]
    },
    {
        'name': 'Ігрові приставки',
        'slug': 'gaming',
        'description': 'Консолі Xbox, PlayStation, Nintendo та аксесуари',
        'children': [
            {'name': 'Xbox', 'slug': 'xbox', 'description': 'Xbox Series X|S, Xbox One та аксесуари Microsoft'},
            {'name': 'PlayStation', 'slug': 'playstation', 'description': 'PlayStation 5, PS4 та аксесуари Sony'},
            {'name': 'Nintendo', 'slug': 'nintendo', 'description': 'Nintendo Switch, Switch Lite, Switch OLED'},
        ]
    },
    {
        'name': 'Аксесуари та ігри',
        'slug': 'accessories',
        'description': 'Контролери, ігри, зарядки та захисні аксесуари',
        'children': [
            {'name': 'Контролери та геймпади', 'slug': 'controllers', 'description': 'Геймпади, джойстики, рулі'},
            {'name': 'Ігри', 'slug': 'games', 'description': 'Ігри для всіх платформ (диски та цифрові версії)'},
            {'name': 'Зарядки та кабелі', 'slug': 'chargers', 'description': 'Зарядні пристрої, кабелі, павербанки'},
            {'name': 'Чохли та захист', 'slug': 'cases', 'description': 'Чохли, скла, захисні плівки'},
        ]
    },
]


class Command(BaseCommand):
    help = 'Setup Yar4ick Technology categories (replaces old ones)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear ALL existing categories before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing all existing categories...')
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING('All categories deleted.'))

        created_count = 0
        updated_count = 0

        for cat_data in CATEGORIES:
            children = cat_data.pop('children', [])

            parent, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data.get('description', ''),
                    'is_active': True,
                }
            )
            if not created:
                parent.name = cat_data['name']
                parent.description = cat_data.get('description', '')
                parent.is_active = True
                parent.save()
                updated_count += 1
                self.stdout.write(f'  Updated: {parent.name}')
            else:
                created_count += 1
                self.stdout.write(f'  Created: {parent.name}')

            for child_data in children:
                child, child_created = Category.objects.get_or_create(
                    slug=child_data['slug'],
                    defaults={
                        'name': child_data['name'],
                        'description': child_data.get('description', ''),
                        'parent': parent,
                        'is_active': True,
                    }
                )
                if not child_created:
                    child.name = child_data['name']
                    child.description = child_data.get('description', '')
                    child.parent = parent
                    child.is_active = True
                    child.save()
                    updated_count += 1
                    self.stdout.write(f'    Updated: {child.name}')
                else:
                    created_count += 1
                    self.stdout.write(f'    Created: {child.name}')

            cat_data['children'] = children  # restore for idempotency

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}, Updated: {updated_count}'
        ))
        self.stdout.write(self.style.SUCCESS(
            'Yar4ick Technology categories are ready!'
        ))
