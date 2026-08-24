// filepath: /home/sumeet725/Desktop/Hershey/Random projects/SMT/frontend/app.js
// Fix the API base URL and add missing functions

const API_BASE_URL = 'http://localhost:8000/api';

// Fix login function
async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
        showError('Email and password are required');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.detail || 'Login failed');
            return;
        }

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        currentUser = data.user;

        window.location.href = 'resident.html';
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

// Fix register function
async function register() {
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;

    if (!name || !email || !password || !confirmPassword) {
        showError('All fields are required');
        return;
    }

    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    if (password.length < 8) {
        showError('Password must be at least 8 characters');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, role: 'resident' })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.detail || 'Registration failed');
            return;
        }

        showSuccess('Registration successful! Logging in...');
        setTimeout(() => {
            document.getElementById('loginEmail').value = email;
            document.getElementById('loginPassword').value = password;
            login();
        }, 1000);
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

// Fix complaint creation with file upload
async function createComplaint() {
    const category = document.getElementById('complaintCategory').value;
    const description = document.getElementById('complaintDescription').value;
    const fileInput = document.getElementById('complaintPhoto');

    if (!category || !description) {
        showError('Category and description are required');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('category', category);
        formData.append('description', description);
        formData.append('resident_id', currentUser.id);

        // Add file if selected
        if (fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
        }

        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/complaints/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.detail || 'Failed to create complaint');
            return;
        }

        showSuccess('Complaint created successfully!');
        document.getElementById('complaintCategory').value = '';
        document.getElementById('complaintDescription').value = '';
        fileInput.value = '';

        // Refresh complaints list
        loadComplaints();
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

// Fix get all complaints
async function loadComplaints() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/complaints/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            showError('Failed to load complaints');
            return;
        }

        const complaints = await response.json();
        displayComplaints(complaints);
    } catch (error) {
        showError('Error loading complaints: ' + error.message);
    }
}

// Fix display complaints
function displayComplaints(complaints) {
    const container = document.getElementById('complaintsContainer');
    if (!container) return;

    if (!complaints || complaints.length === 0) {
        container.innerHTML = '<p>No complaints found</p>';
        return;
    }

    container.innerHTML = complaints.map(complaint => `
        <div class="complaint-card" onclick="viewComplaint(${complaint.id})">
            <div class="complaint-header">
                <h3>${complaint.category}</h3>
                <span class="status-badge ${complaint.status.toLowerCase()}">${complaint.status}</span>
            </div>
            <p>${complaint.description.substring(0, 100)}...</p>
            <div class="complaint-meta">
                <small>Created: ${new Date(complaint.created_at).toLocaleDateString()}</small>
                <small>Priority: ${complaint.priority || 'Not set'}</small>
            </div>
        </div>
    `).join('');
}

// Fix view complaint detail
async function viewComplaint(complaintId) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/complaints/${complaintId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            showError('Failed to load complaint');
            return;
        }

        const complaint = await response.json();
        displayComplaintDetail(complaint);
    } catch (error) {
        showError('Error loading complaint: ' + error.message);
    }
}

// Fix display complaint detail
function displayComplaintDetail(complaint) {
    const container = document.getElementById('complaintDetail');
    if (!container) return;

    const historyHtml = (complaint.history || []).map(h => `
        <div class="history-item">
            <strong>${h.actor}</strong> - ${h.action}
            <p>${h.note || ''}</p>
            <small>${new Date(h.timestamp).toLocaleString()}</small>
        </div>
    `).join('');

    container.innerHTML = `
        <h2>${complaint.category}</h2>
        <p>${complaint.description}</p>
        ${complaint.photo_url ? `<img src="${complaint.photo_url}" alt="Complaint photo" style="max-width: 100%; margin: 20px 0;">` : ''}
        <div class="complaint-info">
            <p><strong>Status:</strong> ${complaint.status}</p>
            <p><strong>Priority:</strong> ${complaint.priority || 'Not set'}</p>
            <p><strong>Created:</strong> ${new Date(complaint.created_at).toLocaleString()}</p>
        </div>
        <div class="history">
            <h3>History</h3>
            ${historyHtml}
        </div>
    `;
}

// Fix update complaint status (admin only)
async function updateComplaintStatus(complaintId, status, note) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/complaints/${complaintId}/status`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status, note })
        });

        if (!response.ok) {
            showError('Failed to update complaint');
            return;
        }

        showSuccess('Complaint updated successfully!');
        loadComplaints();
    } catch (error) {
        showError('Error updating complaint: ' + error.message);
    }
}

// Fix set priority (admin only)
async function setComplaintPriority(complaintId, priority) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/complaints/${complaintId}/priority`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ priority })
        });

        if (!response.ok) {
            showError('Failed to set priority');
            return;
        }

        showSuccess('Priority updated!');
        loadComplaints();
    } catch (error) {
        showError('Error setting priority: ' + error.message);
    }
}

// Fix get notices
async function loadNotices() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/notices/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            showError('Failed to load notices');
            return;
        }

        const notices = await response.json();
        displayNotices(notices);
    } catch (error) {
        showError('Error loading notices: ' + error.message);
    }
}

// Fix display notices
function displayNotices(notices) {
    const container = document.getElementById('noticesContainer');
    if (!container) return;

    if (!notices || notices.length === 0) {
        container.innerHTML = '<p>No notices available</p>';
        return;
    }

    container.innerHTML = notices.map(notice => `
        <div class="notice-card ${notice.is_pinned ? 'pinned' : ''}">
            <div class="notice-header">
                <h3>${notice.title}</h3>
                ${notice.is_pinned ? '<span class="pinned-badge">📌 Pinned</span>' : ''}
            </div>
            <p>${notice.content}</p>
            <small>Posted: ${new Date(notice.created_at).toLocaleDateString()}</small>
        </div>
    `).join('');
}

// Fix create notice (admin only)
async function createNotice() {
    const title = document.getElementById('noticeTitle').value;
    const content = document.getElementById('noticeContent').value;
    const isPinned = document.getElementById('noticePinned').checked;

    if (!title || !content) {
        showError('Title and content are required');
        return;
    }

    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/notices/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, content, is_pinned: isPinned })
        });

        if (!response.ok) {
            showError('Failed to create notice');
            return;
        }

        showSuccess('Notice created successfully!');
        document.getElementById('noticeTitle').value = '';
        document.getElementById('noticeContent').value = '';
        document.getElementById('noticePinned').checked = false;

        loadNotices();
    } catch (error) {
        showError('Error creating notice: ' + error.message);
    }
}

// Fix get dashboard
async function loadDashboard() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/dashboard/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            showError('Failed to load dashboard');
            return;
        }

        const stats = await response.json();
        displayDashboard(stats);
    } catch (error) {
        showError('Error loading dashboard: ' + error.message);
    }
}

// Fix display dashboard
function displayDashboard(stats) {
    const container = document.getElementById('dashboardStats');
    if (!container) return;

    container.innerHTML = `
        <div class="stat-card">
            <h3>Total Complaints</h3>
            <p class="stat-number">${stats.total_complaints || 0}</p>
        </div>
        <div class="stat-card">
            <h3>Open</h3>
            <p class="stat-number">${stats.open_complaints || 0}</p>
        </div>
        <div class="stat-card">
            <h3>In Progress</h3>
            <p class="stat-number">${stats.in_progress_complaints || 0}</p>
        </div>
        <div class="stat-card">
            <h3>Resolved</h3>
            <p class="stat-number">${stats.resolved_complaints || 0}</p>
        </div>
        <div class="stat-card overdue">
            <h3>Overdue</h3>
            <p class="stat-number">${stats.overdue_complaints || 0}</p>
        </div>
    `;
}

// Fix logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    currentUser = null;
    window.location.href = 'login.html';
}

// Fix utility functions
function showError(message) {
    const div = document.createElement('div');
    div.className = 'alert alert-error';
    div.textContent = message;
    document.body.prepend(div);
    setTimeout(() => div.remove(), 5000);
}

function showSuccess(message) {
    const div = document.createElement('div');
    div.className = 'alert alert-success';
    div.textContent = message;
    document.body.prepend(div);
    setTimeout(() => div.remove(), 5000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');

    if (userStr) {
        currentUser = JSON.parse(userStr);
    }

    // Check if on login/register page
    if (window.location.pathname.includes('login.html')) {
        // Login page specific code
    } else if (window.location.pathname.includes('register.html')) {
        // Register page specific code
    } else if (window.location.pathname.includes('resident.html')) {
        if (!token) {
            window.location.href = 'login.html';
        } else {
            loadComplaints();
            loadNotices();
            if (currentUser.role === 'admin') {
                loadDashboard();
            }
        }
    }
});