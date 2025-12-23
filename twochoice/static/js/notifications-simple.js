/**
 * Simple Notification Dropdown - Guaranteed to work
 */

(function() {
    'use strict';
    
    let isOpen = false;
    let dropdown = null;
    let backdrop = null;
    let button = null;
    
    function init() {
        button = document.getElementById('nav-notifications-desktop');
        if (!button) {
            console.warn('Notification button not found');
            return;
        }
        
        createElements();
        attachEvents();
        console.log('Notification system initialized');
    }
    
    function createElements() {
        // Create backdrop
        backdrop = document.createElement('div');
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 999;
            background: transparent;
            display: none;
        `;
        backdrop.id = 'notification-backdrop';
        
        // Create dropdown
        dropdown = document.createElement('div');
        dropdown.style.cssText = `
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
            display: none;
        `;
        dropdown.id = 'notification-dropdown';
        
        document.body.appendChild(backdrop);
        document.body.appendChild(dropdown);
    }
    
    function attachEvents() {
        // Button click
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggle();
        });
        
        // Backdrop click
        backdrop.addEventListener('click', function() {
            close();
        });
        
        // ESC key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && isOpen) {
                close();
            }
        });
    }
    
    function toggle() {
        if (isOpen) {
            close();
        } else {
            open();
        }
    }
    
    function open() {
        isOpen = true;
        
        // Position dropdown
        const rect = button.getBoundingClientRect();
        dropdown.style.top = (rect.bottom + 8) + 'px';
        dropdown.style.right = (window.innerWidth - rect.right) + 'px';
        
        backdrop.style.display = 'block';
        dropdown.style.display = 'block';
        
        loadNotifications();
        console.log('Dropdown opened');
    }
    
    function close() {
        isOpen = false;
        backdrop.style.display = 'none';
        dropdown.style.display = 'none';
        console.log('Dropdown closed');
    }
    
    function loadNotifications() {
        fetch('/notifications/latest-unread/')
            .then(response => response.json())
            .then(data => {
                renderNotifications(data.notifications || []);
            })
            .catch(error => {
                console.error('Error loading notifications:', error);
                dropdown.innerHTML = '<div style="padding: 2rem; text-align: center;">Bildirimler yüklenemedi</div>';
            });
    }
    
    function renderNotifications(notifications) {
        if (notifications.length === 0) {
            dropdown.innerHTML = `
                <div style="padding: 3rem; text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔔</div>
                    <div style="color: #6B7280; font-size: 0.875rem;">Henüz bildirim yok</div>
                </div>
            `;
            return;
        }
        
        let html = `
            <div style="padding: 1rem; border-bottom: 1px solid #E5E7EB; display: flex; justify-content: space-between; align-items: center;">
                <h3 style="font-weight: 700; font-size: 1rem; margin: 0;">Bildirimler</h3>
                <button onclick="window.markAllNotificationsRead()" style="color: #8B5CF6; font-size: 0.875rem; font-weight: 600; cursor: pointer; background: none; border: none;">
                    Tümünü Okundu İşaretle
                </button>
            </div>
            <div style="overflow-y: auto; max-height: 400px;">
        `;
        
        notifications.forEach(notif => {
            const isUnread = !notif.is_read;
            html += `
                <div style="padding: 1rem; border-bottom: 1px solid #F3F4F6; cursor: pointer; ${isUnread ? 'background: rgba(139, 92, 246, 0.05);' : ''}"
                     onclick="window.handleNotificationClick(${notif.id}, '${notif.url}')">
                    <div style="display: flex; gap: 0.75rem;">
                        ${isUnread ? '<div style="width: 8px; height: 8px; border-radius: 50%; background: #8B5CF6; margin-top: 0.25rem;"></div>' : '<div style="width: 8px;"></div>'}
                        <div style="flex: 1;">
                            <div style="font-weight: ${isUnread ? '600' : '400'}; color: #111827; font-size: 0.875rem; margin-bottom: 0.25rem;">
                                ${escapeHtml(notif.text)}
                            </div>
                            <div style="color: #6B7280; font-size: 0.75rem;">
                                ${formatTime(notif.created_at)}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `
            </div>
            <div style="padding: 0.75rem; text-align: center; border-top: 1px solid #E5E7EB;">
                <a href="/notifications/" style="color: #8B5CF6; font-size: 0.875rem; font-weight: 600; text-decoration: none;">
                    Tüm Bildirimleri Gör
                </a>
            </div>
        `;
        
        dropdown.innerHTML = html;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'Az önce';
        if (diff < 3600) return Math.floor(diff / 60) + ' dakika önce';
        if (diff < 86400) return Math.floor(diff / 3600) + ' saat önce';
        return Math.floor(diff / 86400) + ' gün önce';
    }
    
    // Global functions
    window.handleNotificationClick = function(id, url) {
        fetch('/notifications/' + id + '/read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            }
        }).then(() => {
            if (url && url !== 'None' && url !== 'undefined') {
                window.location.href = url;
            }
        });
    };
    
    window.markAllNotificationsRead = function() {
        fetch('/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            }
        }).then(() => {
            loadNotifications();
        });
    };
    
    function getCookie(name) {
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
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
