/**
 * Comment Reactions System
 */

const REACTIONS = {
    'like': { emoji: '👍', label: 'Beğen' },
    'love': { emoji: '❤️', label: 'Sevdim' },
    'laugh': { emoji: '😂', label: 'Komik' },
    'think': { emoji: '🤔', label: 'Düşündürücü' }
};

class CommentReactions {
    constructor() {
        this.init();
    }
    
    init() {
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        document.addEventListener('click', (e) => {
            // Reaction button click
            if (e.target.closest('.reaction-btn')) {
                const btn = e.target.closest('.reaction-btn');
                const commentId = btn.dataset.commentId;
                const reaction = btn.dataset.reaction;
                this.toggleReaction(commentId, reaction, btn);
            }
            
            // Show reaction picker
            if (e.target.closest('.show-reactions')) {
                e.preventDefault();
                const btn = e.target.closest('.show-reactions');
                const commentId = btn.dataset.commentId;
                this.showReactionPicker(commentId, btn);
            }
        });
        
        // Close picker on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.reaction-picker') && !e.target.closest('.show-reactions')) {
                this.closeAllPickers();
            }
        });
    }
    
    showReactionPicker(commentId, button) {
        this.closeAllPickers();
        
        const picker = document.createElement('div');
        picker.className = 'reaction-picker';
        picker.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 2rem;
            padding: 0.5rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            display: flex;
            gap: 0.25rem;
            z-index: 1000;
        `;
        
        Object.entries(REACTIONS).forEach(([key, data]) => {
            const btn = document.createElement('button');
            btn.className = 'reaction-btn';
            btn.dataset.commentId = commentId;
            btn.dataset.reaction = key;
            btn.textContent = data.emoji;
            btn.title = data.label;
            btn.style.cssText = `
                font-size: 1.5rem;
                padding: 0.5rem;
                border: none;
                background: none;
                cursor: pointer;
                border-radius: 50%;
                transition: transform 0.2s;
            `;
            btn.onmouseenter = () => btn.style.transform = 'scale(1.3)';
            btn.onmouseleave = () => btn.style.transform = 'scale(1)';
            picker.appendChild(btn);
        });
        
        const rect = button.getBoundingClientRect();
        picker.style.position = 'fixed';
        picker.style.top = `${rect.top - 60}px`;
        picker.style.left = `${rect.left}px`;
        
        document.body.appendChild(picker);
    }
    
    closeAllPickers() {
        document.querySelectorAll('.reaction-picker').forEach(p => p.remove());
    }
    
    async toggleReaction(commentId, reaction, button) {
        try {
            const response = await fetch(`/api/comment/${commentId}/react/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({ reaction })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateReactionDisplay(commentId, data.reactions);
                this.closeAllPickers();
            }
        } catch (error) {
            console.error('Error toggling reaction:', error);
        }
    }
    
    updateReactionDisplay(commentId, reactions) {
        const container = document.querySelector(`[data-reactions-for="${commentId}"]`);
        if (!container) return;
        
        container.innerHTML = '';
        
        Object.entries(reactions).forEach(([key, count]) => {
            if (count > 0) {
                const badge = document.createElement('span');
                badge.className = 'reaction-badge';
                badge.style.cssText = `
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                    padding: 0.25rem 0.5rem;
                    background: #F3F4F6;
                    border-radius: 1rem;
                    font-size: 0.875rem;
                `;
                badge.innerHTML = `${REACTIONS[key].emoji} ${count}`;
                container.appendChild(badge);
            }
        });
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new CommentReactions();
});
