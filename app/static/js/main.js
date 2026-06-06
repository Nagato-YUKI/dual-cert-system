/**
 * Certificate Management System - Common JavaScript
 */

const API_BASE_URL = '';

const TOKEN_KEY = 'access_token';
const USER_KEY = 'user_info';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function setUserInfo(userInfo) {
  localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
}

function getUserInfo() {
  const data = localStorage.getItem(USER_KEY);
  try {
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

/**
 * Generic API request wrapper with Authorization header
 */
async function apiRequest(url, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = 'Bearer ' + token;
  }

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(API_BASE_URL + url, config);

  if (response.status === 401) {
    removeToken();
    window.location.href = '/login';
    return Promise.reject(new Error('Unauthorized'));
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.msg || 'Request failed: ' + response.status);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * Check authentication status on page load
 */
async function checkAuth() {
  const token = getToken();
  if (!token) {
    redirectToLogin();
    return false;
  }

  try {
    const user = await apiRequest('/auth/me');
    setUserInfo(user);
    updateNavbar(user);
    return true;
  } catch (error) {
    removeToken();
    redirectToLogin();
    return false;
  }
}

/**
 * Redirect to login page
 */
function redirectToLogin() {
  const currentPath = window.location.pathname;
  if (currentPath !== '/login') {
    window.location.href = '/login';
  }
}

/**
 * Logout user
 */
function logout() {
  removeToken();
  window.location.href = '/login';
}

/**
 * Update navbar based on user role
 */
function updateNavbar(user) {
  const adminNavs = document.querySelectorAll('.admin-nav');
  const studentNavs = document.querySelectorAll('.student-nav');
  const userNameEl = document.getElementById('user-name');
  const logoutBtn = document.getElementById('logout-btn');

  if (userNameEl) {
    userNameEl.textContent = user.name || user.username || user.student_no || 'User';
  }

  if (logoutBtn) {
    logoutBtn.style.display = 'inline-block';
  }

  if (user.role === 'admin') {
    adminNavs.forEach(el => el.style.display = 'block');
    studentNavs.forEach(el => el.style.display = 'none');
  } else if (user.role === 'student') {
    adminNavs.forEach(el => el.style.display = 'none');
    studentNavs.forEach(el => el.style.display = 'block');
  }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'danger') {
  const container = document.getElementById('alert-container');
  if (!container) return;

  const alertEl = document.createElement('div');
  alertEl.className = `alert alert-${type} alert-dismissible fade show`;
  alertEl.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  container.appendChild(alertEl);

  setTimeout(() => {
    alertEl.classList.remove('show');
    setTimeout(() => alertEl.remove(), 150);
  }, 5000);
}

/**
 * Format date string
 */
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN');
}

/**
 * Format datetime string
 */
function formatDateTime(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
  const map = {
    approved: 'success',
    rejected: 'danger',
    pending: 'warning',
    ai_reviewed: 'info',
    need_more_info: 'secondary',
    upcoming: 'primary',
    ongoing: 'info',
    completed: 'success',
    cancelled: 'secondary',
    active: 'success',
    inactive: 'secondary',
  };
  const cls = map[status] || 'secondary';
  const label = status ? status.replace(/_/g, ' ').toUpperCase() : 'UNKNOWN';
  return `<span class="badge bg-${cls}">${label}</span>`;
}

// Attach logout handler on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      logout();
    });
  }
});
