// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand(); // Make it fullscreen

// Apply theme params
if (tg.themeParams) {
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
}

// API Functions
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('total-users').innerText = data.users;
        document.getElementById('revenue').innerText = `${data.revenue_today} TJS`;
        document.getElementById('active-orders').innerText = data.active_orders;
    } catch (e) {
        console.error("Failed to fetch stats", e);
    }
}

async function fetchBookings() {
    try {
        const response = await fetch('/api/bookings');
        const data = await response.json();
        const container = document.getElementById('bookings-container');

        container.innerHTML = ''; // Clear loading

        if (data.length === 0) {
            container.innerHTML = '<div style="text-align:center; color:var(--tg-theme-hint-color)">Заявок пока нет</div>';
            return;
        }

        data.forEach(booking => {
            const div = document.createElement('div');
            div.className = 'booking-item';
            div.onclick = () => showDetails(booking.id); // Add interaction
            div.style.cursor = 'pointer'; // Visual cue

            div.innerHTML = `
                <div class="booking-info">
                    <h4>${booking.client}</h4>
                    <p>${booking.service} • ${new Date(booking.time).toLocaleDateString()}</p>
                </div>
                <div class="status ${booking.status}">${booking.status.toUpperCase()}</div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error("Failed to fetch bookings", e);
    }
}

// --- Modal Logic ---

async function showDetails(id) {
    const modal = document.getElementById('detail-modal');
    modal.classList.add('active');

    // Show Loading state
    document.getElementById('modal-content').innerHTML = 'Загрузка...';
    document.getElementById('modal-actions').innerHTML = '';
    document.getElementById('modal-title').innerText = `Заказ #${id}`;

    try {
        const response = await fetch(`/api/orders/${id}`);
        const order = await response.json();

        // Render Details
        const html = `
            <div class="detail-row">
                <span class="detail-label">Клиент</span>
                <div class="detail-value">${order.name}</div>
            </div>
            <div class="detail-row">
                <span class="detail-label">Услуга</span>
                <div class="detail-value">${order.service_context || order.task_description}</div>
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
                <span class="detail-label">Описание задачи</span>
                <div class="detail-value" style="font-size:13px; opacity:0.8">${order.task_description}</div>
            </div>
        `;
        document.getElementById('modal-content').innerHTML = html;

        // Render Actions based on Status
        let buttons = '';
        if (order.status === 'new') {
            buttons = `
                <button class="btn btn-primary" onclick="updateStatus(${id}, 'in_progress')">В работу</button>
                <button class="btn btn-danger" onclick="updateStatus(${id}, 'cancelled')">Отказать</button>
            `;
        } else if (order.status === 'in_progress') {
            buttons = `
                <button class="btn btn-secondary" onclick="updateStatus(${id}, 'completed')">✅ Выполнено</button>
                <button class="btn btn-danger" onclick="updateStatus(${id}, 'cancelled')">Отмена</button>
            `;
        } else {
            buttons = `<div class="detail-label" style="text-align:center; grid-column: span 2;">Статус заказа: ${order.status}</div>`;
        }

        document.getElementById('modal-actions').innerHTML = buttons;

    } catch (e) {
        document.getElementById('modal-content').innerText = 'Ошибка загрузки';
    }
}

function closeModal() {
    document.getElementById('detail-modal').classList.remove('active');
}

async function updateStatus(id, status) {
    if (!confirm(`Вы уверены, что хотите изменить статус на "${status}"?`)) return;

    try {
        const response = await fetch(`/api/orders/${id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status })
        });

        if (response.ok) {
            closeModal();
            fetchBookings(); // Refresh list
            fetchStats(); // Refresh stats

            // Telegram haptic feedback if available
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            alert('Не удалось изменить статус');
        }
    } catch (e) {
        console.error(e);
        alert('Ошибка обновления');
    }
}

// Init
fetchStats();
fetchBookings();
fetchUser();

function fetchUser() {
    // Set user data if available
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        document.querySelector('.subtitle').innerText = `С возвращением, ${user.first_name} 👋`;
        if (user.photo_url) {
            document.getElementById('admin-avatar').src = user.photo_url;
        }
    }
}
