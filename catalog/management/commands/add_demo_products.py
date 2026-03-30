"""
Add demo products for Yar4ick Technology store.
Usage: python manage.py add_demo_products
"""
from django.core.management.base import BaseCommand
from catalog.models import Category, Product


PRODUCTS = [
    # iPhone
    {'category': 'iphone', 'slug': 'iphone-15-128-black', 'name': 'Apple iPhone 15 128GB Black',
     'sku': 'IPH15-128-BLK', 'price': 34999, 'is_popular': True, 'is_new': True,
     'description': 'iPhone 15 з чіпом A16 Bionic, камера 48 МП, Dynamic Island, USB-C.'},
    {'category': 'iphone', 'slug': 'iphone-15-pro-256-titanium', 'name': 'Apple iPhone 15 Pro 256GB Natural Titanium',
     'sku': 'IPH15P-256-TI', 'price': 52999, 'is_popular': True, 'is_new': True,
     'description': 'iPhone 15 Pro з чіпом A17 Pro, ProMotion 120Hz, 3x телеоб\'єктив.'},
    {'category': 'iphone', 'slug': 'iphone-14-128-starlight', 'name': 'Apple iPhone 14 128GB Starlight',
     'sku': 'IPH14-128-STL', 'price': 27999, 'is_popular': False, 'is_new': False,
     'description': 'iPhone 14, чіп A15 Bionic, 12 МП основна камера, режим екшн.'},

    # Samsung
    {'category': 'samsung', 'slug': 'samsung-s24-256-black', 'name': 'Samsung Galaxy S24 256GB Phantom Black',
     'sku': 'SGS24-256-BLK', 'price': 35999, 'is_popular': True, 'is_new': True,
     'description': 'Galaxy S24 з Snapdragon 8 Gen 3, 50 МП камера, 7 років оновлень.'},
    {'category': 'samsung', 'slug': 'samsung-a55-256-navy', 'name': 'Samsung Galaxy A55 256GB Awesome Navy',
     'sku': 'SGA55-256-NVY', 'price': 16499, 'is_popular': False, 'is_new': True,
     'description': 'Galaxy A55, AMOLED 120Hz, IP67, 50 МП Triple Camera.'},

    # Xiaomi
    {'category': 'xiaomi', 'slug': 'xiaomi-14-256-black', 'name': 'Xiaomi 14 256GB Black',
     'sku': 'XMI14-256-BLK', 'price': 29999, 'is_popular': True, 'is_new': True,
     'description': 'Xiaomi 14 з Leica камерою, Snapdragon 8 Gen 3, 90W зарядка.'},
    {'category': 'xiaomi', 'slug': 'redmi-note13-pro-256-black', 'name': 'Redmi Note 13 Pro 256GB Midnight Black',
     'sku': 'RN13P-256-BLK', 'price': 12999, 'is_popular': False, 'is_new': False,
     'description': 'Redmi Note 13 Pro, 200 МП камера, AMOLED 120Hz, 67W зарядка.'},

    # Laptops
    {'category': 'laptops', 'slug': 'macbook-air-15-m3-256-sg', 'name': 'Apple MacBook Air 15" M3 256GB Space Gray',
     'sku': 'MBA15-M3-256-SG', 'price': 62999, 'is_popular': True, 'is_new': True,
     'description': 'MacBook Air 15" з чіпом M3, 8GB RAM, 18 год. автономності, Liquid Retina.'},
    {'category': 'laptops', 'slug': 'asus-rog-strix-g16-rtx4060', 'name': 'ASUS ROG Strix G16 RTX 4060 512GB',
     'sku': 'AROG-G16-4060', 'price': 54999, 'is_popular': True, 'is_new': False,
     'description': 'Ігровий ноутбук ASUS ROG Strix, RTX 4060, i7-13650HX, 165Hz IPS.'},
    {'category': 'laptops', 'slug': 'lenovo-ideapad5-i5-512-blue', 'name': 'Lenovo IdeaPad 5 15" i5 512GB Blue',
     'sku': 'LIP5-I5-512-BLU', 'price': 22999, 'is_popular': False, 'is_new': False,
     'description': 'Lenovo IdeaPad 5, Intel Core i5-12500H, 16GB RAM, IPS FHD.'},

    # iPad
    {'category': 'ipad', 'slug': 'ipad-air-11-m2-256-blue', 'name': 'Apple iPad Air 11" M2 256GB Wi-Fi Blue',
     'sku': 'IPA11-M2-256-BLU', 'price': 32999, 'is_popular': True, 'is_new': True,
     'description': 'iPad Air з чіпом M2, Liquid Retina 11", підтримка Apple Pencil Pro.'},
    {'category': 'ipad', 'slug': 'ipad-109-64-silver', 'name': 'Apple iPad 10.9" 64GB Wi-Fi Silver',
     'sku': 'IP109-64-SLV', 'price': 14999, 'is_popular': False, 'is_new': False,
     'description': 'iPad 10-го покоління, A14 Bionic, USB-C, Touch ID, 12 МП фронтальна.'},

    # PlayStation
    {'category': 'playstation', 'slug': 'ps5-slim-1tb-disc', 'name': 'Sony PlayStation 5 Slim 1TB Disc',
     'sku': 'PS5-SLIM-1TB', 'price': 21999, 'is_popular': True, 'is_new': True,
     'description': 'PS5 Slim з дисководом, SSD 1TB, 4K 120fps, DualSense контролер у комплекті.'},
    {'category': 'playstation', 'slug': 'dualsense-midnight-black', 'name': 'Sony DualSense Controller Midnight Black',
     'sku': 'DS-CTRL-BLK', 'price': 3299, 'is_popular': False, 'is_new': False,
     'description': 'Бездротовий контролер DualSense з хаптичним зворотнім зв\'язком і адаптивними тригерами.'},

    # Xbox
    {'category': 'xbox', 'slug': 'xbox-series-x-1tb', 'name': 'Microsoft Xbox Series X 1TB',
     'sku': 'XBX-SX-1TB', 'price': 19999, 'is_popular': True, 'is_new': False,
     'description': 'Xbox Series X, 4K 120fps, SSD 1TB, Game Pass Ultimate сумісний.'},
    {'category': 'xbox', 'slug': 'xbox-controller-carbon-black', 'name': 'Xbox Wireless Controller Carbon Black',
     'sku': 'XBX-CTRL-BLK', 'price': 2299, 'is_popular': False, 'is_new': False,
     'description': 'Бездротовий контролер Xbox, Bluetooth, текстурований хват, USB-C.'},

    # Nintendo
    {'category': 'nintendo', 'slug': 'nintendo-switch-oled-white', 'name': 'Nintendo Switch OLED White',
     'sku': 'NSW-OLED-WHT', 'price': 12999, 'is_popular': True, 'is_new': False,
     'description': 'Nintendo Switch OLED з 7" екраном, Joy-Con, 64GB вбудованої пам\'яті.'},

    # Accessories
    {'category': 'controllers', 'slug': 'gamesir-t4-pro-bt', 'name': 'GameSir T4 Pro Bluetooth Gamepad',
     'sku': 'GSR-T4P-BT', 'price': 1899, 'is_popular': False, 'is_new': True,
     'description': 'Геймпад GameSir T4 Pro, Bluetooth 5.0, iOS/Android/PC/Switch.'},
    {'category': 'chargers', 'slug': 'apple-magsafe-15w-usbc', 'name': 'Apple MagSafe Charger 15W',
     'sku': 'APL-MGSF-15W', 'price': 1499, 'is_popular': False, 'is_new': False,
     'description': 'MagSafe зарядка 15W для iPhone 12 і новіших, кабель 1 метр.'},
    {'category': 'cases', 'slug': 'spigen-ultra-hybrid-iphone15-clear', 'name': 'Spigen Ultra Hybrid iPhone 15 Crystal Clear',
     'sku': 'SPG-UH-IP15-CLR', 'price': 699, 'is_popular': False, 'is_new': False,
     'description': 'Прозорий чохол Spigen для iPhone 15, захист від падінь MIL-STD 810G.'},
]


class Command(BaseCommand):
    help = 'Add demo products to Yar4ick Technology store'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear all products first')

    def handle(self, *args, **options):
        if options['clear']:
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING('All products deleted.'))

        created = skipped = errors = 0

        for p in PRODUCTS:
            try:
                cat = Category.objects.get(slug=p['category'])
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Category not found: {p['category']}"))
                errors += 1
                continue

            if Product.objects.filter(slug=p['slug']).exists():
                skipped += 1
                continue

            Product.objects.create(
                slug=p['slug'],
                name=p['name'],
                category=cat,
                sku=p.get('sku', ''),
                price=p['price'],
                description=p.get('description', ''),
                is_popular=p.get('is_popular', False),
                is_new=p.get('is_new', False),
                is_available=True,
            )
            created += 1
            self.stdout.write(f'  + {p["name"]}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created}, Skipped: {skipped}, Errors: {errors}'
        ))
