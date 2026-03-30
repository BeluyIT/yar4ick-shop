const DEBUG_CART = false;
const log = (...args) => {
    if (DEBUG_CART) {
        console.log(...args);
    }
};
const warn = (...args) => {
    if (DEBUG_CART) {
        console.warn(...args);
    }
};

// Fallback: clear cart if order was just sent (session flag)
(function () {
    const orderJustSent = sessionStorage.getItem('order_just_sent');
    if (orderJustSent) {
        log('[Cart] Order was just sent, clearing cart');
        try {
            localStorage.removeItem('antidrone_cart');
            localStorage.removeItem('antidrone_cart_v1');
            localStorage.removeItem('cart');
        } catch (err) {
            console.error('[Cart] Failed to clear cart from localStorage:', err);
        }
        sessionStorage.removeItem('order_just_sent');

        if (typeof updateCartBadge === 'function') {
            updateCartBadge();
        }
    }
})();

const CART_KEY = 'antidrone_cart';
const LEGACY_KEYS = ['antidrone_cart_v1'];

window.updateCartBadge = () => {
    log('[cart] updateCartBadge called');
    let cart = {};
    try {
        cart = JSON.parse(localStorage.getItem(CART_KEY) || '{}') || {};
    } catch (err) {
        console.error('[cart] Failed to parse cart:', err);
        cart = {};
    }
    if (!cart.items || typeof cart.items !== 'object') {
        cart.items = {};
    }
    const qty = Object.values(cart.items).reduce((sum, item) => sum + (Number(item.qty) || 0), 0);
    log('[cart] Total quantity:', qty);

    const badges = [];
    const badge = document.getElementById('cartBadge');
    if (badge) {
        badges.push(badge);
        log('[cart] Found badge by ID: cartBadge');
    } else {
        warn('[cart] Badge element #cartBadge NOT FOUND');
    }
    document.querySelectorAll('.js-cart-badge').forEach((node) => badges.push(node));

    log('[cart] Total badges found:', badges.length);
    if (!badges.length) {
        warn('[cart] No badge elements found!');
        return;
    }

    badges.forEach((node, index) => {
        node.textContent = String(qty);
        if (qty > 0) {
            node.removeAttribute('hidden');
            log(`[cart] Badge ${index}: showing with qty=${qty}`);
        } else {
            node.setAttribute('hidden', '');
            log(`[cart] Badge ${index}: hidden (qty=0)`);
        }
    });
};

function addToCart(button) {
    log('[cart] addToCart called', button);
    if (!window.__cartAddItem) {
        log('[cart] addToCart called before cart init, fallback to direct save');
    }
    if (!button || !button.dataset) {
        return;
    }
    const item = {
        id: String(button.dataset.productId || button.dataset.id || ''),
        name: button.dataset.name || 'Товар',
        sku: button.dataset.sku || '',
        price: Number(button.dataset.price) || 0,
        image: button.dataset.image || '',
        url: button.dataset.url || '',
        qty: 1,
    };
    if (!item.id) return;
    if (window.__cartAddItem) {
        window.__cartAddItem(item);
    } else {
        let cart = {};
        try {
            cart = JSON.parse(localStorage.getItem(CART_KEY) || '{}') || {};
        } catch (err) {
            cart = {};
        }
        if (!cart.items || typeof cart.items !== 'object') {
            cart.items = {};
        }
        const existing = cart.items[item.id];
        if (existing) {
            existing.qty = (Number(existing.qty) || 0) + 1;
            if (!existing.image && item.image) {
                existing.image = item.image;
            }
        } else {
            cart.items[item.id] = item;
        }
        log('[cart] before save', cart);
        localStorage.setItem(CART_KEY, JSON.stringify(cart));
        log('[cart] after save', localStorage.getItem(CART_KEY));
        if (window.__cartUpdateBadge) {
            window.__cartUpdateBadge();
        }
        if (window.updateCartBadge) {
            window.updateCartBadge();
        }
        if (window.__cartRenderPage) {
            window.__cartRenderPage();
        }
    }

    showAddToCartAnimation(button);
}

function showAddToCartAnimation(btn) {
    log('[cart] Starting animation');

    // 1. Button animation - change text
    if (btn && btn.tagName === 'BUTTON') {
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check-lg"></i> Додано!';
        btn.classList.add('btn-added');
        btn.disabled = true;

        setTimeout(() => {
            btn.classList.remove('btn-added');
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }, 1500);
    }

    // 2. Cart icon bounce animation
    const cartLink = document.querySelector('.header-cart');
    if (cartLink) {
        cartLink.classList.add('cart-bounce');
        setTimeout(() => cartLink.classList.remove('cart-bounce'), 600);
    }

    // 3. Badge bounce
    const badge = document.getElementById('cartBadge');
    if (badge) {
        badge.classList.add('badge-bounce');
        setTimeout(() => badge.classList.remove('badge-bounce'), 400);
    }

    log('[cart] Animation complete');
}

window.addToCart = addToCart;
window.showAddToCartAnimation = showAddToCartAnimation;
log('[cart] cart.js loaded; window.addToCart =', typeof window.addToCart);

(() => {
    log('cart.js loaded');

    const safeParse = (value) => {
        if (!value) return null;
        try {
            return JSON.parse(value);
        } catch (err) {
            return null;
        }
    };

    const loadStoredCart = () => {
        let raw = localStorage.getItem(CART_KEY);
        if (!raw) {
            for (const key of LEGACY_KEYS) {
                raw = localStorage.getItem(key);
                if (raw) {
                    localStorage.setItem(CART_KEY, raw);
                    localStorage.removeItem(key);
                    log('migrated cart key', key, '->', CART_KEY);
                    break;
                }
            }
        }
        log('load cart raw', raw);
        return safeParse(raw) || {};
    };

    const getCart = () => {
        const data = loadStoredCart();
        if (!data.items || typeof data.items !== 'object') {
            data.items = {};
        }
        return data;
    };

    const saveCart = (cart) => {
        localStorage.setItem(CART_KEY, JSON.stringify(cart));
        log('save cart', cart);
        if (window.updateCartBadge) {
            window.updateCartBadge();
        }
    };

    const clearCart = () => {
        const cart = { items: {} };
        saveCart(cart);
        renderCartPage();
    };

    // Auto-cleanup: Set order timestamp
    const setOrderTimestamp = () => {
        localStorage.setItem('order_timestamp', Date.now());
        log('Order timestamp set');
    };

    // Auto-cleanup: Check if cart should be cleared (20 minutes after order)
    const checkAutoCleanCart = () => {
        const orderTime = localStorage.getItem('order_timestamp');
        if (!orderTime) return;

        const elapsed = Date.now() - parseInt(orderTime);
        const TWENTY_MINUTES = 20 * 60 * 1000; // 20 minutes in milliseconds

        if (elapsed > TWENTY_MINUTES) {
            clearCart();
            localStorage.removeItem('order_timestamp');
            log('Auto-cleaned cart after 20 minutes');
        }
    };

    const getTotalQty = (cart) => {
        return Object.values(cart.items).reduce((sum, item) => sum + (Number(item.qty) || 0), 0);
    };

    const formatPrice = (value) => {
        const amount = Number(value) || 0;
        return new Intl.NumberFormat('uk-UA', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const buildTelegramMessage = (item) => {
        const priceValue = Number(item.price) || 0;
        const priceText = priceValue > 0 ? `${formatPrice(priceValue)} UAH` : 'ціна за запитом';
        const lines = [
            'Запит на товар:',
            item.name ? `Назва: ${item.name}` : null,
            `Ціна: ${priceText}`,
        ].filter(Boolean);
        return lines.join('\n');
    };

    const openTelegramOrder = (button) => {
        const handle = button.dataset.telegram || 'yar4ick_tech';
        const item = {
            name: button.dataset.name || 'Товар',
            price: Number(button.dataset.price) || 0,
        };
        const message = buildTelegramMessage(item);
        const url = `https://t.me/${handle}?text=${encodeURIComponent(message)}`;
        window.open(url, '_blank', 'noopener');
    };

    const addItem = (item) => {
        const cart = getCart();
        const existing = cart.items[item.id];
        if (existing) {
            existing.qty = (Number(existing.qty) || 0) + (Number(item.qty) || 1);
            if (!existing.image && item.image) {
                existing.image = item.image;
            }
            if (!existing.url && item.url) {
                existing.url = item.url;
            }
        } else {
            cart.items[item.id] = { ...item, qty: Number(item.qty) || 1 };
        }
        log('before save', cart);
        log('add item', item);
        saveCart(cart);
        log('after save', localStorage.getItem(CART_KEY));
    };

    window.__cartAddItem = addItem;

    const updateItemQty = (id, delta) => {
        const cart = getCart();
        const item = cart.items[id];
        if (!item) return;
        const nextQty = (Number(item.qty) || 0) + delta;
        if (nextQty <= 0) {
            delete cart.items[id];
        } else {
            item.qty = nextQty;
        }
        saveCart(cart);
        renderCartPage();
    };

    const removeItem = (id) => {
        const cart = getCart();
        if (cart.items[id]) {
            delete cart.items[id];
            saveCart(cart);
            renderCartPage();
        }
    };

    const renderCartPage = () => {
        const container = document.getElementById('cart-items');
        const summary = document.getElementById('cart-summary');
        if (!container || !summary) return;

        const cart = getCart();
        const items = Object.values(cart.items);
        log('render cart items', items.length);

        const totalEl = summary.querySelector('#cart-total');
        const checkoutButton = summary.querySelector('.btn-checkout');
        const clearButton = summary.querySelector('.btn-clear-cart');

        if (!items.length) {
            const catalogUrl = container.dataset.catalogUrl || '/catalog/';
            container.innerHTML = `<div class="cart-empty"><div class="cart-empty-text">Кошик порожній.</div><a class="btn btn-primary btn-ghost" href="${catalogUrl}">Перейти до каталогу</a></div>`;
            if (totalEl) {
                totalEl.textContent = 'Разом: 0 грн';
            }
            if (checkoutButton) {
                checkoutButton.setAttribute('aria-disabled', 'true');
                checkoutButton.dataset.cartEmpty = 'true';
            }
            if (clearButton) {
                clearButton.disabled = true;
            }
            return;
        }

        let total = 0;
        const rows = items.map((item) => {
            const price = Number(item.price) || 0;
            const qty = Number(item.qty) || 0;
            const lineTotal = price * qty;
            total += lineTotal;
            const thumb = item.image
                ? `<img src="${item.image}" alt="${item.name || 'Товар'}">`
                : `<div class="cart-thumb-placeholder"></div>`;
            const nameHTML = item.name || 'Товар';
            const linkOpen = item.url ? `<a href="${item.url}" class="cart-item-link">` : '';
            const linkClose = item.url ? '</a>' : '';
            return `
                <div class="cart-row">
                    <div class="cart-cell cart-thumb">${linkOpen}${thumb}${linkClose}</div>
                    <div class="cart-cell">
                        ${linkOpen}<div class="cart-title">${nameHTML}</div>${linkClose}
                    </div>
                    <div class="cart-cell cart-price">${formatPrice(price)} UAH</div>
                    <div class="cart-cell cart-qty">
                        <button class="btn btn-primary btn-qty" data-cart-action="dec" data-cart-id="${item.id}">−</button>
                        <span class="cart-qty-value">${qty}</span>
                        <button class="btn btn-primary btn-qty" data-cart-action="inc" data-cart-id="${item.id}">+</button>
                    </div>
                    <div class="cart-cell cart-line-total">${formatPrice(lineTotal)} UAH</div>
                    <div class="cart-cell cart-actions">
                        <button class="btn btn-primary btn-remove" data-cart-action="remove" data-cart-id="${item.id}">Видалити</button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = rows.join('');
        if (totalEl) {
            totalEl.textContent = `Разом: ${formatPrice(total)} грн`;
        }
        if (checkoutButton) {
            checkoutButton.removeAttribute('aria-disabled');
            checkoutButton.dataset.cartEmpty = 'false';
        }
        if (clearButton) {
            clearButton.disabled = false;
        }
    };

    document.addEventListener('click', (event) => {
        const productCard = event.target.closest('.product-card[data-product-url]');
        if (productCard) {
            const isAction = event.target.closest('a, button');
            if (!isAction) {
                const url = productCard.dataset.productUrl;
                if (url) {
                    window.location.href = url;
                    return;
                }
            }
        }

        const addButton = event.target.closest('.js-add-to-cart');
        if (addButton) {
            // Only handle non-direct mode (direct mode uses onclick)
            if (addButton.dataset.addMode !== 'direct') {
                log('add button click', addButton.dataset);
                window.addToCart(addButton);
            }
            return;
        }

        const telegramButton = event.target.closest('.js-telegram-order');
        if (telegramButton) {
            event.preventDefault();
            openTelegramOrder(telegramButton);
            return;
        }

        const checkoutTrigger = event.target.closest('[data-checkout-start]');
        if (checkoutTrigger) {
            event.preventDefault();
            startCheckout();
            return;
        }

        const confirmTrigger = event.target.closest('[data-checkout-confirm], [data-action="confirm-order"]');
        if (confirmTrigger) {
            event.preventDefault();
            checkoutToTelegram();
            return;
        }

        const actionButton = event.target.closest('[data-cart-action]');
        if (!actionButton) return;

        const action = actionButton.dataset.cartAction;
        const id = String(actionButton.dataset.cartId || '');

        if (action === 'clear') {
            clearCart();
            return;
        }

        if (!id) return;

        if (action === 'inc') {
            updateItemQty(id, 1);
        } else if (action === 'dec') {
            updateItemQty(id, -1);
        } else if (action === 'remove') {
            removeItem(id);
        }
    });

    // Auto-clear cart when redirected from bot with ?confirmed_order=
    const checkConfirmedOrder = () => {
        const params = new URLSearchParams(window.location.search);
        if (params.has('confirmed_order')) {
            log('Confirmed order detected, clearing cart');
            clearCart();
            localStorage.removeItem('order_timestamp');
            // Clean URL without reloading
            const url = new URL(window.location);
            url.searchParams.delete('confirmed_order');
            window.history.replaceState({}, '', url.pathname + url.search);
        }
    };

    // Check if user recently sent an order (e.g. returning from bot tab)
    const checkRecentOrder = () => {
        const orderSent = localStorage.getItem('order_sent');
        const orderTime = localStorage.getItem('order_time');

        if (orderSent && orderTime) {
            const elapsed = Date.now() - parseInt(orderTime);
            const FIVE_MINUTES = 5 * 60 * 1000;

            if (elapsed < FIVE_MINUTES) {
                log('Recently sent order, cart remains cleared');
                if (window.updateCartBadge) {
                    window.updateCartBadge();
                }
                // If on cart page, show success message
                const cartContainer = document.getElementById('cart-items');
                if (cartContainer) {
                    const cart = getCart();
                    const items = Object.values(cart.items);
                    if (!items.length) {
                        cartContainer.innerHTML = '';
                        try {
                            renderSuccessModal({ showTelegramLink: true });
                        } catch (err) {
                            // ignore
                        }
                    }
                }
            } else {
                // Remove stale flags
                localStorage.removeItem('order_sent');
                localStorage.removeItem('order_time');
            }
        }
    };

    document.addEventListener('DOMContentLoaded', () => {
        log('[cart] DOMContentLoaded fired');
        checkConfirmedOrder();
        checkAutoCleanCart();
        checkRecentOrder();
        if (window.updateCartBadge) {
            window.updateCartBadge();
            log('[cart] Badge updated on DOMContentLoaded');
        }
        renderCartPage();

        // Confirm button handler is bound via event delegation above.
    });

    const checkoutState = {
        items: [],
        total: 0,
        isSubmitting: false,
    };

    const getCookie = (name) => {
        const match = document.cookie.match(new RegExp(`(?:^|; )${name.replace(/([$?*|{}\]\\^])/g, '\\$1')}=([^;]*)`));
        return match ? decodeURIComponent(match[1]) : '';
    };

    const showToast = (message, tone = 'error') => {
        const toast = document.getElementById('checkout-toast');
        if (!toast) {
            alert(message);
            return;
        }
        toast.textContent = message;
        toast.classList.toggle('is-error', tone === 'error');
        toast.classList.add('is-visible');
        toast.removeAttribute('hidden');
        clearTimeout(toast.__hideTimer);
        toast.__hideTimer = setTimeout(() => {
            toast.classList.remove('is-visible');
            toast.setAttribute('hidden', '');
        }, 4200);
    };

    const renderCheckoutPreview = () => {
        const itemsContainer = document.getElementById('checkout-modal-items');
        const totalContainer = document.getElementById('checkout-modal-total');
        if (!itemsContainer || !totalContainer) return;

        if (!checkoutState.items.length) {
            itemsContainer.innerHTML = '<div class="checkout-modal-empty">Кошик порожній.</div>';
            totalContainer.textContent = '';
            return;
        }

        const rows = checkoutState.items.map((item) => {
            const name = item.name || 'Товар';
            const qty = Number(item.qty) || 1;
            return `
                <div class="checkout-modal-row">
                    <span class="checkout-modal-name">${name}</span>
                    <span class="checkout-modal-qty">× ${qty}</span>
                </div>
            `;
        });

        itemsContainer.innerHTML = rows.join('');
        totalContainer.textContent = `Разом: ${formatPrice(checkoutState.total)} грн`;
    };

    const openCheckoutModal = () => {
        const modal = document.getElementById('checkout-modal');
        if (!modal) {
            showToast('Не вдалося відкрити вікно підтвердження.');
            return;
        }
        const errorBox = document.getElementById('checkout-modal-error');
        if (errorBox) {
            errorBox.textContent = '';
            errorBox.setAttribute('hidden', '');
        }
        renderCheckoutPreview();
        modal.removeAttribute('hidden');
        modal.classList.add('is-open');
        document.body.classList.add('modal-open');
    };

    const closeCheckoutModal = () => {
        const modal = document.getElementById('checkout-modal');
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.setAttribute('hidden', '');
        document.body.classList.remove('modal-open');
    };

    const buildOrderPayload = () => ({
        items: checkoutState.items.map((item) => ({
            sku: String(item.sku || '').trim(),
            name: String(item.name || 'Товар').trim(),
            price: Math.round(Number(item.price) || 0),
            qty: Math.max(1, Math.round(Number(item.qty) || 1)),
        })),
        total: Math.round(Number(checkoutState.total) || 0),
        currency: 'UAH',
        source: 'site',
        page: window.location.href,
        ts: Date.now(),
    });

    const createOrder = async () => {
        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            throw new Error('Не вдалося отримати CSRF токен.');
        }

        const response = await fetch('/api/create-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(buildOrderPayload()),
        });

        if (!response.ok) {
            let errorMessage = 'Помилка при створенні замовлення.';
            try {
                const data = await response.json();
                if (data && data.error) {
                    errorMessage = data.error;
                }
            } catch (err) {
                // ignore parsing errors
            }
            throw new Error(errorMessage);
        }

        return response.json();
    };

    const renderSuccessModal = (options = {}) => {
        const { showTelegramLink = true } = options;
        const modal = document.getElementById('checkout-modal');
        if (!modal) return;
        const title = modal.querySelector('#checkout-modal-title');
        const subtitle = modal.querySelector('.checkout-modal-subtitle');
        const itemsContainer = modal.querySelector('#checkout-modal-items');
        const totalContainer = modal.querySelector('#checkout-modal-total');
        const errorBox = modal.querySelector('#checkout-modal-error');
        const actions = modal.querySelector('.checkout-modal-actions');

        if (title) title.textContent = '✅ Замовлення успішно надіслане';
        if (subtitle) {
            subtitle.textContent = showTelegramLink
                ? 'Перевірте Telegram для продовження.'
                : 'Telegram вже відкрито у новій вкладці.';
        }
        if (itemsContainer) itemsContainer.innerHTML = '';
        if (totalContainer) totalContainer.textContent = '';
        if (errorBox) {
            errorBox.textContent = '';
            errorBox.setAttribute('hidden', '');
        }
        if (actions) {
            actions.innerHTML = showTelegramLink
                ? `
                    <a class="btn btn-primary" href="https://t.me/yar4ick_order_bot" target="_blank" rel="noopener">Відкрити Telegram</a>
                    <a class="btn btn-primary" href="/">На головну</a>
                  `
                : `
                    <a class="btn btn-primary" href="/">На головну</a>
                  `;
        }

        modal.removeAttribute('hidden');
        modal.classList.add('is-open');
        document.body.classList.add('modal-open');
    };

    const startCheckout = () => {
        const cart = getCart();
        const items = Object.values(cart.items || {});
        if (!items.length) {
            showToast('Кошик порожній.');
            return;
        }
        checkoutState.items = items;
        checkoutState.total = items.reduce(
            (sum, item) => sum + (Number(item.price) || 0) * (Number(item.qty) || 1),
            0
        );
        openCheckoutModal();
    };

    const checkoutToTelegram = async () => {
        if (checkoutState.isSubmitting) return;
        checkoutState.isSubmitting = true;
        log('[Cart] checkoutToTelegram called');

        // Open Telegram immediately to keep popup tied to user gesture.
        let botPopup = null;
        try {
            botPopup = window.open('https://t.me/yar4ick_order_bot', '_blank', 'noopener');
        } catch (err) {
            botPopup = null;
        }

        const confirmBtn = document.querySelector('.btn-checkout-confirm, [data-action="confirm-order"], [data-checkout-confirm]');
        if (confirmBtn) {
            confirmBtn.setAttribute('disabled', '');
            confirmBtn.classList.add('is-loading');
        }

        const errorBox = document.getElementById('checkout-modal-error');
        if (errorBox) {
            errorBox.textContent = '';
            errorBox.setAttribute('hidden', '');
        }

        const cartData = getCart();
        const cartItems = Object.values(cartData.items || {});
        log('[Cart] Current cart:', cartItems);

        if (!cartItems.length) {
            const message = 'Кошик порожній!';
            if (errorBox) {
                errorBox.textContent = message;
                errorBox.removeAttribute('hidden');
            } else {
                alert(message);
            }
            checkoutState.isSubmitting = false;
            if (confirmBtn) {
                confirmBtn.removeAttribute('disabled');
                confirmBtn.classList.remove('is-loading');
            }
            return;
        }

        if (!checkoutState.items.length) {
            checkoutState.items = cartItems;
            checkoutState.total = cartItems.reduce(
                (sum, item) => sum + (Number(item.price) || 0) * (Number(item.qty) || 1),
                0
            );
        }

        try {
            const data = await createOrder();
            const orderId = data && data.order_id ? String(data.order_id) : '';
            if (!orderId) {
                throw new Error('Не вдалося отримати номер замовлення.');
            }

            try {
                localStorage.removeItem(CART_KEY);
                localStorage.removeItem('cart');
                LEGACY_KEYS.forEach((key) => localStorage.removeItem(key));
                sessionStorage.setItem('order_just_sent', 'true');
                localStorage.setItem('order_sent', 'true');
                localStorage.setItem('order_time', String(Date.now()));
                setOrderTimestamp();
                log('[Cart] ✅ Cart cleared from localStorage');
            } catch (err) {
                console.error('[Cart] ❌ Failed to clear cart:', err);
            }

            checkoutState.items = [];
            checkoutState.total = 0;

            try {
                if (window.updateCartBadge) {
                    window.updateCartBadge();
                }
                log('[Cart] ✅ Badge updated');
            } catch (err) {
                console.error('[Cart] ❌ Failed to update badge:', err);
            }

            try {
                closeCheckoutModal();
                log('[Cart] ✅ Modal closed');
            } catch (err) {
                console.error('[Cart] ❌ Failed to close modal:', err);
            }

            if (window.location.pathname.includes('/cart')) {
                try {
                    const popupOpened = !!botPopup;
                    renderSuccessModal({ showTelegramLink: !popupOpened });
                    log('[Cart] ✅ Success modal shown');
                } catch (err) {
                    console.error('[Cart] ❌ Failed to show success modal:', err);
                }
            }

            const botUsername = 'yar4ick_order_bot';
            const botUrl = `https://t.me/${botUsername}?start=${encodeURIComponent(orderId)}`;

            log('[Cart] Opening bot:', botUrl);

            try {
                if (botPopup && !botPopup.closed) {
                    botPopup.location.href = botUrl;
                }
                // If popup was blocked, we don't auto-redirect this tab.
                // User can use the "Open Telegram" link in the success modal.
            } catch (err) {
                // ignore
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Не вдалося оформити замовлення.';
            if (errorBox) {
                errorBox.textContent = message;
                errorBox.removeAttribute('hidden');
            } else {
                showToast(message);
            }
        } finally {
            checkoutState.isSubmitting = false;
            if (confirmBtn) {
                confirmBtn.removeAttribute('disabled');
                confirmBtn.classList.remove('is-loading');
            }
        }
    };

    const bindCheckoutModal = () => {
        const modal = document.getElementById('checkout-modal');
        if (!modal) return;

        modal.addEventListener('click', (event) => {
            const closeTarget = event.target.closest('[data-checkout-close]');
            if (closeTarget) {
                closeCheckoutModal();
            }
        });

        const cancelButton = modal.querySelector('[data-checkout-cancel]');
        if (cancelButton) {
            cancelButton.addEventListener('click', () => closeCheckoutModal());
        }
    };

    window.__checkoutStart = startCheckout;
    bindCheckoutModal();

    // Mobile menu toggle
    const initMobileMenu = () => {
        log('[Mobile Menu] Initializing...');
        const toggle = document.querySelector('.mobile-toggle');
        const mobileNav = document.getElementById('mobile-nav');
        log('[Mobile Menu] Elements:', { toggle, mobileNav });

        if (!toggle || !mobileNav) {
            console.error('[Mobile Menu] Elements not found!');
            return;
        }

        toggle.addEventListener('click', () => {
            log('[Mobile Menu] Toggle clicked!');
            const isOpen = mobileNav.classList.toggle('is-open');
            log('[Mobile Menu] Is open:', isOpen);
            toggle.classList.toggle('is-active', isOpen);
            toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');

            const icon = toggle.querySelector('i');
            if (icon) {
                icon.classList.toggle('bi-list', !isOpen);
                icon.classList.toggle('bi-x-lg', isOpen);
            }
        });

        // Close menu when clicking on a link
        mobileNav.addEventListener('click', (e) => {
            if (e.target.closest('a')) {
                mobileNav.classList.remove('is-open');
                toggle.classList.remove('is-active');
                toggle.setAttribute('aria-expanded', 'false');
                const icon = toggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('bi-x-lg');
                    icon.classList.add('bi-list');
                }
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (mobileNav.classList.contains('is-open') &&
                !mobileNav.contains(e.target) &&
                !toggle.contains(e.target)) {
                log('[Mobile Menu] Closing (clicked outside)');
                mobileNav.classList.remove('is-open');
                toggle.classList.remove('is-active');
                toggle.setAttribute('aria-expanded', 'false');
                const icon = toggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('bi-x-lg');
                    icon.classList.add('bi-list');
                }
            }
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileMenu);
    } else {
        initMobileMenu();
    }

    // Also update badge immediately if DOM is already ready
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        log('[cart] DOM already ready, updating badge immediately');
        setTimeout(() => {
            if (window.updateCartBadge) {
                window.updateCartBadge();
            }
        }, 0);
    }

    window.__cartUpdateBadge = window.updateCartBadge;
    window.__cartRenderPage = renderCartPage;
})();
