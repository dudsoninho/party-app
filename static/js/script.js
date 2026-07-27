document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const formData = new FormData();
            formData.append('username', username);

            const res = await fetch('/login', { method: 'POST', body: formData });
            if (res.ok) {
                window.location.reload();
            }
        });
    }

    const transferForm = document.getElementById('transfer-form');
    if (transferForm) {
        transferForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const receiver_id = document.getElementById('receiver').value;
            const amount = document.getElementById('amount').value;

            const res = await fetch('/transfer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ receiver_id, amount })
            });

            const data = await res.json();
            if (data.success) {
                if (typeof triggerButterflyEffect === 'function') {
                    triggerButterflyEffect();
                }
                alert(data.message);
                setTimeout(() => window.location.reload(), 1500);
            } else {
                alert(data.message);
            }
        });
    }
});

async function adjustCoins(userId, amount) {
    const res = await fetch('/admin/adjust_balance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, amount: amount })
    });
    const data = await res.json();
    if (data.success) window.location.reload();
}

async function kickUser(userId, username) {
    if (confirm(`Na pewno chcesz usunąć gracza ${username}?`)) {
        const res = await fetch('/admin/kick_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await res.json();
        if (data.success) window.location.reload();
    }
}
