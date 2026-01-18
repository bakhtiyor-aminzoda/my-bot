const tg = window.Telegram.WebApp;
tg.expand();

// Ensure colors match theme immediately
tg.setHeaderColor("secondary_bg_color");
tg.setBackgroundColor("secondary_bg_color");

let products = [];
let cart = [];

// Init
document.addEventListener('DOMContentLoaded', async () => {
    await fetchProducts();
    renderProducts('all');

    // User Info
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        if (user.photo_url) document.getElementById('user-avatar').src = user.photo_url;
    }

    // MainButton Setup
    tg.MainButton.textColor = "#FFFFFF";
    tg.MainButton.color = "#007AFF"; // Or use theme params if needed
    if (tg.themeParams.button_color) {
        tg.MainButton.color = tg.themeParams.button_color;
        tg.MainButton.textColor = tg.themeParams.button_text_color;
    }
});

function renderProducts(filter) {
    const container = document.getElementById('product-grid');
    container.innerHTML = '';

    products.forEach(p => {
        if (filter !== 'all' && p.category !== filter) return;
    });

    async function fetchProducts() {
        try {
            const response = await fetch('/api/products');
            if (response.ok) {
                products = await response.json();
                console.log("Products loaded:", products);
            } else {
                console.error("Failed to load products");
            }
        } catch (e) {
            console.error("Error loading products:", e);
        }
    }
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
                <button class="add-btn" onclick="addToCart(${p.id})">+</button>
            </div>
        `;
    container.appendChild(card);
});

// Update tabs UI
document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
document.querySelector(`.tab[onclick="filter('${filter}')"]`).classList.add('active');
}

function filter(cat) {
    renderProducts(cat);
}

function addToCart(id) {
    const product = products.find(p => p.id === id);
    cart.push(product);
    updateCartUI();

    if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
}

function updateCartUI() {
    const total = cart.reduce((sum, item) => sum + item.price, 0);

    if (cart.length > 0) {
        tg.MainButton.setText(`Оформить заказ: ${total} TJS`);
        if (!tg.MainButton.isVisible) {
            tg.MainButton.show();
        }
        // Bind MainButton action to opening checkout
        tg.MainButton.onClick(openCheckout); // Note: This adds listener. We need to be careful not to add multiple.
        tg.MainButton.offClick(submitOrder); // Ensure it's not bound to submit yet
        tg.MainButton.offClick(openCheckout); // Remove prev to avoid dupes
        tg.MainButton.onClick(openCheckout);
    } else {
        tg.MainButton.hide();
        document.getElementById('checkout-modal').classList.remove('active'); // Auto close if empty
    }
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartUI();
    // Re-render list if modal is open
    openCheckout();
    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

// Modal
function openCheckout() {
    if (cart.length === 0) return;

    const modal = document.getElementById('checkout-modal');
    const list = document.getElementById('cart-items');

    list.innerHTML = '';
    let total = 0;

    cart.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                <div class="cart-del-btn" onclick="removeFromCart(${index})">⛔️</div>
                <div>
                    <div class="cart-item-title">${item.title}</div>
                    <div class="cart-item-price">${item.price} TJS</div>
                </div>
            </div>
        `;
        list.appendChild(div);
        total += item.price;
    });

    document.getElementById('cart-total').innerText = `${total} TJS`;
    modal.classList.add('active');

    // Switch MainButton to "Pay"
    tg.MainButton.setText(`Оплатить ${total} TJS`);
    tg.MainButton.offClick(openCheckout);
    tg.MainButton.onClick(submitOrder);
}

function closeCheckout() {
    document.getElementById('checkout-modal').classList.remove('active');

    // Revert MainButton to "View Cart" mode
    const total = cart.reduce((sum, item) => sum + item.price, 0);
    tg.MainButton.setText(`Оформить заказ: ${total} TJS`);
    tg.MainButton.offClick(submitOrder);
    tg.MainButton.onClick(openCheckout);
}

// Submit Order
async function submitOrder() {
    const contact = document.getElementById('order-contact').value;
    const comment = document.getElementById('order-comment').value;

    if (!contact || contact.length < 5) {
        tg.showPopup({
            title: "Ошибка",
            message: "Пожалуйста, укажите корректный контакт для связи.",
            buttons: [{ type: "ok" }]
        });
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
        return;
    }

    tg.MainButton.showProgress();

    const total = cart.reduce((sum, item) => sum + item.price, 0);
    const user = tg.initDataUnsafe.user || { id: 0, first_name: "Guest" };

    const orderData = {
        user_id: user.id,
        name: user.first_name + (user.last_name ? " " + user.last_name : ""),
        contact_info: contact,
        items: cart,
        total: total,
        comment: comment
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
