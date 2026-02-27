const BASE_URL = '/api/auth';

document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.textContent = 'Registering...';
    btn.disabled = true;

    const data = {
        name: document.getElementById('regName').value,
        email: document.getElementById('regEmail').value,
        phone: document.getElementById('regPhone').value,
        mpin: document.getElementById('regMpin').value
    };

    try {
        const res = await fetch(`${BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        const msgDiv = document.getElementById('registerMsg');

        if (res.ok) {
            msgDiv.innerHTML = `<span style="color:var(--success)">${result.msg}. You can now login.</span>`;
            e.target.reset();
        } else {
            msgDiv.innerHTML = `<span style="color:var(--danger)">${result.msg}</span>`;
        }
    } catch (err) {
        console.error(err);
    } finally {
        btn.textContent = 'Register';
        btn.disabled = false;
    }
});


document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.textContent = 'Logging in...';
    btn.disabled = true;

    const data = {
        phone: document.getElementById('loginPhone').value,
        mpin: document.getElementById('loginMpin').value
    };

    try {
        const res = await fetch(`${BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        const msgDiv = document.getElementById('loginMsg');

        if (res.ok) {
            msgDiv.innerHTML = `<span style="color:var(--success)">${result.msg}</span>`;
            // Save Token
            localStorage.setItem('token', result.access_token);
            localStorage.setItem('user', JSON.stringify(result.user));
            // Redirect
            window.location.href = '/dashboard';
        } else {
            msgDiv.innerHTML = `<span style="color:var(--danger)">${result.msg}</span>`;
        }
    } catch (err) {
        console.error(err);
    } finally {
        btn.textContent = 'Login';
        btn.disabled = false;
    }
});
