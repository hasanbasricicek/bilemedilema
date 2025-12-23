/**
 * Enhanced Notification System with Real-time Updates
 */

class NotificationSystem {
    constructor() {
        this.dropdown = null;
        this.badge = null;
        this.button = null;
        this.unreadCount = 0;
        this.notifications = [];
        this.isOpen = false;
        this.updateInterval = null;
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initElements());
        } else {
            this.initElements();
        }
    }
    
    initElements() {
        this.button = document.getElementById('nav-notifications-desktop');
        this.badge = document.getElementById('notifications-unread-badge-desktop');
        
        if (!this.button) {
            console.warn('Notification button not found');
            return;
        }
        
        this.createDropdown();
        this.attachEventListeners();
        this.startPolling();
        this.loadNotifications();
    }
    
    createDropdown() {
        // Create backdrop
        this.backdrop = document.createElement('div');
        this.backdrop.className = 'notification-backdrop hidden';
        this.backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 999;
            background: transparent;
        `;
        
        // Create dropdown
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'notification-dropdown hidden';
        this.dropdown.style.cssText = `
            position: fixed;
            width: 380px;
            max-width: 90vw;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 1rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            z-index: 1000;
            max-height: 500px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        `;
        
        // Position relative to button
        const buttonRect = this.button.getBoundingClientRect();
        this.dropdown.style.top = `${buttonRect.bottom + 8}px`;
        this.dropdown.style.right = `${window.innerWidth - buttonRect.right}px`;
        
        document.body.appendChild(this.backdrop);
        document.body.appendChild(this.dropdown);
    }
    
    attachEventListeners() {
        // Toggle dropdown on button click
        this.button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (this.isOpen) {
                this.closeDropdown();
            } else {
                this.openDropdown();
            }
        });
        
        // Close dropdown when clicking backdrop
        this.backdrop.addEventListener('click', () => {
            this.closeDropdown();
        });
        
        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeDropdown();
            }
        });
    }
    
    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }
    
    openDropdown() {
        this.isOpen = true;
        this.backdrop.classList.remove('hidden');
        this.dropdown.classList.remove('hidden');
        this.renderNotifications();
    }
    
    closeDropdown() {
        this.isOpen = false;
        this.backdrop.classList.add('hidden');
        this.dropdown.classList.add('hidden');
    }
    
    async loadNotifications() {
        try {
            const response = await fetch('/notifications/latest-unread/');
            const data = await response.json();
            
            this.notifications = data.notifications || [];
            this.unreadCount = data.unread_count || 0;
            
            this.updateBadge();
            
            if (this.isOpen) {
                this.renderNotifications();
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }
    
    updateBadge() {
        if (this.unreadCount > 0) {
            this.badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            this.badge.classList.remove('hidden');
        } else {
            this.badge.classList.add('hidden');
        }
    }
    
    renderNotifications() {
        if (this.notifications.length === 0) {
            this.dropdown.innerHTML = `
                <div style="padding: 3rem; text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔔</div>
                    <div style="color: #6B7280; font-size: 0.875rem;">Henüz bildirim yok</div>
                </div>
            `;
            return;
        }
        
        const header = `
            <div style="padding: 1rem; border-bottom: 1px solid #E5E7EB; display: flex; justify-content: space-between; align-items: center;">
                <h3 style="font-weight: 700; font-size: 1rem;">Bildirimler</h3>
                <button onclick="notificationSystem.markAllAsRead()" style="color: #8B5CF6; font-size: 0.875rem; font-weight: 600; cursor: pointer; background: none; border: none;">
                    Tümünü Okundu İşaretle
                </button>
            </div>
        `;
        
        const notificationsList = this.notifications.map(notif => {
            const isUnread = !notif.is_read;
            const notifUrl = notif.url || notif.target_url || '/notifications/';
            const notifText = notif.text || notif.message || 'Yeni bildirim';
            return `
                <div class="notification-item ${isUnread ? 'unread' : ''}" 
                     data-id="${notif.id}"
                     data-url="${this.escapeHtml(notifUrl)}"
                     style="padding: 1rem; border-bottom: 1px solid #F3F4F6; cursor: pointer; transition: background 0.2s; ${isUnread ? 'background: rgba(139, 92, 246, 0.05);' : ''}"
                     onmouseenter="this.style.background='#F9FAFB'"
                     onmouseleave="this.style.background='${isUnread ? 'rgba(139, 92, 246, 0.05)' : 'white'}'"
                     onclick="notificationSystem.handleNotificationClick(${notif.id}, this.dataset.url)">
                    <div style="display: flex; gap: 0.75rem;">
                        ${isUnread ? '<div style="width: 8px; height: 8px; border-radius: 50%; background: #8B5CF6; margin-top: 0.25rem;"></div>' : '<div style="width: 8px;"></div>'}
                        <div style="flex: 1;">
                            <div style="font-weight: ${isUnread ? '600' : '400'}; color: #111827; font-size: 0.875rem; margin-bottom: 0.25rem;">
                                ${this.escapeHtml(notifText)}
                            </div>
                            <div style="color: #6B7280; font-size: 0.75rem;">
                                ${this.formatTime(notif.created_at)}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        const footer = `
            <div style="padding: 0.75rem; text-align: center; border-top: 1px solid #E5E7EB;">
                <a href="/notifications/" style="color: #8B5CF6; font-size: 0.875rem; font-weight: 600; text-decoration: none;">
                    Tüm Bildirimleri Gör
                </a>
            </div>
        `;
        
        this.dropdown.innerHTML = header + `<div style="overflow-y: auto; max-height: 400px;">${notificationsList}</div>` + footer;
    }
    
    async handleNotificationClick(notificationId, targetUrl) {
        try {
            // Mark as read
            await fetch(`/notifications/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            // Update UI immediately
            const notifElement = document.querySelector(`[data-id="${notificationId}"]`);
            if (notifElement) {
                notifElement.style.background = 'white';
                const dot = notifElement.querySelector('div[style*="background: #8B5CF6"]');
                if (dot) {
                    dot.style.width = '8px';
                    dot.style.background = 'transparent';
                }
            }
            
            // Reload notifications in background
            this.loadNotifications();
            
            // Navigate to target
            if (targetUrl && targetUrl !== 'None' && targetUrl !== 'undefined') {
                window.location.href = targetUrl;
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            await fetch('/notifications/read-all/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            this.loadNotifications();
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }
    
    startPolling() {
        // Poll every 15 seconds for better sync
        this.updateInterval = setInterval(() => {
            this.loadNotifications();
        }, 15000);
        
        // Also poll when page becomes visible again
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadNotifications();
            }
        });
    }
    
    stopPolling() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'Az önce';
        if (diff < 3600) return `${Math.floor(diff / 60)} dakika önce`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} saat önce`;
        if (diff < 604800) return `${Math.floor(diff / 86400)} gün önce`;
        
        return date.toLocaleDateString('tr-TR');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize notification system
let notificationSystem;
document.addEventListener('DOMContentLoaded', () => {
    notificationSystem = new NotificationSystem();
});
