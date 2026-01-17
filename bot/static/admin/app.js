// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Globals
let currentOrder = null;
let chartInstance = null;
const ADMIN_ID = 409951664; // Fallback if not strictly enforcing backend

// Apply theme
if (tg.themeParams) {
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
}

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

    if (chartInstance) chartInstance.destroy(); // Prevent duplicates

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Заказы',
                data: chartData.data,
                borderColor: '#007AFF',
                backgroundColor: 'rgba(0, 122, 255, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointBackgroundColor: '#ffffff',
                pointBorderColor: '#007AFF',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { precision: 0 } },
                x: { grid: { display: false } }
            }
        }
    });
}

async function fetchBookings() {
    try {
        const response = await fetch('/api/bookings', { headers: getHeaders() });
        const data = await response.json();
        const container = document.getElementById('bookings-container');

        container.innerHTML = '';

        if (data.length === 0) {
            container.innerHTML = '<div style="text-align:center; color:var(--tg-theme-hint-color)">Заявок пока нет</div>';
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
                <div class="status ${booking.status}">${booking.status.toUpperCase()}</div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error(e);
    }
}

// --- Modal Logic ---

async function showDetails(id) {
    const modal = document.getElementById('detail-modal');
    modal.classList.add('active');

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
    const formHtml = `
        <div class="edit-form">
            <label class="detail-label">Контакты</label>
            <input type="text" id="edit-contact" value="${order.contact_info || ''}" style="width:100%; padding:8px; margin-bottom:12px; border-radius:8px; border:1px solid #ddd;">
            
            <label class="detail-label">Бюджет</label>
            <input type="text" id="edit-budget" value="${order.budget || ''}" style="width:100%; padding:8px; margin-bottom:12px; border-radius:8px; border:1px solid #ddd;">
            
            <label class="detail-label">Описание</label>
            <textarea id="edit-desc" rows="3" style="width:100%; padding:8px; margin-bottom:12px; border-radius:8px; border:1px solid #ddd;">${order.task_description || ''}</textarea>
        
            <button class="btn btn-primary" style="width:100%" onclick="saveOrderDetails()">Сохранить</button>
            <button class="btn btn-sm" style="width:100%; margin-top:8px;" onclick="renderReadMode(currentOrder)">Отмена</button>
        </div>
    `;
    document.getElementById('read-view').style.display = 'none';
    const editView = document.getElementById('edit-view');
    editView.innerHTML = formHtml;
    editView.style.display = 'block';

    // Hide main actions while editing
    document.getElementById('modal-actions').style.display = 'none';
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
            alert("Ошибка сохранения");
        }
    } catch (e) {
        alert("Ошибка сети");
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
    } else {
        buttons = `<div class="detail-label" style="text-align:center; grid-column: span 2;">Статус: ${order.status.toUpperCase()}</div>`;
    }
    document.getElementById('modal-actions').innerHTML = buttons;
    document.getElementById('modal-actions').style.display = 'grid';
}

function closeModal() {
    document.getElementById('detail-modal').classList.remove('active');
}

async function updateStatus(id, status) {
    if (!confirm(`Изменить статус на "${status}"?`)) return;

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

function fetchUser() {
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        document.querySelector('.subtitle').innerText = `С возвращением, ${user.first_name} 👋`;
        if (user.photo_url) document.getElementById('admin-avatar').src = user.photo_url;
    }
}
