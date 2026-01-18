const tg = window.Telegram.WebApp;
tg.expand();

// Products Data (Mock)
const products = [
    { id: 1, title: 'Telegram Магазин', price: 2500, icon: '🛍', category: 'bots', desc: 'Каталог, корзина, оплата внутри Telegram.' },
    { id: 2, title: 'CRM Система', price: 4000, icon: '📊', category: 'crm', desc: 'Управление заявками и аналитика для бизнеса.' },
    { id: 3, title: 'Чат-бот Визитка', price: 1000, icon: '📇', category: 'bots', desc: 'Ответы на вопросы, контакты, портфолио.' },
    { id: 4, title: 'Запись клиентов', price: 3000, icon: '📅', category: 'bots', desc: 'Бронирование слотов, календарь, напоминания.' },
    { id: 5, title: 'AI Ассистент', price: 5000, icon: '🤖', category: 'crm', desc: 'Умный бот на базе GPT для техподдержки.' },
    { id: 6, title: 'Консультация', price: 500, icon: '👨‍💻', category: 'other', desc: 'Разбор вашей бизнес-задачи за 1 час.' }
];

let cart = [];

// Init
document.addEventListener('DOMContentLoaded', () => {
    renderProducts('all');

    // User Info
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        if (user.photo_url) document.getElementById('user-avatar').src = user.photo_url;
        // Autofill name if available (not contact, sadly)
    }
});

function renderProducts(filter) {
    const container = document.getElementById('product-grid');
    container.innerHTML = '';

    products.forEach(p => {
        if (filter !== 'all' && p.category !== filter) return;

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
    updateCartIcon();

    if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
}

function updateCartIcon() {
    const count = cart.length;
    document.getElementById('cart-count').innerText = count;

    const btn = document.getElementById('cart-btn');
    if (count > 0) {
        btn.style.transform = 'scale(1)';
    } else {
        btn.style.transform = 'scale(0)';
    }
}

// Modal
function openCheckout() {
    if (cart.length === 0) return;

    const modal = document.getElementById('checkout-modal');
    const list = document.getElementById('cart-items');

    list.innerHTML = '';
    let total = 0;

    cart.forEach(item => {
        const div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = `
            <span class="cart-item-title">${item.title}</span>
            <span class="cart-item-price">${item.price} TJS</span>
        `;
        list.appendChild(div);
        total += item.price;
    });

    document.getElementById('cart-total').innerText = `${total} TJS`;
    modal.classList.add('active');
}

function closeCheckout() {
    document.getElementById('checkout-modal').classList.remove('active');
}

// Submit Order
async function submitOrder() {
    const btn = document.querySelector('.btn-primary');
    const contact = document.getElementById('order-contact').value;
    const comment = document.getElementById('order-comment').value;

    if (!contact) {
        alert("Пожалуйста, укажите ваш контакт");
        return;
    }

    btn.innerText = "Оформляем...";
    btn.disabled = true;

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
            alert("✅ Заказ успешно оформлен!");
            cart = [];
            updateCartIcon();
            closeCheckout();
            tg.close(); // Close the Mini App
        } else {
            alert("Ошибка оформления заказа.");
        }
    } catch (e) {
        alert("Ошибка сети.");
    } finally {
        btn.innerText = "Оформить заказ";
        btn.disabled = false;
    }
}
