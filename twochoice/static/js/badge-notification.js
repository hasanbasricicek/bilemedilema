// Badge Notification System

// Show badge earned popup
function showBadgeEarnedPopup(badge) {
    const popup = document.createElement('div');
    popup.className = 'badge-earned-popup';
    popup.innerHTML = `
        <div class="badge-earned-content">
            <div class="badge-earned-confetti"></div>
            <div class="badge-earned-icon">${badge.icon}</div>
            <h3 class="badge-earned-title">Yeni Rozet Kazandın! 🎉</h3>
            <div class="badge-earned-badge" style="border-color: ${badge.color}40; background: ${badge.color}10;">
                <span class="badge-icon">${badge.icon}</span>
                <span class="badge-name" style="color: ${badge.color};">${badge.name}</span>
            </div>
            <p class="badge-earned-description">${badge.description}</p>
            <button class="badge-earned-close" onclick="this.closest('.badge-earned-popup').remove()">
                Harika!
            </button>
        </div>
    `;
    
    document.body.appendChild(popup);
    
    // Trigger confetti
    setTimeout(() => {
        if (typeof confetti !== 'undefined') {
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
            });
        }
    }, 300);
    
    // Show popup with animation
    setTimeout(() => {
        popup.classList.add('show');
    }, 10);
    
    // Auto close after 8 seconds
    setTimeout(() => {
        if (popup.parentElement) {
            popup.classList.remove('show');
            setTimeout(() => popup.remove(), 300);
        }
    }, 8000);
}

// Check for new badges after actions
async function checkNewBadges() {
    try {
        const response = await fetch('/api/check-new-badges/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.new_badges && data.new_badges.length > 0) {
                // Show popup for each new badge (with delay)
                data.new_badges.forEach((badge, index) => {
                    setTimeout(() => {
                        showBadgeEarnedPopup(badge);
                    }, index * 500);
                });
            }
        }
    } catch (error) {
        console.error('Error checking badges:', error);
    }
}

// Listen for badge-earning events
document.addEventListener('DOMContentLoaded', () => {
    // Check after vote
    document.addEventListener('vote-success', () => {
        setTimeout(checkNewBadges, 1000);
    });
    
    // Check after comment
    document.addEventListener('comment-success', () => {
        setTimeout(checkNewBadges, 1000);
    });
    
    // Check after post creation
    document.addEventListener('post-created', () => {
        setTimeout(checkNewBadges, 1000);
    });
});

// CSS for badge popup
const style = document.createElement('style');
style.textContent = `
    .badge-earned-popup {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.5);
        opacity: 0;
        transition: opacity 0.3s ease-in-out;
        backdrop-filter: blur(4px);
    }
    
    .badge-earned-popup.show {
        opacity: 1;
    }
    
    .badge-earned-content {
        background: white;
        border-radius: 24px;
        padding: 32px;
        max-width: 400px;
        width: 90%;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        transform: scale(0.8);
        transition: transform 0.3s ease-in-out;
        position: relative;
        overflow: hidden;
    }
    
    .badge-earned-popup.show .badge-earned-content {
        transform: scale(1);
    }
    
    .badge-earned-icon {
        font-size: 64px;
        margin-bottom: 16px;
        animation: bounce 0.6s ease-in-out;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    
    .badge-earned-title {
        font-size: 24px;
        font-weight: bold;
        color: #000;
        margin-bottom: 20px;
    }
    
    .badge-earned-badge {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        padding: 16px 24px;
        border-radius: 16px;
        border: 2px solid;
        margin-bottom: 16px;
    }
    
    .badge-earned-badge .badge-icon {
        font-size: 32px;
    }
    
    .badge-earned-badge .badge-name {
        font-size: 18px;
        font-weight: bold;
    }
    
    .badge-earned-description {
        color: #666A73;
        font-size: 14px;
        margin-bottom: 24px;
    }
    
    .badge-earned-close {
        background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
        color: white;
        border: none;
        padding: 12px 32px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .badge-earned-close:hover {
        transform: scale(1.05);
    }
    
    @media (max-width: 640px) {
        .badge-earned-content {
            padding: 24px;
        }
        
        .badge-earned-icon {
            font-size: 48px;
        }
        
        .badge-earned-title {
            font-size: 20px;
        }
    }
`;
document.head.appendChild(style);
