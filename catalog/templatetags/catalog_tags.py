from django import template

register = template.Library()

CATEGORY_ICONS = {
    # ── Смартфони ─────────────────────────────────
    'smartphones':        ('bi-phone',              '#FF6600'),
    'iphone':             ('bi-apple',              '#A8A8A8'),
    'samsung':            ('bi-phone-flip',         '#1877F2'),
    'xiaomi':             ('bi-phone-vibrate',      '#FF6900'),
    'smartphones-other':  ('bi-phone-landscape',    '#888888'),

    # ── Ноутбуки / ПК ────────────────────────────
    'laptops-pk':         ('bi-laptop',             '#00B4D8'),
    'laptops':            ('bi-laptop',             '#00B4D8'),
    'computers':          ('bi-pc-display',         '#7B2FBE'),
    'components':         ('bi-cpu',                '#F72585'),

    # ── Планшети ─────────────────────────────────
    'tablets':            ('bi-tablet',             '#A855F7'),
    'ipad':               ('bi-tablet-landscape',   '#A8A8A8'),
    'galaxy-tab':         ('bi-tablet-fill',        '#1877F2'),
    'tablets-other':      ('bi-tablet-landscape',   '#888888'),

    # ── Ігрові приставки ─────────────────────────
    'gaming':             ('bi-controller',         '#FF6600'),
    'xbox':               ('bi-microsoft',          '#107C10'),
    'playstation':        ('bi-playstation',        '#003791'),
    'nintendo':           ('bi-nintendo-switch',    '#E4000F'),

    # ── Аксесуари та ігри ────────────────────────
    'accessories':        ('bi-bag',                '#2ECC71'),
    'controllers':        ('bi-joystick',           '#FF8800'),
    'games':              ('bi-disc',               '#9B59B6'),
    'chargers':           ('bi-lightning-charge',   '#F39C12'),
    'cases':              ('bi-shield-check',       '#3498DB'),

    # ── Додаткові ────────────────────────────────
    'headphones':         ('bi-headphones',         '#FF6600'),
    'monitors':           ('bi-display',            '#00B4D8'),
    'keyboards':          ('bi-keyboard',           '#F72585'),
    'mice':               ('bi-mouse',              '#7B2FBE'),
    'cables':             ('bi-usb-plug',           '#F39C12'),
    'memory':             ('bi-sd-card',            '#2ECC71'),
    'storage':            ('bi-hdd',                '#E74C3C'),
    'printers':           ('bi-printer',            '#95A5A6'),
    'cameras':            ('bi-camera',             '#E67E22'),
    'smartwatch':         ('bi-watch',              '#1877F2'),
    'speakers':           ('bi-speaker',            '#FF6600'),
    'powerbank':          ('bi-battery-charging',   '#27AE60'),
}

DEFAULT_ICON = ('bi-box-seam', '#FF6600')


@register.filter
def category_icon(slug):
    icon, _ = CATEGORY_ICONS.get(slug, DEFAULT_ICON)
    return icon


@register.filter
def category_color(slug):
    _, color = CATEGORY_ICONS.get(slug, DEFAULT_ICON)
    return color
