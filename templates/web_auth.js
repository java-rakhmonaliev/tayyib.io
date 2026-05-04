// Tayyib Web Auth - JWT handling (same as Flutter app)
const API_BASE = 'http://13.217.178.63';

function getAccessToken() {
    return localStorage.getItem('access_token');
}

function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

function saveTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
}

async function apiFetch(url, options = {}) {
    const token = getAccessToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Try to refresh token
        const refreshed = await tryRefreshToken();
        if (refreshed) {
            return apiFetch(url, options); // Retry
        } else {
            clearTokens();
            window.location.href = '/login/';
            return;
        }
    }

    return response;
}

async function tryRefreshToken() {
    const refresh = getRefreshToken();
    if (!refresh) return false;

    try {
        const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
        });

        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('access_token', data.access);
            return true;
        }
    } catch (e) {}
    return false;
}

async function login(username, password) {
    const res = await fetch(`${API_BASE}/api/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.error || 'Login failed');
    }

    const data = await res.json();
    saveTokens(data.access, data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.user;
}

async function register(userData) {
    const res = await fetch(`${API_BASE}/api/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.error || 'Registration failed');
    }

    const data = await res.json();
    saveTokens(data.access, data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.user;
}

async function getProfile() {
    const res = await apiFetch('/api/auth/profile/');
    if (!res.ok) throw new Error('Failed to fetch profile');
    return await res.json();
}

async function updateProfile(madhab, country) {
    const res = await apiFetch('/api/auth/profile/update/', {
        method: 'PATCH',
        body: JSON.stringify({ madhab, country })
    });
    return await res.json();
}

function getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function isLoggedIn() {
    return !!getAccessToken();
}

// Make functions available globally
window.TayyibAuth = {
    login,
    register,
    getProfile,
    updateProfile,
    getCurrentUser,
    isLoggedIn,
    clearTokens,
    apiFetch
};