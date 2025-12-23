/**
 * Poll Expiry Countdown Timer
 * Shows real-time countdown for polls that are about to close
 */

(function() {
    'use strict';
    
    const activeIntervals = new Map();
    
    function initCountdowns() {
        const countdownElements = document.querySelectorAll('[data-poll-expires]');
        
        countdownElements.forEach(element => {
            const expiryTime = element.dataset.pollExpires;
            if (expiryTime && expiryTime !== 'None') {
                // Clear existing interval if any
                const existingInterval = activeIntervals.get(element);
                if (existingInterval) {
                    clearInterval(existingInterval);
                }
                
                // Initial update
                updateCountdown(element, expiryTime);
                
                // Update every second and store interval
                const intervalId = setInterval(() => updateCountdown(element, expiryTime), 1000);
                activeIntervals.set(element, intervalId);
            }
        });
    }
    
    function updateCountdown(element, expiryTime) {
        const now = new Date().getTime();
        const expiry = new Date(expiryTime).getTime();
        const diff = expiry - now;
        
        if (diff <= 0) {
            element.innerHTML = `
                <div class="poll-countdown closed">
                    <i class="fas fa-lock"></i>
                    <span>Anket Kapandı</span>
                </div>
            `;
            element.classList.add('expired');
            
            // Clear interval for expired countdown
            const intervalId = activeIntervals.get(element);
            if (intervalId) {
                clearInterval(intervalId);
                activeIntervals.delete(element);
            }
            return;
        }
        
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        let timeText = '';
        let urgencyClass = '';
        let icon = 'fa-clock';
        let urgencyText = '';
        
        // Determine urgency level
        if (diff < 5 * 60 * 1000) {
            // Less than 5 minutes - CRITICAL
            urgencyClass = 'critical';
            icon = 'fa-exclamation-triangle';
            urgencyText = '⚠️ SON 5 DAKİKA!';
            timeText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        } else if (diff < 30 * 60 * 1000) {
            // Less than 30 minutes - URGENT
            urgencyClass = 'urgent';
            icon = 'fa-hourglass-end';
            urgencyText = '🔥 SON 30 DAKİKA!';
            timeText = `${minutes} dakika ${seconds} saniye`;
        } else if (diff < 60 * 60 * 1000) {
            // Less than 1 hour - WARNING
            urgencyClass = 'warning';
            icon = 'fa-hourglass-half';
            timeText = `${minutes} dakika`;
        } else if (diff < 6 * 60 * 60 * 1000) {
            // Less than 6 hours - CAUTION
            urgencyClass = 'caution';
            icon = 'fa-clock';
            timeText = `${hours} saat ${minutes} dakika`;
        } else if (diff < 24 * 60 * 60 * 1000) {
            // Less than 24 hours - NORMAL
            urgencyClass = 'normal';
            icon = 'fa-clock';
            timeText = `${hours} saat`;
        } else {
            // More than 24 hours - SAFE
            urgencyClass = 'safe';
            icon = 'fa-clock';
            if (days === 1) {
                timeText = `1 gün ${hours} saat`;
            } else {
                timeText = `${days} gün`;
            }
        }
        
        element.innerHTML = `
            <div class="poll-countdown ${urgencyClass}">
                ${urgencyText ? `<div class="urgency-text">${urgencyText}</div>` : ''}
                <div class="countdown-content">
                    <i class="fas ${icon}"></i>
                    <span class="countdown-label">Kapanıyor:</span>
                    <span class="countdown-time">${timeText}</span>
                </div>
            </div>
        `;
        
        // Add pulsing animation for critical/urgent
        if (urgencyClass === 'critical' || urgencyClass === 'urgent') {
            element.classList.add('pulse');
        } else {
            element.classList.remove('pulse');
        }
    }
    
    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCountdowns);
    } else {
        initCountdowns();
    }
    
    // Re-initialize for dynamically loaded content
    window.initPollCountdowns = initCountdowns;
})();
