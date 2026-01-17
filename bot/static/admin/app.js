// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand(); // Make it fullscreen

// Apply theme params
if (tg.themeParams) {
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
    // Add more mappings if needed
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
            container.innerHTML = '<div style="text-align:center; color:var(--tg-theme-hint-color)">No bookings yet</div>';
            return;
        }

        data.forEach(booking => {
            const div = document.createElement('div');
            div.className = 'booking-item';
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

// Init
fetchStats();
fetchBookings();

// Set user data if available
if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    const user = tg.initDataUnsafe.user;
    document.querySelector('.subtitle').innerText = `Welcome back, ${user.first_name} 👋`;
    if (user.photo_url) {
        document.getElementById('admin-avatar').src = user.photo_url;
    }
}
