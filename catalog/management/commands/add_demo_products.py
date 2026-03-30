"""
Add demo products for Yar4ick Technology store.
Usage: python manage.py add_demo_products
"""
from django.core.management.base import BaseCommand
from catalog.models import Category, Product


PRODUCTS = [
    # Smartphones → iPhone
    {'category': 'iphone', 'name': 'Apple iPhone 15 128GB Black', 'sku': 'IPH15-128-BLK', 'price': 34999, 'is_popular': True, 'is_new': True,
     'description': 'iPhone 15 з чіпом A16 Bionic, камера 48 МП, Dynamic Island, USB-C.'},
    {'category': 'iphone', 'name': 'Apple iPhone 15 Pro 256GB Natural Titanium', 'sku': 'IPH15P-256-TI', 'price': 52999, 'is_popular': True, 'is_new': True,
     'description': 'iPhone 15 Pro з чіпом A17 Pro, ProMotion 120Hz, 3x телеоб\'єктив.'},
    {'category': 'iphone', 'name': 'Apple iPhone 14 128GB Starlight', 'sku': 'IPH14-128-STL', 'price': 27999, 'is_popular': False, 'is_new': False,
     'description': 'iPhone 14, чіп A15 Bionic, 12 МП основна камера, режим екшн.'},

    # Smartphones → Samsung
    {'category': 'samsung', 'name': 'Samsung Galaxy S24 256GB Phantom Black', 'sku': 'SGS24-256-BLK', 'price': 35999, 'is_popular': True, 'is_new': True,
     'description': 'Galaxy S24 з Snapdragon 8 Gen 3, 50 МП камера, 7 років оновлень.'},
    {'category': 'samsung', 'name': 'Samsung Galaxy A55 256GB Awesome Navy', 'sku': 'SGA55-256-NVY', 'price': 16499, 'is_popular': False, 'is_new': True,
     'description': 'Galaxy A55, AMOLED 120Hz, IP67, 50 МП Triple Camera.'},

    # Smartphones → Xiaomi
    {'category': 'xiaomi', 'name': 'Xiaomi 14 256GB Black', 'sku': 'XMI14-256-BLK', 'price': 29999, 'is_popular': True, 'is_new': True,
     'description': 'Xiaomi 14 з Leica камерою, Snapdragon 8 Gen 3, 90W зарядка.'},
    {'category': 'xiaomi', 'name': 'Redmi Note 13 Pro 256GB Midnight Black', 'sku': 'RN13P-256-BLK', 'price': 12999, 'is_popular': False, 'is_new': False,
     'description': 'Redmi Note 13 Pro, 200 МП камера, AMOLED 120Hz, 67W зарядка.'},

    # Laptops
    {'category': 'laptops', 'name': 'Apple MacBook Air 15" M3 256GB Space Gray', 'sku': 'MBA15-M3-256-SG', 'price': 62999, 'is_popular': True, 'is_new': True,
     'description': 'MacBook Air 15" з чіпом M3, 8GB RAM, 18 год. автономності, Liquid Retina.'},
    {'category': 'laptops', 'name': 'ASUS ROG Strix G16 RTX 4060 512GB', 'sku': 'AROG-G16-4060', 'price': 54999, 'is_popular': True, 'is_new': False,
     'description': 'Ігровий ноутбук ASUS ROG Strix, RTX 4060, i7-13650HX, 165Hz IPS.'},
    {'category': 'laptops', 'name': 'Lenovo IdeaPad 5 15" i5 512GB Blue', 'sku': 'LIP5-I5-512-BLU', 'price': 22999, 'is_popular': False, 'is_new': False,
     'description': 'Lenovo IdeaPad 5, Intel Core i5-12500H, 16GB RAM, IPS FHD.'},

    # Tablets → iPad
    {'category': 'ipad', 'name': 'Apple iPad Air 11" M2 256GB Wi-Fi Blue', 'sku': 'IPA11-M2-256-BLU', 'price': 32999, 'is_popular': True, 'is_new': True,
     'description': 'iPad Air з чіпом M2, Liquid Retina 11", підтримка Apple Pencil Pro.'},
    {'category': 'ipad', 'name': 'Apple iPad 10.9" 64GB Wi-Fi Silver', 'sku': 'IP109-64-SLV', 'price': 14999, 'is_popular': False, 'is_new': False,
     'description': 'iPad 10-го покоління, A14 Bionic, USB-C, Touch ID, 12 МП фронтальна.'},

    # Gaming → PlayStation
    {'category': 'playstation', 'name': 'Sony PlayStation 5 Slim 1TB Disc', 'sku': 'PS5-SLIM-1TB', 'price': 21999, 'is_popular': True, 'is_new': True,
     'description': 'PS5 Slim з дисководом, SSD 1TB, 4K 120fps, DualSense контролер.'},
    {'category': 'playstation', 'name': 'Sony DualSense Controller Midnight Black', 'sku': 'DS-CTRL-BLK', 'price': 3299, 'is_popular': False, 'is_new': False,
     'description': 'Бездротовий контролер DualSense з хаптичним зворотнім зв\'язком.'},

    # Gaming → Xbox
    {'category': 'xbox', 'name': 'Microsoft Xbox Series X 1TB', 'sku': 'XBX-SX-1TB', 'price': 19999, 'is_popular': True, 'is_new': False,
     'description': 'Xbox Series X, 4K 120fps, SSD 1TB, Game Pass Ultimate сумісний.'},
    {'category': 'xbox', 'name': 'Xbox Wireless Controller Carbon Black', 'sku': 'XBX-CTRL-BLK', 'price': 2299, 'is_popular': False, 'is_new': False,
     'description': 'Бездротовий контролер Xbox, Bluetooth, текстурований хват, USB-C.'},

    # Gaming → Nintendo
    {'category': 'nintendo', 'name': 'Nintendo Switch OLED White', 'sku': 'NSW-OLED-WHT', 'price': 12999, 'is_popular': True, 'is_new': False,
     'description': 'Nintendo Switch OLED з 7" екраном, Joy-Con, 64GB вбудованої пам\'яті.'},

    # Accessories
    {'category': 'controllers', 'name': 'GameSir T4 Pro Bluetooth Gamepad', 'sku': 'GSR-T4P-BT', 'price': 1899, 'is_popular': False, 'is_new': True,
     'description': 'Геймпад GameSir T4 Pro, Bluetooth 5.0, iOS/Android/PC/Switch.'},
    {'category': 'chargers', 'name': 'Apple MagSafe Charger 15W USB-C', 'sku': 'APL-MGSF-15W', 'price': 1499, 'is_popular': False, 'is_new': False,
     'description': 'MagSafe зарядка 15W для iPhone 12 і новіших, кабель 1м.'},
    {'category': 'cases', 'name': 'Spigen Ultra Hybrid iPhone 15 Crystal Clear', 'sku': 'SPG-UH-IP15-CLR', 'price': 699, 'is_popular': False, 'is_new': False,
     'description': 'Прозорий чохол Spigen для iPhone 15, захист від падінь, жовтіє.'},
]


class Command(BaseCommand):
    help = 'Add demo products to Yar4ick Technology store'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear all products first')

    def handle(self, *args, **options):
        if options['clear']:
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING('All products deleted.'))

        created = 0
        skipped = 0

        for p in PRODUCTS:
            try:
                cat = Category.objects.get(slug=p['category'])
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Category not found: {p['category']}"))
                skipped += 1
                continue

            obj, is_new = Product.objects.get_or_create(
                sku=p['sku'],
                defaults={
                    'name': p['name'],
                    'category': cat,
                    'price': p['price'],
                    'description': p['description'],
                    'is_popular': p.get('is_popular', False),
                    'is_new': p.get('is_new', False),
                    'is_available': True,
                }
            )
            if is_new:
                created += 1
                self.stdout.write(f'  + {obj.name}')
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created: {created}, Skipped (exist): {skipped}'))
