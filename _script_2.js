
function showToast(title, msg, type='info', dur=4500) {
  const c = document.getElementById('toasts');
  if (!c) return;
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.innerHTML = `
    <div class="toast-bar"></div>
    <div style="flex:1">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${msg}</div>
    </div>
    <button class="toast-x" onclick="this.closest('.toast').remove()">✕</button>`;
  c.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'toastOut 0.25s ease forwards';
    setTimeout(() => t.remove(), 250);
  }, dur);
}
const showSuccess = (m,t='Success') => showToast(t,m,'success');
const showError   = (m,t='Error')   => showToast(t,m,'error',  8000);
const showWarning = (m,t='Warning') => showToast(t,m,'warning',6000);
const showInfo    = (m,t='Info')    => showToast(t,m,'info',   4000);

// Global search — pages can override this
function globalSearchFn(q) {
  q = q.toLowerCase();
  document.querySelectorAll('[data-searchable]').forEach(r => {
    r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// Notification system
let notifications = [];
let notificationInterval;

function toggleNotifications() {
  console.log('Notification button clicked!');
  const dropdown = document.getElementById('notifDropdown');
  console.log('Dropdown element found:', dropdown);
  
  if (dropdown) {
    dropdown.classList.toggle('show');
    console.log('Dropdown classes after toggle:', dropdown.className);
    console.log('Is show class present?', dropdown.classList.contains('show'));
    
    // Close when clicking outside
    if (dropdown.classList.contains('show')) {
      setTimeout(() => {
        document.addEventListener('click', closeNotificationsOutside);
      }, 100);
    }
  } else {
    console.error('notifDropdown element not found!');
  }
}

function closeNotificationsOutside(e) {
  const dropdown = document.getElementById('notifDropdown');
  if (!dropdown.contains(e.target) && !e.target.closest('.notif-btn')) {
    dropdown.classList.remove('show');
    document.removeEventListener('click', closeNotificationsOutside);
  }
}

function loadNotifications() {
  console.log('Loading notifications...');
  fetch('/api/contact-messages/unread')
    .then(response => response.json())
    .then(data => {
      console.log('Notifications data received:', data);
      notifications = data;
      updateNotificationUI();
    })
    .catch(error => console.error('Error loading notifications:', error));
}

function updateNotificationUI() {
  console.log('Updating notification UI with:', notifications);
  const notifCount = document.getElementById('notifCount');
  const notifList = document.getElementById('notifList');
  
  console.log('notifCount element:', notifCount);
  console.log('notifList element:', notifList);
  
  if (notifications.length === 0) {
    console.log('No notifications, hiding count');
    if (notifCount) notifCount.style.display = 'none';
    if (notifList) notifList.innerHTML = '<div class="notif-empty">No new notifications</div>';
  } else {
    console.log('Found', notifications.length, 'notifications');
    if (notifCount) {
      notifCount.style.display = 'block';
      notifCount.textContent = notifications.length;
    }
    
    const notifHTML = notifications.map(notif => `
      <div class="notif-item unread" onclick="markAsRead(${notif.id})">
        <div class="notif-title">New Contact Message</div>
        <div class="notif-message">${notif.name}: ${notif.subject}</div>
        <div class="notif-time">${formatTime(notif.created_at)}</div>
      </div>
    `).join('');
    
    console.log('Generated notification HTML:', notifHTML);
    if (notifList) notifList.innerHTML = notifHTML;
  }
}

function markAsRead(messageId) {
  fetch(`/api/contact-messages/${messageId}/mark-read`, {
    method: 'PUT'
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Remove from notifications list
      notifications = notifications.filter(n => n.id !== messageId);
      updateNotificationUI();
      showSuccess('Message marked as read');
    }
  })
  .catch(error => console.error('Error marking as read:', error));
}

function clearAllNotifications() {
  if (notifications.length === 0) return;
  
  if (confirm('Clear all notifications?')) {
    Promise.all(notifications.map(n => 
      fetch(`/api/contact-messages/${n.id}/mark-read`, { method: 'PUT' })
    ))
    .then(() => {
      notifications = [];
      updateNotificationUI();
      showSuccess('All notifications cleared');
    })
    .catch(error => console.error('Error clearing notifications:', error));
  }
}

function formatTime(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return Math.floor(diff / 60000) + ' minutes ago';
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' hours ago';
  return date.toLocaleDateString();
}

// Auto-refresh notifications every 30 seconds
function startNotificationRefresh() {
  loadNotifications();
  notificationInterval = setInterval(loadNotifications, 30000);
}

// Stop refresh when page is hidden
document.addEventListener('visibilitychange', function() {
  if (document.hidden) {
    clearInterval(notificationInterval);
  } else {
    startNotificationRefresh();
  }
});

// Start notification system
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(startNotificationRefresh, 500); // Small delay to ensure page is ready
});
