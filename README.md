# Yar4ick Technology — Інтернет-магазин

Django-сайт магазину техніки з каталогом, кошиком, оформленням замовлень і Telegram-ботом.

**Живий сайт:** https://new-birth.xyz  
**Сервер:** `root@185.237.207.137`  
**Шлях на сервері:** `/var/www/antidrone/`

---

## Зміст

1. [Структура проекту](#структура-проекту)
2. [Локальний запуск](#локальний-запуск)
3. [Деплой на сервер](#деплой-на-сервер)
4. [Змінні оточення (.env)](#змінні-оточення)
5. [Адмін-панель](#адмін-панель)
6. [Додавання товарів через Excel](#додавання-товарів-через-excel)
7. [Telegram-бот](#telegram-бот)
8. [Корисні команди](#корисні-команди)
9. [Іконки та кольори категорій](#іконки-та-кольори-категорій)
10. [Що ще можна покращити](#що-ще-можна-покращити)

---

## Структура проекту

```
yar4ick-shop/
├── antidrone/                  # Конфіг Django (settings, urls, wsgi)
│   ├── settings.py
│   └── urls.py
├── catalog/                    # Основний додаток каталогу
│   ├── models.py               # Category, Product, ProductImage
│   ├── views.py                # IndexView, CategoryList, CategoryDetail, ProductDetail
│   ├── admin.py                # Адмін-інтерфейс
│   ├── templatetags/
│   │   └── catalog_tags.py     # Фільтри: category_icon, category_color
│   └── management/commands/
│       ├── import_excel.py     # Імпорт товарів з Excel
│       ├── setup_categories.py # Створення категорій
│       └── add_demo_products.py
├── telegram_bot/               # Telegram-бот (окремий процес)
│   ├── bot.py                  # Логіка бота (FSM замовлення)
│   ├── config.py               # BOT_TOKEN, MANAGER_USERNAME тощо
│   └── README.md
├── templates/
│   ├── base.html               # Базовий шаблон (хедер, кошик, стилі)
│   ├── catalog/
│   │   ├── index.html          # Головна сторінка (splash, категорії, товари)
│   │   ├── category_list.html  # Сторінка каталогу (/catalog/)
│   │   ├── category_detail.html# Сторінка категорії з підкатегоріями і товарами
│   │   ├── product_detail.html # Сторінка товару
│   │   └── cart.html           # Кошик
│   └── pages/
│       ├── about.html
│       └── delivery.html
├── static/
│   └── css/
│       └── style.v2.css        # Основні стилі (темна тема, компоненти)
├── deploy/
│   ├── deploy.sh               # Скрипт деплою (запустити на сервері)
│   ├── gunicorn.service        # systemd юніт для gunicorn
│   └── nginx.conf              # Конфіг nginx
├── requirements.txt
├── manage.py
└── .env                        # НЕ в git! (секрети)
```

---

## Локальний запуск

```bash
# 1. Клонувати репо
git clone https://github.com/BeluyIT/yar4ick-shop.git
cd yar4ick-shop

# 2. Створити venv
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Встановити залежності
pip install -r requirements.txt

# 4. Створити .env (дивись розділ нижче)
cp .env.example .env            # або створити вручну

# 5. Міграції
python manage.py migrate

# 6. Заповнити базу тестовими категоріями і товарами
python manage.py setup_categories
python manage.py add_demo_products

# 7. Створити адміна
python manage.py createsuperuser

# 8. Запустити
python manage.py runserver
```

Сайт: http://127.0.0.1:8000  
Адмін: http://127.0.0.1:8000/admin/

---

## Деплой на сервер

### Перший деплой (з нуля)

```bash
# Підключитись до сервера
ssh root@185.237.207.137

# Встановити залежності системи
apt update && apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx git

# Клонувати проект
cd /var/www
git clone https://github.com/BeluyIT/yar4ick-shop.git antidrone
cd antidrone

# Створити venv і встановити пакети
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Створити .env (заповнити своїми даними)
nano .env

# Міграції і статика
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_categories

# Systemd сервіс для gunicorn
cp deploy/gunicorn.service /etc/systemd/system/antidrone.service
# Відредагувати шляхи у файлі якщо потрібно:
nano /etc/systemd/system/antidrone.service

systemctl daemon-reload
systemctl enable antidrone
systemctl start antidrone

# Nginx
cp deploy/nginx.conf /etc/nginx/sites-available/antidrone
ln -s /etc/nginx/sites-available/antidrone /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# SSL (після того як DNS вказує на сервер)
certbot --nginx -d new-birth.xyz -d www.new-birth.xyz
```

### Оновлення (pull нових змін)

```bash
ssh root@185.237.207.137
cd /var/www/antidrone
git pull origin main
source venv/bin/activate
pip install -r requirements.txt          # якщо змінились залежності
python manage.py migrate                  # якщо є нові міграції
python manage.py collectstatic --noinput  # якщо змінились статичні файли
systemctl restart antidrone
```

### Перезапуск і статус сервісів

```bash
systemctl restart antidrone       # перезапустити сайт
systemctl restart antidrone-bot   # перезапустити Telegram-бота
systemctl status antidrone        # статус сайту
journalctl -u antidrone -n 50     # логи сайту
journalctl -u antidrone-bot -n 50 # логи бота
```

---

## Змінні оточення

Файл `.env` в корені проекту (не комітити в git):

```env
SECRET_KEY=your-very-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,new-birth.xyz,www.new-birth.xyz

# Telegram-бот
BOT_TOKEN=8469869255:AAGrQIOvr3DaSZUr093M6iGpkVObC-gsvzo
ORDERS_CHAT_ID=-1003809201269
MANAGER_USERNAME=@DoubleVasya
MANAGER_USERNAME_2=@liashyarchik
SITE_URL=https://new-birth.xyz
```

Для локальної розробки можна встановити `DEBUG=True` і `ALLOWED_HOSTS=*`.

**Генерація SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Адмін-панель

URL: https://new-birth.xyz/admin/  
Логін: створюється командою `python manage.py createsuperuser`

### Що робити в адміні:

**Категорії (Categories):**
- Додавати/редагувати категорії
- Поле `slug` — важливе! Від нього залежать іконка і колір (дивись `catalog_tags.py`)
- Поле `parent` — для підкатегорій
- `is_active` — показувати/приховувати

**Товари (Products):**
- Назва, опис, ціна (якщо пусто — показується "За запитом")
- `sku` — артикул
- `is_new` / `is_popular` — бейджі на картці
- Зображення додаються в розділі ProductImages нижче
- Перше зображення (order=0) — головне

---

## Додавання товарів через Excel

### Формат файлу Excel

Перший рядок — заголовки (назви можуть бути будь-якими, головне — порядок):

| Назва | Категорія | Ціна | Опис | Артикул | Новинка | Популярний |
|-------|-----------|------|------|---------|---------|-----------|
| iPhone 15 Pro | iphone | 54999 | Опис товару | IPH-15P | 1 | 0 |
| Samsung S24 | samsung | 42999 | | SAM-S24 | 0 | 1 |

**Колонки (порядок важливий):**
1. `name` — назва товару (обов'язково)
2. `category` — slug або назва категорії
3. `price` — ціна в гривнях (число, можна пусто)
4. `description` — опис
5. `sku` — артикул
6. `is_new` — 1/0 або True/False
7. `is_popular` — 1/0 або True/False

### Команди імпорту

```bash
# Перевірити без змін (dry-run)
python manage.py import_excel товари.xlsx --dry-run

# Імпортувати (нові товари)
python manage.py import_excel товари.xlsx

# Імпортувати і оновити існуючі (за назвою)
python manage.py import_excel товари.xlsx --update

# Вказати аркуш Excel
python manage.py import_excel товари.xlsx --sheet "Аркуш1"
```

### Зображення після імпорту

Після імпорту завантажити зображення можна:
1. Через адмін-панель: знайти товар → додати зображення
2. Або через API якщо буде реалізовано

---

## Telegram-бот

**Файли:** `telegram_bot/bot.py`, `telegram_bot/config.py`

### Можливості бота

- Перегляд категорій і товарів
- Оформлення замовлення (ПІБ → телефон → місто → відділення НП → підтвердження → оплата)
- Відправка фото оплати
- Повідомлення менеджерам (@DoubleVasya і @liashyarchik) з деталями замовлення
- Кнопка "◀️ Назад" — відкотитись до попереднього кроку
- Кнопка "❌ Скасувати замовлення"

### Запуск бота локально

```bash
cd telegram_bot
python bot.py
```

### Systemd сервіс бота (на сервері)

```bash
# Перевірити статус
systemctl status antidrone-bot

# Перезапустити (після змін в bot.py)
systemctl restart antidrone-bot

# Логи
journalctl -u antidrone-bot -f
```

Файл сервісу: `/etc/systemd/system/antidrone-bot.service`

---

## Корисні команди

```bash
# Заповнити категорії (22 категорії: смартфони, ноутбуки, планшети, ігрові, аксесуари)
python manage.py setup_categories

# Додати тестові товари (20 шт.)
python manage.py add_demo_products

# Відкрити Django shell
python manage.py shell

# Перевірити кількість товарів і категорій
python manage.py shell -c "
from catalog.models import Category, Product
print(f'Категорій: {Category.objects.count()}')
print(f'Товарів: {Product.objects.count()}')
"

# Скинути і перезаповнити базу
python manage.py flush --no-input
python manage.py setup_categories
python manage.py add_demo_products

# Зібрати статику (після змін CSS/JS)
python manage.py collectstatic --noinput
```

---

## Іконки та кольори категорій

Файл: `catalog/templatetags/catalog_tags.py`

Кожна категорія визначається по `slug`. Щоб додати нову іконку:

```python
CATEGORY_ICONS = {
    'my-new-category': ('bi-star', '#FF6600'),
    # (Bootstrap Icon class, HEX колір)
}
```

Іконки — з Bootstrap Icons: https://icons.getbootstrap.com  
Формат: `bi-назва-іконки`

### Поточні категорії і їх кольори

| Slug | Іконка | Колір |
|------|--------|-------|
| smartphones | bi-phone | #FF6600 (оранжевий) |
| iphone | bi-apple | #A8A8A8 (сірий) |
| samsung | bi-phone-flip | #1877F2 (синій) |
| xiaomi | bi-phone-vibrate | #FF6900 |
| laptops-pk | bi-laptop | #00B4D8 (блакитний) |
| computers | bi-pc-display | #7B2FBE (фіолетовий) |
| components | bi-cpu | #F72585 (рожевий) |
| tablets | bi-tablet | #A855F7 (фіолетовий) |
| ipad | bi-tablet-landscape | #A8A8A8 |
| galaxy-tab | bi-tablet-fill | #1877F2 |
| gaming | bi-controller | #FF6600 |
| xbox | bi-microsoft | #107C10 (зелений) |
| playstation | bi-playstation | #003791 (синій Sony) |
| nintendo | bi-nintendo-switch | #E4000F (червоний) |
| accessories | bi-bag | #2ECC71 (зелений) |
| controllers | bi-joystick | #FF8800 |
| games | bi-disc | #9B59B6 |
| chargers | bi-lightning-charge | #F39C12 |
| cases | bi-shield-check | #3498DB |

---

## Що ще можна покращити

### Функціонал
- [ ] Пошук по каталогу (поле у хедері)
- [ ] Фільтрація товарів (по ціні, бренду, наявності)
- [ ] Сторінка замовлень в адміні з статусами
- [ ] Відправка email-підтвердження замовникам
- [ ] Інтеграція з Nova Poshta API (авторозрахунок доставки)
- [ ] Відгуки на товари
- [ ] Порівняння товарів
- [ ] Wishlist / обране
- [ ] Промокоди і знижки

### Технічне
- [ ] PostgreSQL замість SQLite (для продакшну)
- [ ] Redis + Celery для фонових задач (email, сповіщення)
- [ ] Логування помилок через Sentry
- [ ] Кешування сторінок каталогу
- [ ] CDN для зображень
- [ ] Бекап бази даних (cron)
- [ ] Метрики (Google Analytics або Plausible)

### Контент
- [ ] Сторінка "Про нас" заповнити реальним текстом
- [ ] Сторінка "Доставка і оплата" деталі
- [ ] Додати реальні фото товарів
- [ ] Заповнити описи категорій

---

## Технічний стек

| Компонент | Технологія |
|-----------|-----------|
| Backend | Django 4.2 |
| БД | SQLite (dev) / PostgreSQL (prod рекомендовано) |
| Категорії | django-mptt (дерево категорій) |
| Статика | WhiteNoise + Nginx |
| Сервер додатку | Gunicorn (2 workers) |
| Веб-сервер | Nginx + Let's Encrypt SSL |
| Процес-менеджер | systemd |
| Frontend | Vanilla JS + Bootstrap Icons |
| Стилі | Кастомний CSS (темна тема, без фреймворків) |
| Бот | python-telegram-bot 20.7 (async) |
| Excel | openpyxl |
