const API_BASE = "/api";

const api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            if (options.body && typeof options.body !== 'string') {
                options.body = JSON.stringify(options.body);
            }
        }

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
            
            if (response.status === 401) {
                // Unauthorized, redirect to login
                localStorage.removeItem('token');
                localStorage.removeItem('userRole');
                window.location.href = 'login.html';
                return null;
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                let errorMessage = 'An error occurred';
                if (data.detail) {
                    if (Array.isArray(data.detail)) {
                        errorMessage = data.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join('\n');
                    } else {
                        errorMessage = data.detail;
                    }
                }
                throw new Error(errorMessage);
            }
            
            return data;
        } catch (error) {
            showToast(error.message, 'error');
            throw error;
        }
    },

    auth: {
        login: (username, password) => {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            return api.request('/auth/login', {
                method: 'POST',
                body: formData
            });
        },
        register: (userData) => api.request('/auth/register', { method: 'POST', body: userData }),
        me: () => api.request('/users/me')
    },
    
    courses: {
        getAll: () => api.request('/courses/'),
        create: (data) => api.request('/courses/', { method: 'POST', body: data })
    },
    
    courseworks: {
        getByCourse: (courseId) => api.request(`/courseworks/course/${courseId}`),
        create: (formData) => api.request('/courseworks/', { method: 'POST', body: formData })
    },
    
    submissions: {
        submit: (formData) => api.request('/submissions/', { method: 'POST', body: formData }),
        getMy: () => api.request('/submissions/my'),
        getForCoursework: (courseworkId) => api.request(`/submissions/coursework/${courseworkId}`),
        grade: (submissionId, data) => api.request(`/submissions/${submissionId}/grade`, { method: 'PUT', body: data })
    }
};

// UI Utilities
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check';
    const color = type === 'error' ? 'var(--danger)' : 'var(--success)';
    
    toast.innerHTML = `<i class="fa-solid ${icon}" style="color: ${color}"></i> <span>${message}</span>`;
    toast.style.borderLeftColor = color;
    
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Theme toggling
function initTheme() {
    const isDark = localStorage.getItem('theme') === 'dark';
    if (isDark) document.documentElement.setAttribute('data-theme', 'dark');
    
    const toggleBtn = document.querySelector('.theme-toggle');
    if (toggleBtn) {
        toggleBtn.innerHTML = isDark ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        toggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            if (current === 'dark') {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
                toggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                toggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            }
        });
    }
}

// Authentication Check
async function requireAuth(expectedRole = null) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return null;
    }
    
    try {
        const user = await api.auth.me();
        if (expectedRole && user.role !== expectedRole && user.role !== 'admin') {
            window.location.href = 'login.html'; // Or forbidden page
        }
        
        // Update user profile UI if exists
        const userNameEl = document.getElementById('user-name-display');
        const userRoleEl = document.getElementById('user-role-display');
        if (userNameEl) userNameEl.textContent = user.full_name;
        if (userRoleEl) userRoleEl.textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
        
        return user;
    } catch (e) {
        return null;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    window.location.href = 'login.html';
}

document.addEventListener('DOMContentLoaded', initTheme);
