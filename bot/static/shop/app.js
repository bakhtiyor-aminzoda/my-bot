const tg = window.Telegram.WebApp;
tg.expand();
// Disable swipe-to-close
if (tg.isVerticalSwipesEnabled !== undefined) {
    tg.isVerticalSwipesEnabled = false;
}

// Ensure colors match theme immediately
tg.setHeaderColor("secondary_bg_color");
tg.setBackgroundColor("secondary_bg_color");

let products = [];
let cart = {}; // Object for fast lookup: { id: { product: p, qty: 1 } }

// Init
document.addEventListener('DOMContentLoaded', async () => {
    await fetchProducts();
    renderProducts('all');

    // User Info
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        const avatarEl = document.getElementById('user-avatar');

        if (user.photo_url) {
            avatarEl.src = user.photo_url;
            avatarEl.onerror = () => {
                avatarEl.src = `https://ui-avatars.com/api/?name=${user.first_name}&background=007AFF&color=fff`;
            };
        } else {
            avatarEl.src = `https://ui-avatars.com/api/?name=${user.first_name}&background=007AFF&color=fff`;
        }

        // Load Referral Stats
        loadReferralStats(user.id);
    }

    // MainButton Setup
    tg.MainButton.textColor = "#FFFFFF";
    tg.MainButton.color = "#007AFF";
    if (tg.themeParams.button_color) {
        tg.MainButton.color = tg.themeParams.button_color;
        tg.MainButton.textColor = tg.themeParams.button_text_color;
    }
});

async function loadReferralStats(userId) {
    try {
        const res = await fetch(`/api/client/referrals?user_id=${userId}`);
        const data = await res.json();

        if (data && typeof data.count === 'number') {
            document.getElementById('referral-stats').innerText = `Приглашено: ${data.count}`;
            document.getElementById('referral-card').style.display = 'block';
        }
    } catch (e) {
        console.error("Referral stats fail:", e);
    }
}

function copyReferralLink() {
    if (!tg.initDataUnsafe || !tg.initDataUnsafe.user) {
        tg.showAlert("Ошибка: Не удалось определить пользователя.");
        return;
    }

    // NOTE: Replace with your actual bot username if different.
    // If we are developing locally, user needs to manually adjust this.
    const botUsername = "ProgradeBot";
    const link = `https://t.me/${botUsername}?start=ref_${tg.initDataUnsafe.user.id}`;

    // Fallback copy mechanism (supports HTTP and older browsers)
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(link).then(showCopyFeedback).catch(err => {
            console.error('Async: Could not copy text: ', err);
            fallbackCopyTextToClipboard(link);
        });
    } else {
        fallbackCopyTextToClipboard(link);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // Ensure it's not visible
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopyFeedback();
        } else {
            tg.showAlert("Не удалось скопировать ссылку. Попробуйте вручную: " + text);
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        tg.showAlert("Ошибка копирования: " + err);
    }

    document.body.removeChild(textArea);
}

function showCopyFeedback() {
    const feedback = document.getElementById('ref-copy-feedback');
    if (feedback) {
        feedback.style.opacity = '1';
        setTimeout(() => feedback.style.opacity = '0', 2000);
    }
    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

function renderProducts(filter) {
    const container = document.getElementById('product-grid');
    container.innerHTML = '';

    products.forEach(p => {
        if (filter !== 'all' && p.category !== filter) return;

        // Check if in cart
        const inCart = cart[p.id] ? cart[p.id].qty : 0;
        const btnText = inCart > 0 ? `${inCart} шт` : '+';
        const btnClass = inCart > 0 ? 'add-btn active' : 'add-btn';

        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <div>
                <div class="icon-box">${p.icon}</div>
                <h3 class="product-title">${p.title}</h3>
                <p class="product-desc">${p.desc}</p>
            </div>
            <div class="price-row">
                <span class="price">${p.price} TJS</span>
                <button class="${btnClass}" onclick="addToCart(${p.id})">${btnText}</button>
            </div>
        `;
        container.appendChild(card);
    });

    // Update tabs UI
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    // Safe selection
    const activeTab = document.querySelector(`.tab[onclick="filter('${filter}')"]`);
    if (activeTab) activeTab.classList.add('active');
}

async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        if (response.ok) {
            products = await response.json();
            console.log("Products loaded:", products);
        } else {
            console.error("Failed to load products");
            tg.showPopup({ title: 'Error', message: 'Failed to load products' });
        }
    } catch (e) {
        console.error("Error loading products:", e);
    }
}

function filter(cat) {
    renderProducts(cat);
}

function addToCart(id) {
    try {
        // Optimize: Check cart first
        if (cart[id]) {
            cart[id].qty++;
        } else {
            const product = products.find(p => p.id === id);
            if (!product) {
                console.error("Product not found:", id);
                return;
            }
            cart[id] = { product: product, qty: 1 };
        }

        updateCartUI();

        // Re-render grid counters
        // Using a try-catch for the DOM manipulation specifically
        try {
            const activeTabObj = document.querySelector('.tab.active');
            if (activeTabObj) {
                const match = activeTabObj.getAttribute('onclick').match(/'([^']+)'/);
                if (match) renderProducts(match[1]);
            }
        } catch (domErr) {
            console.warn("Grid update skipped:", domErr);
        }

        // Force re-render modal
        const modal = document.getElementById('checkout-modal');
        if (modal && modal.classList.contains('active')) {
            openCheckout();
        }

        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    } catch (e) {
        console.error("Cart Add Error:", e);
        tg.showAlert("Error adding to cart: " + e.message);
    }
}

function removeFromCart(id) {
    try {
        if (cart[id]) {
            cart[id].qty--;
            if (cart[id].qty <= 0) {
                delete cart[id];
            }
        }
        updateCartUI();

        // Safely re-render grid
        const activeTabObj = document.querySelector('.tab.active');
        if (activeTabObj) {
            const match = activeTabObj.getAttribute('onclick').match(/'([^']+)'/);
            const currentFilter = match ? match[1] : 'all';
            renderProducts(currentFilter);
        }

        // Force re-render modal
        const modal = document.getElementById('checkout-modal');
        if (modal && modal.classList.contains('active')) {
            openCheckout();
        }

        if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    } catch (e) {
        console.error("Cart remove error:", e);
    }
}

function updateCartUI() {
    const total = Object.values(cart).reduce((sum, item) => sum + (item.product.price * item.qty), 0);

    if (total > 0) {
        tg.MainButton.setText(`Оформить заказ: ${total} TJS`);
        if (!tg.MainButton.isVisible) {
            tg.MainButton.show();
        }

        // Clean up all potential listeners to avoid duplicates or errors
        // We removed 'submitOrder' so checking it causes ReferenceError
        tg.MainButton.offClick(openCheckout);
        tg.MainButton.offClick(proceedToPayment);
        tg.MainButton.offClick(finalizeOrder);

        // Set the correct entry point listener
        tg.MainButton.onClick(openCheckout);
    } else {
        tg.MainButton.hide();
        document.getElementById('checkout-modal').classList.remove('active');
    }
}

// Modal
function openCheckout() {
    const cartItems = Object.values(cart);
    if (cartItems.length === 0) return;

    const modal = document.getElementById('checkout-modal');
    const list = document.getElementById('cart-items');

    list.innerHTML = '';
    let total = 0;

    cartItems.forEach(item => {
        const p = item.product;
        total += p.price * item.qty;

        const div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px; width: 100%;">
                <div style="margin-right:auto;">
                    <div class="cart-item-title">${p.title}</div>
                    <div class="cart-item-price">${p.price} TJS</div>
                </div>
                
                <div class="qty-controls" style="display:flex; align-items:center; gap:10px;">
                    <button class="qty-btn" onclick="removeFromCart(${p.id})">➖</button>
                    <span style="font-weight:600; min-width:20px; text-align:center;">${item.qty}</span>
                    <button class="qty-btn" onclick="addToCart(${p.id})">➕</button>
                </div>
            </div>
        `;
        list.appendChild(div);
    });

    document.getElementById('cart-total').innerText = `${total} TJS`;
    modal.classList.add('active');

    tg.MainButton.setText(`Оплатить ${total} TJS`);
    tg.MainButton.offClick(openCheckout);
    tg.MainButton.onClick(proceedToPayment);
}

function closeCheckout() {
    document.getElementById('checkout-modal').classList.remove('active');
    updateCartUI();
}

// Submit Order
// Submit Logic Split
function proceedToPayment() {
    const contact = document.getElementById('order-contact').value;

    // Validate Contact first
    if (!contact || contact.length < 5) {
        tg.showPopup({
            title: "Контакт обязателен",
            message: "Пожалуйста, укажите телефон или @username, чтобы мы могли связаться с вами.",
            buttons: [{ type: "ok" }]
        });
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
        return;
    }

    const total = Object.values(cart).reduce((sum, item) => sum + (item.product.price * item.qty), 0);

    // Populate Payment Modal
    document.getElementById('payment-amount').innerText = `${total} TJS`;

    // Show Modal
    document.getElementById('payment-modal').classList.add('active');

    // Update MainButton to "I Paid"
    tg.MainButton.setText(`✅ Я оплатил ${total} TJS`);
    tg.MainButton.offClick(proceedToPayment); // Remove old listener
    tg.MainButton.offClick(finalizeOrder); // Dedupe
    tg.MainButton.onClick(finalizeOrder);
}

function closePayment() {
    document.getElementById('payment-modal').classList.remove('active');

    // Revert MainButton to "Checkout" logic
    const total = Object.values(cart).reduce((sum, item) => sum + (item.product.price * item.qty), 0);
    tg.MainButton.setText(`Оплатить ${total} TJS`);
    tg.MainButton.offClick(finalizeOrder);
    tg.MainButton.onClick(proceedToPayment);
}

function copyToClipboard(text, feedbackId) {
    navigator.clipboard.writeText(text).then(() => {
        const feedback = document.getElementById(feedbackId);
        if (feedback) {
            feedback.style.opacity = '1';
            setTimeout(() => feedback.style.opacity = '0', 2000);
        }
        if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    });
}

// Final Submit
async function finalizeOrder() {
    tg.MainButton.showProgress();

    const contact = document.getElementById('order-contact').value;
    const comment = document.getElementById('order-comment').value;
    const cartItems = Object.values(cart);
    const total = cartItems.reduce((sum, item) => sum + (item.product.price * item.qty), 0);
    const user = tg.initDataUnsafe.user || { id: 0, first_name: "Guest" };

    const orderData = {
        user_id: user.id,
        name: user.first_name + (user.last_name ? " " + user.last_name : ""),
        contact_info: contact,
        items: cartItems.map(i => ({ ...i.product, quantity: i.qty })),
        total: total,
        comment: comment + " [PAID VIA QR]"
    };

    try {
        const response = await fetch('/api/client/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        if (response.ok) {
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
            tg.MainButton.hideProgress();
            tg.close();
        } else {
            throw new Error("Server Error");
        }
    } catch (e) {
        tg.MainButton.hideProgress();
        tg.showPopup({
            title: "Ошибка",
            message: "Не удалось оформить заказ. Проверьте интернет.",
            buttons: [{ type: "ok" }]
        });
    }
}
