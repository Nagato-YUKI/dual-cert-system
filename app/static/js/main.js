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

  console.log('[apiRequest]', url, 'token:', token ? 'present' : 'none');
  const response = await fetch(API_BASE_URL + url, config);
  console.log('[apiRequest]', url, 'status:', response.status);

  if (response.status === 401) {
    const errorData = await response.json().catch(() => ({}));
    const errorMsg = errorData.msg || 'Unauthorized';
    // Only redirect to login for non-auth API calls
    // Auth login endpoints should show error messages instead of redirecting
    if (!url.startsWith('/auth/login') && !url.startsWith('/auth/student/login')) {
      removeToken();
      window.location.href = '/login';
    }
    throw new Error(errorMsg);
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
    console.log('[checkAuth] No token found, redirecting to login');
    redirectToLogin();
    return false;
  }

  try {
    console.log('[checkAuth] Token found, calling /auth/me');
    const user = await apiRequest('/auth/me');
    console.log('[checkAuth] /auth/me success:', user);
    setUserInfo(user);
    updateNavbar(user);
    return true;
  } catch (error) {
    console.log('[checkAuth] /auth/me failed:', error.message);
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
  const avatarContainer = document.getElementById('avatar-container');
  const avatarEl = document.getElementById('user-avatar');

  if (userNameEl) {
    userNameEl.textContent = user.name || user.username || user.student_no || 'User';
  }

  if (logoutBtn) {
    logoutBtn.style.display = 'inline-block';
  }

  // Show avatar image if avatar_url is available
  if (avatarContainer && avatarEl && user.avatar_url) {
    avatarEl.innerHTML = '';
    const img = document.createElement('img');
    img.src = user.avatar_url;
    img.alt = 'avatar';
    img.style.cssText = 'width:100%;height:100%;object-fit:cover;border-radius:50%;';
    img.onerror = function() {
      // Fallback to initial letter on image load error
      avatarEl.innerHTML = (user.name || user.username || 'U').charAt(0).toUpperCase();
      img.remove();
    };
    avatarEl.innerHTML = '';
    avatarEl.appendChild(img);
  } else if (avatarEl) {
    const initial = (user.name || user.username || 'U').charAt(0).toUpperCase();
    avatarEl.textContent = initial;
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
    approved: { cls: 'success', label: '已通过' },
    rejected: { cls: 'danger', label: '已拒绝' },
    pending: { cls: 'warning', label: '待审核' },
    ai_reviewed: { cls: 'info', label: 'AI已审' },
    need_more_info: { cls: 'secondary', label: '需补充' },
    upcoming: { cls: 'primary', label: '即将开始' },
    ongoing: { cls: 'info', label: '进行中' },
    completed: { cls: 'success', label: '已结束' },
    cancelled: { cls: 'secondary', label: '已取消' },
    finished: { cls: 'secondary', label: '已结束' },
    active: { cls: 'success', label: '启用' },
    inactive: { cls: 'secondary', label: '停用' },
    obtained: { cls: 'success', label: '已获取' },
    failed: { cls: 'danger', label: '未通过' },
    passed: { cls: 'success', label: '已通过' },
    expired: { cls: 'secondary', label: '已过期' },
    reviewed: { cls: 'info', label: '已审核' },
    revoked: { cls: 'danger', label: '已撤销' },
  };
  const entry = map[status];
  if (entry) {
    return `<span class="badge bg-${entry.cls}">${entry.label}</span>`;
  }
  return `<span class="badge bg-secondary">${status || '未知'}</span>`;
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
