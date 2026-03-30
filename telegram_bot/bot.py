#!/usr/bin/env python3
"""Yar4ick Technology Telegram bot for order intake flow with payment."""
import html
import asyncio
import base64
import json
import logging
import os
import re
import ssl
from typing import Any, Dict, List, Optional, Tuple
from urllib import request as urlrequest

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, LOG_FILE, ORDERS_CHAT_ID, MANAGER_USERNAME, SITE_URL, PAYMENT_DETAILS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ],
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ============================================
# STATES
# ============================================
ASK_NAME = 0
ASK_SURNAME = 1
ASK_PHONE = 2
ASK_CITY = 3
ASK_BRANCH = 4
CONFIRM_DATA = 5
PAYMENT_METHOD = 6
WAITING_PAYMENT_PROOF = 7

STATE_KEY = "order_state"
CANCEL_TEXT = "❌ Скасувати"

MENU_NEW_ORDER = "📦 Нове замовлення"
MENU_MANAGER = "💬 Менеджер"
MENU_SITE = "🌐 Сайт"
MENU_ORDER_SENT = "🛒 Замовлення"

# ============================================
# ORDER API
# ============================================
def _open_url(url: str) -> Optional[bytes]:
    try:
        with urlrequest.urlopen(url, timeout=10) as response:
            if response.status != 200:
                return None
            return response.read()
    except Exception:
        return None


def _open_url_allow_insecure(url: str) -> Optional[bytes]:
    try:
        context = ssl._create_unverified_context()
        with urlrequest.urlopen(url, timeout=10, context=context) as response:
            if response.status != 200:
                return None
            return response.read()
    except Exception:
        return None


def fetch_order_from_api(order_id: str) -> Optional[dict]:
    """Fetch order JSON from site API."""
    bases = []
    site = SITE_URL.rstrip('/')
    if site:
        bases.append(site)
    env_bases = os.getenv('ORDER_API_BASE_URLS', '')
    for raw in env_bases.split(','):
        base = raw.strip().rstrip('/')
        if base:
            bases.append(base)
    if '127.0.0.1' not in ' '.join(bases):
        bases.append('http://127.0.0.1:8000')
    if 'localhost' not in ' '.join(bases):
        bases.append('http://localhost:8000')

    for base_url in bases:
        url = f"{base_url}/api/order/{order_id}/"
        try:
            data = _open_url(url)
            if data is None:
                data = _open_url_allow_insecure(url)
            if data is None:
                continue
            return json.loads(data.decode('utf-8'))
        except Exception as exc:
            logger.error(f"Failed to fetch order {order_id} from {base_url}: {exc}")
            continue
    return None


def confirm_order_via_api(order_id: str) -> bool:
    """Mark order as confirmed via site API."""
    base_url = SITE_URL.rstrip('/')
    url = f"{base_url}/api/order/{order_id}/confirm/"
    request = urlrequest.Request(url, method='POST', data=b'{}', headers={'Content-Type': 'application/json'})
    try:
        try:
            with urlrequest.urlopen(request, timeout=10) as response:
                if response.status != 200:
                    return False
                data = response.read()
        except Exception:
            context = ssl._create_unverified_context()
            with urlrequest.urlopen(request, timeout=10, context=context) as response:
                if response.status != 200:
                    return False
                data = response.read()
        payload = json.loads((data or b'{}').decode('utf-8'))
        return payload.get('status') == 'confirmed'
    except Exception as exc:
        logger.error(f"Failed to confirm order {order_id}: {exc}")
        return False


# ============================================
# KEYBOARDS
# ============================================
def build_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[
            KeyboardButton("📦 Нове замовлення"),
            KeyboardButton("💬 Менеджер"),
            KeyboardButton("🌐 Сайт"),
        ]],
        resize_keyboard=True,
    )


def build_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Так, все вірно")],
            [KeyboardButton("❌ Ні, змінити дані")],
        ],
        resize_keyboard=True,
    )


def build_payment_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("💳 ПриватБанк"), KeyboardButton("💳 ПУМБ")],
            [KeyboardButton("💳 A-Bank"), KeyboardButton("🏢 ФОП")],
        ],
        resize_keyboard=True,
    )


def build_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("❌ Скасувати")]],
        resize_keyboard=True,
    )


def build_cancel_order_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("❌ Скасувати замовлення")]],
        resize_keyboard=True,
    )


def build_site_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Перейти на сайт", url=SITE_URL)]])


# ============================================
# HELPERS
# ============================================
def decode_payload(payload: str) -> Optional[List[Dict[str, Any]]]:
    """Decode base64 payload from deep link.

    Supported formats:
    1) Compact JSON (urlsafe base64): [[id,name,sku,price,qty], ...]
    2) Legacy text: base64(encodeURIComponent("1.Name|SKU|price|qty;..."))
    """
    logger.info(f"decode_payload called with: '{payload}'")

    def parse_compact_json(data: Any) -> Optional[List[Dict[str, Any]]]:
        if isinstance(data, list) and data and isinstance(data[0], list):
            items = []
            for row in data:
                if len(row) < 5:
                    continue
                items.append({
                    'id': str(row[0]),
                    'name': str(row[1]),
                    'sku': str(row[2]),
                    'price': int(row[3]) if row[3] else 0,
                    'qty': int(row[4]) if row[4] else 1,
                })
            return items or None
        if isinstance(data, list) and (not data or isinstance(data[0], dict)):
            items = []
            for row in data:
                if not isinstance(row, dict):
                    continue
                items.append({
                    'id': str(row.get('id', '')),
                    'name': str(row.get('name', 'Товар')),
                    'sku': str(row.get('sku', '')),
                    'price': int(row.get('price', 0) or 0),
                    'qty': int(row.get('qty', 1) or 1),
                })
            return items or None
        return None

    def parse_legacy_text(text: str) -> Optional[List[Dict[str, Any]]]:
        items = []
        for item_str in text.split(';'):
            item_str = item_str.strip()
            if not item_str or '|' not in item_str:
                continue
            parts = item_str.split('|')
            if len(parts) < 4:
                continue
            first_part = parts[0]
            name = first_part.split('.', 1)[1].strip() if '.' in first_part else first_part.strip()
            sku = parts[1].strip()
            try:
                price = float(parts[2])
            except Exception:
                price = 0
            try:
                qty = int(parts[3])
            except Exception:
                qty = 1
            items.append({
                'name': name,
                'sku': sku,
                'price': price,
                'qty': qty,
            })
        return items or None

    try:
        from urllib.parse import unquote

        padding = '=' * (-len(payload) % 4)
        padded = payload + padding
        decoded_bytes = base64.urlsafe_b64decode(padded)
        decoded_str = decoded_bytes.decode('utf-8')

        # 1) Try compact JSON first (no URL decode)
        try:
            data = json.loads(decoded_str)
            items = parse_compact_json(data)
            if items:
                logger.info(f"Parsed {len(items)} items (compact json)")
                return items
        except Exception:
            pass

        # 2) Legacy format: URL-decode then parse text
        decoded_raw = unquote(decoded_str)
        logger.info(f"Decoded raw: '{decoded_raw}'")
        items = parse_legacy_text(decoded_raw)
        if items:
            logger.info(f"Parsed {len(items)} items (legacy text)")
            return items

    except Exception as exc:
        logger.error(f"Decoded payload failed: {exc}", exc_info=True)
    return None


def format_items(items: list[dict[str, Any]]) -> tuple[str, int]:
    """Format items list and calculate total."""
    total = 0
    lines = []
    for idx, item in enumerate(items, 1):
        name = str(item.get('name') or 'Товар')
        qty = int(item.get('qty') or 1)
        price = int(item.get('price') or 0)
        line_total = price * qty
        total += line_total
        lines.append(f"{idx}. {name}\n   {qty} шт × {price} грн = {line_total} грн")
    return "\n".join(lines), total


def format_items_short(items: list[dict[str, Any]]) -> str:
    """Format items list in short format for order notification."""
    lines = []
    for idx, item in enumerate(items, 1):
        name = str(item.get('name') or 'Товар')
        qty = int(item.get('qty') or 1)
        price = int(item.get('price') or 0)
        line_total = price * qty
        lines.append(f"{idx}. {name} {price}×{qty}={line_total}грн")
    return "\n".join(lines)


def validate_phone(phone: str) -> Optional[str]:
    """Validate and normalize Ukrainian phone number."""
    cleaned = re.sub(r'[^\d+]', '', phone)
    patterns = [
        (r'^\+380\d{9}$', lambda p: p),
        (r'^380\d{9}$', lambda p: '+' + p),
        (r'^0\d{9}$', lambda p: '+38' + p),
    ]
    for pattern, normalizer in patterns:
        if re.match(pattern, cleaned):
            return normalizer(cleaned)
    return None


def parse_order_text(text: str) -> Optional[Tuple[List[Dict[str, Any]], int]]:
    """Parse order from text message sent via ?text= link.

    Format: ORDER:
    1. Name|SKU:xxx|priceгрн×qty=totalгрн
    TOTAL:total
    """
    if not text.startswith('ORDER:'):
        return None

    try:
        lines = text.strip().split('\n')
        items = []
        total = 0

        for line in lines:
            line = line.strip()
            # Parse item: "1. Name|SKU:xxx|priceгрн×qty=totalгрн"
            if '|SKU:' in line:
                # Remove number prefix
                if '. ' in line:
                    line = line.split('. ', 1)[1]

                parts = line.split('|')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    sku = parts[1].replace('SKU:', '').strip()
                    price_qty = parts[2]  # "priceгрн×qty=totalгрн"

                    # Parse price and qty from "priceгрн×qty=totalгрн"
                    match = re.match(r'(\d+)грн[×x](\d+)=', price_qty)
                    if match:
                        price = int(match.group(1))
                        qty = int(match.group(2))
                    else:
                        # Fallback: try old format "qtyxprice=total"
                        if 'x' in price_qty and '=' in price_qty:
                            qty_part = price_qty.split('x')[0]
                            price_part = price_qty.split('x')[1].split('=')[0]
                            qty = int(qty_part) if qty_part.isdigit() else 1
                            price = int(price_part) if price_part.isdigit() else 0
                        else:
                            qty, price = 1, 0

                    items.append({'name': name, 'sku': sku, 'price': price, 'qty': qty})

            elif line.startswith('TOTAL:'):
                total_str = line.replace('TOTAL:', '').strip()
                total = int(total_str) if total_str.isdigit() else 0

        if items:
            if total == 0:
                total = sum(item['price'] * item['qty'] for item in items)
            return items, total
    except Exception as e:
        logger.error(f"Failed to parse order text: {e}")
    return None


def parse_clipboard_order(text: str) -> Optional[Tuple[List[Dict[str, Any]], int]]:
    """Parse order from clipboard paste (new format from cart.js).

    Format:
    1. Product Name
    SKU: xxx × qty = total грн

    Разом: total грн
    """
    if 'SKU:' not in text or 'грн' not in text:
        return None

    try:
        lines = text.strip().split('\n')
        items = []
        total = 0
        current_name = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for item name line (starts with number and dot)
            if re.match(r'^\d+\.', line):
                # Extract name after "N. "
                current_name = re.sub(r'^\d+\.\s*', '', line).strip()

            # Check for SKU line: "SKU: xxx × qty = total грн"
            elif line.startswith('SKU:') and current_name:
                # Parse: "SKU: xxx × qty = total грн"
                match = re.match(r'SKU:\s*([^\s×]+)\s*×\s*(\d+)\s*=\s*(\d+)\s*грн', line)
                if match:
                    sku = match.group(1).strip()
                    qty = int(match.group(2))
                    line_total = int(match.group(3))
                    price = line_total // qty if qty > 0 else 0
                    items.append({
                        'name': current_name,
                        'sku': sku,
                        'price': price,
                        'qty': qty,
                    })
                    current_name = None

            # Check for total line: "Разом: xxx грн"
            elif line.startswith('Разом:'):
                match = re.search(r'(\d+)', line)
                if match:
                    total = int(match.group(1))

        if items:
            if total == 0:
                total = sum(item['price'] * item['qty'] for item in items)
            return items, total

    except Exception as e:
        logger.error(f"Failed to parse clipboard order: {e}")
    return None


def get_payment_details(choice: str) -> tuple[str, str]:
    """Get payment details based on user choice."""
    if "ПриватБанк" in choice:
        p = PAYMENT_DETAILS.get('privat', {})
        return 'ПриватБанк', f"💳 *ПриватБанк*\n\n`{p.get('card', '5168 XXXX XXXX XXXX')}`\n{p.get('holder', 'Отримувач')}"
    elif "ПУМБ" in choice:
        p = PAYMENT_DETAILS.get('pumb', {})
        return 'ПУМБ', f"💳 *ПУМБ*\n\n`{p.get('card', '5169 XXXX XXXX XXXX')}`\n{p.get('holder', 'Отримувач')}"
    elif "A-Bank" in choice:
        p = PAYMENT_DETAILS.get('alfa', {})
        return 'A-Bank', f"💳 *A-Bank*\n\n`{p.get('card', '5457 XXXX XXXX XXXX')}`\n{p.get('holder', 'Отримувач')}"
    elif "ФОП" in choice:
        p = PAYMENT_DETAILS.get('fop', {}).get('details', {})
        return 'ФОП', (
            f"🏢 *ФОП (безготівковий розрахунок)*\n\n"
            f"Отримувач: {p.get('name', 'ФОП')}\n"
            f"ЄДРПОУ: `{p.get('edrpou', 'XXXXXXXXXX')}`\n"
            f"МФО: `{p.get('mfo', '305299')}`\n"
            f"Р/р: `{p.get('account', 'UAXXXXXXXXXX')}`\n"
            f"Банк: {p.get('bank', 'ПриватБанк')}"
        )
    else:
        return 'Оплата при отриманні', ''


# ============================================
# HANDLERS
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with optional deep link payload."""
    from urllib.parse import unquote

    if context.args:
        payload = context.args[0].strip()
        logger.info(f"Start with payload: {payload}")

        if re.match(r'^[a-z0-9]{8,12}$', payload):
            order_id = payload
            order_data = fetch_order_from_api(order_id)
            if not order_data:
                await asyncio.sleep(1)
                order_data = fetch_order_from_api(order_id)
            if not order_data:
                await update.message.reply_text(
                    "⏳ Замовлення ще обробляється. Будь ласка, повторіть команду "
                    f"/start {order_id} через 1-2 хвилини або напишіть менеджеру.",
                    reply_markup=build_start_keyboard()
                )
                return

            context.user_data.clear()
            context.user_data["order_id"] = order_id
            context.user_data["order_items"] = order_data.get('items', [])
            context.user_data["order_total"] = order_data.get('total', 0)
            context.user_data["group_message_sent"] = False
            context.user_data[STATE_KEY] = ASK_NAME

            await update.message.reply_text(
                f"✅ Замовлення *#{order_id}* прийнято.\n\n"
                f"Вкажіть ваше *ім'я* для оформлення:",
                parse_mode="Markdown",
                reply_markup=build_cancel_keyboard()
            )
            return

        try:
            # Decode base64 legacy payload
            decoded_bytes = base64.b64decode(payload)
            decoded_str = decoded_bytes.decode('utf-8')
            decoded = unquote(decoded_str)
            logger.info(f"Decoded: {decoded}")

            items_raw = decoded.split(';')
            items = []
            total = 0

            for item_str in items_raw:
                item_str = item_str.strip()
                if not item_str or '|' not in item_str:
                    continue

                parts = item_str.split('|')
                if len(parts) >= 4:
                    first = parts[0]
                    name = first.split('.', 1)[1].strip() if '.' in first else first.strip()
                    sku = parts[1].strip()
                    price = float(parts[2]) if parts[2] else 0
                    qty = int(parts[3]) if parts[3] else 1

                    items.append({'name': name, 'sku': sku, 'price': price, 'qty': qty})
                    total += price * qty

            if items:
                context.user_data.clear()
                context.user_data["order_items"] = items
                context.user_data["order_total"] = total
                context.user_data["group_message_sent"] = False
                context.user_data[STATE_KEY] = ASK_NAME

                msg = "🛡️ ВАШЕ ЗАМОВЛЕННЯ:\n━━━━━━━━━━━━━━━━━━━━\n\n"
                for i, item in enumerate(items, 1):
                    msg += f"{i}. {item['name']}\n   {int(item['price'])} грн × {item['qty']} шт\n\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━\n💰 Сума: {int(total)} грн\n\n⬇️ Вкажіть ваше ім'я:"

                await update.message.reply_text(msg, reply_markup=build_cancel_keyboard())
                return

        except Exception as e:
            logger.error(f"Payload decode error: {e}")

    # Default welcome
    user = update.effective_user
    await update.message.reply_text(
        f"Вітаємо, {user.first_name}! 👋\n\n"
        f"Я бот магазину Yar4ick Technology\n\n"
        f"🔹 Щоб оформити замовлення, перейдіть на сайт, "
        f"додайте товари в кошик і натисніть «Оформити».\n\n"
        f"🔹 Або зв'яжіться з менеджером: {MANAGER_USERNAME}",
        reply_markup=build_start_keyboard()
    )


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = (update.message.text or "").strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Ім'я занадто коротке.\n\nВведіть ваше ім'я:", reply_markup=build_cancel_keyboard())
        return
    context.user_data["name"] = name
    context.user_data[STATE_KEY] = ASK_SURNAME
    await update.message.reply_text(f"✅ Ім'я: *{name}*\n\nВведіть ваше *прізвище:*", parse_mode="Markdown", reply_markup=build_cancel_keyboard())


async def handle_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    surname = (update.message.text or "").strip()
    if len(surname) < 2:
        await update.message.reply_text("❌ Прізвище занадто коротке.\n\nВведіть прізвище:", reply_markup=build_cancel_keyboard())
        return
    context.user_data["surname"] = surname
    context.user_data[STATE_KEY] = ASK_PHONE
    await update.message.reply_text(f"✅ Прізвище: *{surname}*\n\nВведіть *номер телефону* (+380...):", parse_mode="Markdown", reply_markup=build_cancel_keyboard())


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    phone = validate_phone((update.message.text or "").strip())
    if not phone:
        await update.message.reply_text("❌ Невірний формат.\n\nВведіть номер: +380XXXXXXXXX", reply_markup=build_cancel_keyboard())
        return
    context.user_data["phone"] = phone
    context.user_data[STATE_KEY] = ASK_CITY
    await update.message.reply_text(f"✅ Телефон: *{phone}*\n\nВведіть *місто* для доставки:", parse_mode="Markdown", reply_markup=build_cancel_keyboard())


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    city = (update.message.text or "").strip()
    if len(city) < 2:
        await update.message.reply_text("❌ Вкажіть місто:", reply_markup=build_cancel_keyboard())
        return
    context.user_data["city"] = city
    context.user_data[STATE_KEY] = ASK_BRANCH
    await update.message.reply_text(f"✅ Місто: *{city}*\n\nВведіть *номер відділення* НП (наприклад: 15):", parse_mode="Markdown", reply_markup=build_cancel_keyboard())


async def handle_branch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    branch = (update.message.text or "").strip().replace("№", "").strip()
    if not branch:
        await update.message.reply_text("❌ Вкажіть номер відділення НП:", reply_markup=build_cancel_keyboard())
        return

    context.user_data["branch"] = branch
    context.user_data[STATE_KEY] = CONFIRM_DATA

    items = context.user_data.get("order_items", [])
    items_text, total = format_items(items) if items else ("—", 0)

    summary = (
        f"📋 *Перевірте дані замовлення:*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Клієнт:*\n"
        f"   {context.user_data.get('name', '—')} {context.user_data.get('surname', '—')}\n"
        f"   📱 {context.user_data.get('phone', '—')}\n\n"
        f"📦 *Доставка:*\n"
        f"   {context.user_data.get('city', '—')}, НП №{branch}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 *Товари:*\n{items_text}\n\n"
        f"💰 *Разом:* {total} грн\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Все вірно?"
    )
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=build_confirm_keyboard())


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()

    if text == "✅ Так, все вірно":
        context.user_data[STATE_KEY] = PAYMENT_METHOD
        total = context.user_data.get("order_total", 0)
        await update.message.reply_text(
            f"💳 *Оберіть спосіб оплати:*\n\n"
            f"💰 Сума до оплати: *{total} грн*",
            parse_mode="Markdown",
            reply_markup=build_payment_keyboard()
        )
        return

    if text == "❌ Ні, змінити дані":
        context.user_data[STATE_KEY] = ASK_NAME
        await update.message.reply_text("🔄 Давайте введемо дані заново.\n\nВведіть ваше *ім'я:*", parse_mode="Markdown", reply_markup=build_cancel_keyboard())
        return

    await update.message.reply_text("Оберіть варіант з клавіатури:", reply_markup=build_confirm_keyboard())


async def handle_payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle payment method selection."""
    choice = (update.message.text or "").strip()
    logger.info(f"Payment choice: {choice}")

    # Get payment details
    payment_name, payment_details = get_payment_details(choice)
    context.user_data["payment_method"] = payment_name

    if not payment_details:
        await finalize_order(update, context)
        return

    context.user_data[STATE_KEY] = WAITING_PAYMENT_PROOF
    total = context.user_data.get("order_total", 0)

    await update.message.reply_text(
        f"{payment_details}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Сума до оплати:* {total} грн\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📸 Після оплати надішліть *скріншот чеку:*",
        parse_mode="Markdown",
        reply_markup=build_cancel_order_keyboard()
    )


async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle payment proof photo."""
    if update.message.text == "❌ Скасувати замовлення":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Замовлення скасовано.",
            reply_markup=build_start_keyboard()
        )
        return

    if update.message.photo:
        photo = update.message.photo[-1]
        context.user_data["payment_proof_id"] = photo.file_id
        logger.info(f"Received payment proof photo: {photo.file_id}")
        await finalize_order(update, context)
    elif update.message.text:
        await update.message.reply_text(
            "📸 Надішліть *фото чеку* або скасуйте замовлення:",
            parse_mode="Markdown",
            reply_markup=build_cancel_order_keyboard()
        )


async def finalize_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Finalize order and send to managers."""
    user = update.effective_user
    def md(text: object) -> str:
        return escape_markdown(str(text), version=2)

    def h(text: object) -> str:
        return html.escape(str(text))

    items = context.user_data.get("order_items", [])
    total = context.user_data.get("order_total", 0)
    payment_method = context.user_data.get("payment_method", "—")
    payment_proof_id = context.user_data.get("payment_proof_id")
    group_message_sent = context.user_data.get("group_message_sent", False)
    order_id = context.user_data.get("order_id")

    if order_id:
        if not confirm_order_via_api(str(order_id)):
            logger.warning(f"Failed to confirm order {order_id} via API")

    try:
        if group_message_sent:
            # Items already sent, only send customer data + photo
            order_line = f"🧾 Замовлення: <b>#{h(order_id)}</b>\n\n" if order_id else ""
            customer_text = (
                f"✅ <b>ДАНІ КЛІЄНТА:</b>\n\n"
                f"{order_line}"
                f"👤 {h(context.user_data.get('name', '—'))} {h(context.user_data.get('surname', '—'))}\n"
                f"📱 {h(context.user_data.get('phone', '—'))}\n"
                f"📍 {h(context.user_data.get('city', '—'))}, НП №{h(context.user_data.get('branch', '—'))}\n\n"
                f"💳 <b>Оплата:</b> {h(payment_method)}\n"
                f"💰 <b>Сума:</b> {h(total)} грн"
            )
            await context.bot.send_message(
                chat_id=ORDERS_CHAT_ID,
                text=customer_text,
                parse_mode=ParseMode.HTML
            )
        else:
            # Full order (fallback)
            items_text = "\n".join(
                f"{idx}. {h(item.get('name') or 'Товар')} "
                f"{h(int(item.get('price') or 0))}×{h(int(item.get('qty') or 1))}="
                f"{h(int(item.get('price') or 0) * int(item.get('qty') or 1))}грн"
                for idx, item in enumerate(items, 1)
            ) or "—"
            order_text = (
                f"🔔 <b>НОВЕ ЗАМОВЛЕННЯ</b>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Клієнт:</b>\n"
                f"├ {h(context.user_data.get('name', '—'))} {h(context.user_data.get('surname', '—'))}\n"
                f"├ 📱 {h(context.user_data.get('phone', '—'))}\n"
                f"└ TG: @{h(user.username or 'немає')} (ID: {h(user.id)})\n\n"
                f"📦 <b>Доставка:</b>\n"
                f"└ {h(context.user_data.get('city', '—'))}, НП №{h(context.user_data.get('branch', '—'))}\n\n"
                f"💳 <b>Оплата:</b> {h(payment_method)}\n"
                f"📸 <b>Чек:</b> {'є' if payment_proof_id else 'немає'}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🛒 <b>Замовлення:</b>\n{items_text}\n\n"
                f"💰 <b>РАЗОМ: {h(total)} грн</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            await context.bot.send_message(
                chat_id=ORDERS_CHAT_ID,
                text=order_text,
                parse_mode=ParseMode.HTML
            )

        # Send payment proof if exists
        if payment_proof_id:
            await context.bot.send_photo(
                chat_id=ORDERS_CHAT_ID,
                photo=payment_proof_id,
                caption=f"📸 Чек від @{user.username or user.id}"
            )

        logger.info(f"Order sent to chat {ORDERS_CHAT_ID}")
    except Exception as e:
        logger.error(f"Failed to send order: {e}")

    # Confirm to user
    await update.message.reply_text(
        f"✅ *Замовлення прийнято!*\n\n"
        f"Менеджер зв'яжеться з вами найближчим часом.\n\n"
        f"📞 Для термінових питань: {MANAGER_USERNAME}",
        parse_mode="Markdown",
        reply_markup=build_start_keyboard()
    )

    context.user_data.clear()


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text("❌ Замовлення скасовано.", reply_markup=build_start_keyboard())


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle menu button presses."""
    text = (update.message.text or "").strip()

    # Try to parse as order (old ORDER: format or new clipboard format)
    result = None
    if text.startswith("ORDER:"):
        result = parse_order_text(text)
    elif 'SKU:' in text and 'грн' in text and 'Разом:' in text:
        result = parse_clipboard_order(text)

    if result:
        items, total = result
        context.user_data.clear()
        context.user_data["order_items"] = items
        context.user_data["order_total"] = total
        context.user_data["order_active"] = True
        context.user_data["group_message_sent"] = False
        context.user_data[STATE_KEY] = ASK_NAME
        items_text, _ = format_items(items)

        await update.message.reply_text(
            f"🛒 *Ваше замовлення:*\n\n{items_text}\n\n"
            f"💰 *Разом:* {total} грн\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Для оформлення введіть ваше *ім'я:*",
            parse_mode="Markdown",
            reply_markup=build_cancel_keyboard()
        )
        return

    if text.startswith(MENU_ORDER_SENT):
        await update.message.reply_text(
            f"✅ Отримано! Менеджер зв'яжеться. {MANAGER_USERNAME}",
            reply_markup=build_start_keyboard()
        )
        return

    if text == MENU_NEW_ORDER:
        await update.message.reply_text(f"🛒 Перейдіть на сайт {SITE_URL}, додайте товари в кошик і натисніть «Оформити»", reply_markup=build_site_keyboard())
        return

    if text == MENU_MANAGER:
        await update.message.reply_text(f"📞 Менеджер: {MANAGER_USERNAME}")
        return

    if text == MENU_SITE:
        await update.message.reply_text("🌐 Сайт:", reply_markup=build_site_keyboard())
        return

    await update.message.reply_text("Оберіть дію з меню.", reply_markup=build_start_keyboard())


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route text messages based on current state."""
    text = (update.message.text or "").strip()
    state = context.user_data.get(STATE_KEY)

    logger.info(f"text_router: state={state}, text='{text[:30]}...'")

    if text == CANCEL_TEXT:
        await handle_cancel(update, context)
        return

    state_handlers = {
        ASK_NAME: handle_name,
        ASK_SURNAME: handle_surname,
        ASK_PHONE: handle_phone,
        ASK_CITY: handle_city,
        ASK_BRANCH: handle_branch,
        CONFIRM_DATA: handle_confirmation,
        PAYMENT_METHOD: handle_payment_choice,
        WAITING_PAYMENT_PROOF: handle_payment_proof,
    }
    handler = state_handlers.get(state)
    if handler:
        await handler(update, context)
        return
    await menu_handler(update, context)


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages (payment proof)."""
    state = context.user_data.get(STATE_KEY)
    if state == WAITING_PAYMENT_PROOF:
        await handle_payment_proof(update, context)
    else:
        await update.message.reply_text("📸 Фото отримано, але зараз воно не потрібне.", reply_markup=build_start_keyboard())


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Error: %s", context.error)


def main() -> None:
    logger.info("Starting Yar4ick Technology Order Bot...")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    application.add_error_handler(error_handler)

    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
