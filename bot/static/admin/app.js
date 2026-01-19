// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;

// 1. Expand to full height (Reduces swipe-to-close area)
tg.expand();

// 2. Disable vertical swipe-to-close (Modern Telegram Clients)
// This locks the app so swiping down DOES NOT close it.
if (tg.isVerticalSwipesEnabled !== undefined) {
    tg.isVerticalSwipesEnabled = false;
}
tg.expand();

// Globals
let currentOrder = null;
let chartInstance = null;
const ADMIN_ID = 409951664; // Fallback if not strictly enforcing backend

// Apply theme
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    } else if (tg.colorScheme === 'dark') {
        // Auto-detect Telegram theme logic (optional, we use manual toggle mostly)
        // document.body.classList.add('dark-mode'); 
    }

    // Fallback for native colors if Telegram web app is not giving them
    if (tg.themeParams && tg.themeParams.bg_color) {
        // We override these if we want manual control, or we respect them.
        // For our Custom Dark Mode, we ignore tg.themeParams bg_color for body background
        // but we might use them elsewhere.
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
}

initTheme();

// Auth Header helper
function getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        headers['X-Telegram-User'] = tg.initDataUnsafe.user.id;
    }
    return headers;
}

// API Functions
async function fetchStats() {
    try {
        const response = await fetch('/api/stats', { headers: getHeaders() });
        const data = await response.json();

        document.getElementById('total-users').innerText = data.users;
        document.getElementById('revenue').innerText = `${data.revenue_today} TJS`;
        document.getElementById('active-orders').innerText = data.active_orders;

        // Render Chart
        if (data.chart) renderChart(data.chart);

    } catch (e) {
        console.error("Failed to fetch stats", e);
    }
}

function renderChart(chartData) {
    const ctx = document.getElementById('ordersChart').getContext('2d');

    // Create Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 122, 255, 0.4)');
    gradient.addColorStop(1, 'rgba(0, 122, 255, 0)');

    if (chartInstance) chartInstance.destroy(); // Prevent duplicates

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Заказы',
                data: chartData.data,
                borderColor: '#007AFF', // Telegram Blue
                backgroundColor: gradient,
                borderWidth: 3,
                tension: 0.4, // Smooth curves
                fill: true,
                pointRadius: 0, // Clean look, show on hover
                pointHoverRadius: 6,
                pointHitRadius: 20
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 14, weight: 'bold' },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { display: false }, // Cleaner
                    ticks: { display: false } // Minimal
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: '#8e8e93',
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 5
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        }
    });
}

const STATUS_MAP = {
    'new': 'Новый',
    'negotiation_pending': 'Переговоры',
    'in_progress': 'В работе',
    'completed': 'Завершен',
    'cancelled': 'Отменен'
};

function translateStatus(status) {
    return STATUS_MAP[status] || status;
}

async function fetchBookings(query = null) {
    try {
        let url = '/api/bookings';
        if (query) url += `?q=${encodeURIComponent(query)}`;

        const response = await fetch(url, { headers: getHeaders() });
        const data = await response.json();
        const container = document.getElementById('bookings-container');

        container.innerHTML = '';

        if (data.length === 0) {
            container.innerHTML = '<div style="text-align:center; color:var(--tg-theme-hint-color); padding: 20px;">Ничего не найдено</div>';
            return;
        }

        data.forEach(booking => {
            const div = document.createElement('div');
            div.className = 'booking-item';
            div.onclick = () => showDetails(booking.id);
            div.style.cursor = 'pointer';

            div.innerHTML = `
                <div class="booking-info">
                    <h4>${booking.client}</h4>
                    <p>${booking.service} • ${booking.time ? new Date(booking.time).toLocaleDateString() : 'N/A'}</p>
                </div>
                <!-- Use translateStatus here -->
                <div class="status ${booking.status}">${translateStatus(booking.status)}</div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error(e);
    }
}

// Global Filter State
let currentFilter = 'all';

function setFilter(status, element) {
    // UI Update
    document.querySelectorAll('.filter-pill').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    // Logic
    currentFilter = status;
    fetchBookings(); // Re-fetch/Re-render with filter
}

// Modify renderBookings to filter
async function fetchBookings() {
    try {
        const response = await fetch('/api/bookings');
        const bookings = await response.json();

        const container = document.getElementById('bookings-container');
        container.innerHTML = '';

        // Apply Filters
        const filtered = bookings.filter(b => {
            if (currentFilter === 'all') return true;
            return b.status === currentFilter;
        });

        if (filtered.length === 0) {
            container.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding:20px;">Нет заявок с таким статусом</div>';
            return;
        }

        filtered.forEach(booking => {
            const div = document.createElement('div');
            div.className = 'booking-item';
            div.onclick = () => showDetails(booking.id);

            // Format nice date
            const date = new Date(booking.created_at || new Date());
            const dateStr = date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });

            div.innerHTML = `
                <div class="booking-info">
                    <h4>${booking.client || 'Клиент'}</h4>
                    <p>${booking.service || 'Заказ'} • ${dateStr}</p>
                </div>
                <div class="status ${booking.status}">${translateStatus(booking.status)}</div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error(e);
    }
}

// --- Search & View All Logic ---

let isViewAll = false;

function toggleViewAll() {
    isViewAll = !isViewAll;
    const statsGrid = document.querySelector('.stats-grid');
    const chartCard = document.querySelector('.chart-card');
    const searchContainer = document.getElementById('search-container');
    const btn = document.querySelector("button[onclick='toggleViewAll()']");

    if (isViewAll) {
        // "All Orders" Mode
        statsGrid.style.display = 'none';
        chartCard.style.display = 'none';
        searchContainer.style.display = 'block';
        btn.innerText = 'Назад';
        document.querySelector('.section-header h3').innerText = 'Все заказы';
        fetchBookings(null); // Fetch explicit list (maybe larger limit or same)
    } else {
        // "Dashboard" Mode
        statsGrid.style.display = 'grid';
        chartCard.style.display = 'block';
        searchContainer.style.display = 'none';
        btn.innerText = 'Все';
        document.getElementById('search-input').value = ''; // Clear search
        document.querySelector('.section-header h3').innerText = 'Новые заявки';
        fetchBookings(); // Reset
    }
}

// Search Listener
document.getElementById('search-input').addEventListener('keyup', (e) => {
    // Simple debounce could be added here
    const val = e.target.value;
    if (val.length > 2 || val.length === 0) {
        fetchBookings(val);
    }
});

// --- Broadcast Logic ---

function showBroadcastModal() {
    document.getElementById('broadcast-modal').classList.add('active');
}

function closeBroadcastModal() {
    document.getElementById('broadcast-modal').classList.remove('active');
}

async function sendBroadcast() {
    const text = document.getElementById('broadcast-text').value;
    if (!text) { alert("Введите текст!"); return; }

    if (!confirm(`Отправить сообщение всем пользователям?`)) return;

    const btn = document.querySelector("#broadcast-modal .btn-primary");
    btn.innerText = "Отправка...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/broadcast', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ message: text })
        });
        const res = await response.json();

        if (response.ok) {
            alert(`✅ Успешно отправлено: ${res.count} пользователям.`);
            closeBroadcastModal();
            document.getElementById('broadcast-text').value = '';
        } else {
            alert("Ошибка рассылки");
        }
    } catch (e) {
        alert("Ошибка сети");
    } finally {
        btn.innerText = "Отправить всем";
        btn.disabled = false;
    }
}

// --- Modal Logic ---

async function showDetails(id) {
    const modal = document.getElementById('detail-modal');
    modal.classList.add('active');
    document.body.classList.add('no-scroll'); // Lock scroll

    // Reset Edit Mode
    document.getElementById('modal-content').classList.remove('editing');

    document.getElementById('modal-content').innerHTML = 'Загрузка...';
    document.getElementById('modal-actions').innerHTML = '';

    try {
        const response = await fetch(`/api/orders/${id}`, { headers: getHeaders() });
        currentOrder = await response.json();
        const order = currentOrder;

        document.getElementById('modal-title').innerText = `Заказ #${id}`;

        // Render Details (Read Mode)
        renderReadMode(order);

        // Render Actions
        renderActions(order);

    } catch (e) {
        document.getElementById('modal-content').innerText = 'Ошибка загрузки';
    }
}

function renderReadMode(order) {
    const html = `
        <div id="read-view">
            <div class="detail-row">
                <span class="detail-label">Клиент</span>
                <div class="detail-value">${order.name}</div>
            </div>
            <div class="detail-row">
                <span class="detail-label">Контакты</span>
                <div class="detail-value"><a href="tel:${order.contact_info}">${order.contact_info}</a></div>
            </div>
             <div class="detail-row">
                <span class="detail-label">Бюджет</span>
                <div class="detail-value">${order.budget || 'Не указан'}</div>
            </div>
            <div class="detail-row">
                <span class="detail-label">Описание</span>
                <div class="detail-value" style="font-size:13px; opacity:0.8">${order.task_description}</div>
            </div>
            <button class="btn-sm" style="margin-top:12px; width:100%; text-align:right" onclick="enableEditMode()">✏️ Редактировать</button>
        </div>
        <div id="edit-view" style="display:none">
            <!-- Injected when edit clicked -->
        </div>
    `;
    document.getElementById('modal-content').innerHTML = html;
}

function enableEditMode() {
    const order = currentOrder;
    // Strip non-numeric chars for editing if needed, or just keep as is but remove TJS suffix
    const numericBudget = (order.budget || '').replace(' TJS', '').trim();

    const formHtml = `
        <div class="edit-form">
            <h4 style="margin-bottom:15px; color:#007AFF;">📝 Редактирование заказа</h4>
            
            <label class="detail-label">Контакты (только чтение)</label>
            <input type="text" id="edit-contact" value="${order.contact_info || ''}" class="form-input" disabled style="background:#f0f0f5; color:#666;">
            
            <label class="detail-label">Описание (только чтение)</label>
            <textarea id="edit-desc" rows="3" class="form-input" disabled style="background:#f0f0f5; color:#666;">${order.task_description || ''}</textarea>
            
            <label class="detail-label">Бюджет (TJS)</label>
            <div style="display:flex; align-items:center; gap:8px;">
                <input type="number" id="edit-budget" value="${numericBudget}" class="form-input" style="margin-bottom:12px; font-weight:bold; font-size:16px;">
                <span style="font-weight:600; margin-bottom:12px;">TJS</span>
            </div>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #e1e1e1;">
            
            <h4 style="margin-bottom:10px; color:#FF9500;">🤝 Переговоры с клиентом</h4>
            <div style="background:#FFF8E8; padding:12px; border-radius:10px; margin-bottom:15px;">
                <p style="font-size:13px; color:#D98200; line-height:1.4;">
                    Измените <b>Бюджет</b> выше и напишите комментарий ниже. Клиент получит кнопку "Принять" или "Отказать".
                </p>
            </div>
            
            <label class="detail-label">Комментарий для клиента</label>
            <textarea id="edit-admin-comment" rows="3" class="form-input" 
                placeholder="Здравствуйте! Мы изучили задачу. Готовы выполнить за..." 
                style="border-color:#FF9500;">${order.admin_comment || ''}</textarea>
        
            <button class="btn btn-warning" style="width:100%; padding:14px; margin-top:10px; font-weight:600;" onclick="sendNegotiation()">
                📤 Отправить предложение клиенту
            </button>
            
            <div style="margin-top:15px; display:flex; gap:10px;">
                <button class="btn btn-secondary" style="flex:1;" onclick="saveOrderDetails()">💾 Сохранить</button>
                <button class="btn btn-sm" style="flex:1; background:white; border:1px solid #ddd;" onclick="renderReadMode(currentOrder)">Отмена</button>
            </div>
        </div>
    `;
    document.getElementById('read-view').style.display = 'none';
    const editView = document.getElementById('edit-view');
    editView.innerHTML = formHtml;
    editView.style.display = 'block';

    // Hide main actions while editing
    document.getElementById('modal-actions').style.display = 'none';
}

async function sendNegotiation() {
    const budgetVal = document.getElementById('edit-budget').value;
    const data = {
        contact_info: document.getElementById('edit-contact').value,
        budget: budgetVal + ' TJS',
        task_description: document.getElementById('edit-desc').value,
        admin_comment: document.getElementById('edit-admin-comment').value
    };

    if (!confirm(`Отправить предложение с ценой ${budgetVal} TJS?`)) return;

    try {
        const response = await fetch(`/api/orders/${currentOrder.id}/negotiate`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert("✅ Предложение отправлено!");
            currentOrder = { ...currentOrder, ...data, status: 'negotiation_pending' };
            renderReadMode(currentOrder);
            document.getElementById('modal-actions').style.display = 'grid';
        } else {
            // Read raw text first to avoid "Body is disturbed"
            const rawText = await response.text();
            let errorMsg = "Неизвестная ошибка";
            try {
                const err = JSON.parse(rawText);
                errorMsg = err.error || JSON.stringify(err);
            } catch (e) {
                // If not JSON, use the raw text (truncated if too long)
                errorMsg = rawText.substring(0, 200);
            }
            alert(`Ошибка сервера (${response.status}): ${errorMsg}`);
        }
    } catch (e) {
        console.error(e);
        alert("Ошибка сети или скрипта: " + e.message);
    }
}

async function saveOrderDetails() {
    const updatedData = {
        contact_info: document.getElementById('edit-contact').value,
        budget: document.getElementById('edit-budget').value,
        task_description: document.getElementById('edit-desc').value
    };

    try {
        const response = await fetch(`/api/orders/${currentOrder.id}/update`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(updatedData)
        });

        if (response.ok) {
            // Update local state
            currentOrder = { ...currentOrder, ...updatedData };
            renderReadMode(currentOrder);
            document.getElementById('modal-actions').style.display = 'grid'; // Show actions again
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            // Read raw text first
            const rawText = await response.text();
            let errorMsg = "Неизвестная ошибка";
            try {
                const err = JSON.parse(rawText);
                errorMsg = err.error || JSON.stringify(err);
            } catch (e) {
                errorMsg = rawText.substring(0, 200);
            }
            alert(`Ошибка сохранения (${response.status}): ${errorMsg}`);
        }
    } catch (e) {
        console.error(e);
        alert("Ошибка сети или скрипта: " + e.message);
    }
}

function renderActions(order) {
    let buttons = '';
    if (order.status === 'new') {
        buttons = `
            <button class="btn btn-primary" onclick="updateStatus(${order.id}, 'in_progress')">В работу</button>
            <button class="btn btn-danger" onclick="updateStatus(${order.id}, 'cancelled')">Отказать</button>
        `;
    } else if (order.status === 'in_progress') {
        buttons = `
            <button class="btn btn-secondary" onclick="updateStatus(${order.id}, 'completed')">✅ Готово</button>
            <button class="btn btn-danger" onclick="updateStatus(${order.id}, 'cancelled')">Отмена</button>
        `;
    } else if (order.status === 'negotiation_pending') {
        buttons = `<div class="detail-label" style="text-align:center; grid-column: span 2; color:#FF9500;">⏳ Ждем ответа клиента...</div>`;
    } else {
        buttons = `<div class="detail-label" style="text-align:center; grid-column: span 2;">Статус: ${translateStatus(order.status)}</div>`;
    }
    document.getElementById('modal-actions').innerHTML = buttons;
    document.getElementById('modal-actions').style.display = 'grid';
}

function closeModal() {
    document.getElementById('detail-modal').classList.remove('active');
    document.body.classList.remove('no-scroll'); // Unlock scroll
}

async function updateStatus(id, status) {
    const statusRu = translateStatus(status);
    if (!confirm(`Изменить статус на "${statusRu}"?`)) return;

    try {
        const response = await fetch(`/api/orders/${id}/status`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ status: status })
        });

        if (response.ok) {
            closeModal();
            fetchBookings();
            fetchStats();
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            alert('Ошибка обновления');
        }
    } catch (e) {
        alert('Ошибка сети');
    }
}

// Init
fetchStats();
fetchBookings();
fetchUser();

// --- Tab Logic ---
function switchTab(tab) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('#dashboard-view, #products-view').forEach(el => el.style.display = 'none');

    if (tab === 'dashboard') {
        document.getElementById('dashboard-view').style.display = 'block';
        document.querySelector('.nav-item[onclick="switchTab(\'dashboard\')"]').classList.add('active');
        document.getElementById('page-title').innerText = 'Панель управления';
    } else {
        document.getElementById('products-view').style.display = 'block';
        document.querySelector('.nav-item[onclick="switchTab(\'products\')"]').classList.add('active');
        document.getElementById('page-title').innerText = 'Управление товарами';
        fetchAdminProducts();
    }

    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

// --- Product Management ---

async function fetchAdminProducts() {
    const list = document.getElementById('products-list');
    list.innerHTML = '<div class="loading-spinner">Загрузка...</div>';

    try {
        const response = await fetch('/api/products', { headers: getHeaders() });
        const products = await response.json();

        list.innerHTML = '';
        products.forEach(p => {
            const div = document.createElement('div');
            div.className = 'product-item';
            div.onclick = () => openProductModal(p);
            div.innerHTML = `
                <div class="prod-icon-box">${p.icon}</div>
                <div class="prod-info">
                    <h4 class="prod-title">${p.title}</h4>
                    <span class="prod-price">${p.price} TJS</span>
                </div>
                <div style="color: #ccc;">›</div>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        list.innerHTML = 'Ошибка загрузки';
    }
}

let currentProduct = null;

function openProductModal(product = null) {
    const modal = document.getElementById('product-modal');
    modal.classList.add('active');
    currentProduct = product;

    if (product) {
        // Edit Mode
        document.getElementById('product-modal-title').innerText = 'Редактировать';
        document.getElementById('prod-id').value = product.id;
        document.getElementById('prod-title').value = product.title;
        document.getElementById('prod-price').value = product.price;
        // document.getElementById('prod-icon').value = product.icon; // Set via selectIcon below
        document.getElementById('prod-category').value = product.category;
        document.getElementById('prod-desc').value = product.desc;
        selectIcon(product.icon);
        document.getElementById('btn-delete-prod').style.display = 'inline-block';
    } else {
        // New Mode
        document.getElementById('product-modal-title').innerText = 'Новый товар';
        document.getElementById('prod-id').value = '';
        document.getElementById('prod-title').value = '';
        document.getElementById('prod-price').value = '';
        document.getElementById('prod-icon').value = '📦';
        document.getElementById('prod-category').value = 'bots';
        document.getElementById('prod-desc').value = '';
        document.getElementById('prod-desc').value = '';
        document.getElementById('btn-delete-prod').style.display = 'none';
        selectIcon('📦'); // Reset default
    }
}

function selectIcon(icon) {
    document.getElementById('prod-icon').value = icon;
    document.getElementById('selected-icon-display').innerText = icon;
    closeEmojiPicker();

    // Highlight active
    document.querySelectorAll('.emoji-option').forEach(el => {
        el.style.transform = el.innerText === icon ? 'scale(1.1)' : 'scale(1)';
        el.style.border = el.innerText === icon ? '2px solid #007AFF' : 'none';
    });
}

function openEmojiPicker() {
    document.getElementById('emoji-modal').classList.add('active');
}

function closeEmojiPicker() {
    document.getElementById('emoji-modal').classList.remove('active');
}

function closeProductModal() {
    document.getElementById('product-modal').classList.remove('active');
}

async function saveProduct() {
    const id = document.getElementById('prod-id').value;
    const data = {
        title: document.getElementById('prod-title').value,
        price: Number(document.getElementById('prod-price').value),
        icon: document.getElementById('prod-icon').value,
        category: document.getElementById('prod-category').value,
        desc: document.getElementById('prod-desc').value
    };

    if (!data.title || !data.price) {
        alert("Заполните название и цену");
        return;
    }

    const url = id ? `/api/products/${id}` : '/api/products';
    const method = id ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: getHeaders(),
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeProductModal();
            fetchAdminProducts();
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            alert("Ошибка сохранения");
        }
    } catch (e) {
        alert("Ошибка сети");
    }
}

async function deleteProduct() {
    if (!currentProduct || !confirm("Удалить этот товар?")) return;

    try {
        const response = await fetch(`/api/products/${currentProduct.id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });

        if (response.ok) {
            closeProductModal();
            fetchAdminProducts();
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            alert("Ошибка удаления");
        }
    } catch (e) {
        alert("Ошибка сети");
    }
}

function fetchUser() {
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        document.querySelector('.subtitle').innerText = `С возвращением, ${user.first_name} 👋`;
        if (user.photo_url) document.getElementById('admin-avatar').src = user.photo_url;
    }
}
