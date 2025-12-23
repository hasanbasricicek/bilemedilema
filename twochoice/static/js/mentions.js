/**
 * User Mentions (@username) System
 */

class MentionSystem {
    constructor(textareaSelector) {
        this.textarea = document.querySelector(textareaSelector);
        if (!this.textarea) return;
        
        this.dropdown = null;
        this.users = [];
        this.selectedIndex = -1;
        this.mentionStart = -1;
        this.searchQuery = '';
        
        this.init();
    }
    
    init() {
        this.createDropdown();
        this.attachEventListeners();
    }
    
    createDropdown() {
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'mention-dropdown hidden';
        this.dropdown.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 0.5rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            min-width: 200px;
        `;
        document.body.appendChild(this.dropdown);
    }
    
    attachEventListeners() {
        this.textarea.addEventListener('input', (e) => this.handleInput(e));
        this.textarea.addEventListener('keydown', (e) => this.handleKeydown(e));
        document.addEventListener('click', (e) => {
            if (!this.dropdown.contains(e.target) && e.target !== this.textarea) {
                this.hideDropdown();
            }
        });
    }
    
    handleInput(e) {
        const text = this.textarea.value;
        const cursorPos = this.textarea.selectionStart;
        
        // Find @ symbol before cursor
        let atPos = -1;
        for (let i = cursorPos - 1; i >= 0; i--) {
            if (text[i] === '@') {
                atPos = i;
                break;
            }
            if (text[i] === ' ' || text[i] === '\n') {
                break;
            }
        }
        
        if (atPos !== -1) {
            this.mentionStart = atPos;
            this.searchQuery = text.substring(atPos + 1, cursorPos);
            this.searchUsers(this.searchQuery);
        } else {
            this.hideDropdown();
        }
    }
    
    async searchUsers(query) {
        if (query.length < 1) {
            this.hideDropdown();
            return;
        }
        
        try {
            const response = await fetch(`/api/search-users/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.users = data.users || [];
            this.showDropdown();
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }
    
    showDropdown() {
        if (this.users.length === 0) {
            this.hideDropdown();
            return;
        }
        
        // Position dropdown
        const rect = this.textarea.getBoundingClientRect();
        const lineHeight = parseInt(window.getComputedStyle(this.textarea).lineHeight);
        this.dropdown.style.top = `${rect.top + lineHeight}px`;
        this.dropdown.style.left = `${rect.left}px`;
        
        // Render users
        this.dropdown.innerHTML = this.users.map((user, index) => `
            <div class="mention-item ${index === this.selectedIndex ? 'selected' : ''}" 
                 data-index="${index}"
                 style="padding: 0.5rem 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #8B5CF6, #EC4899); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.875rem;">
                    ${user.username.substring(0, 2).toUpperCase()}
                </div>
                <div>
                    <div style="font-weight: 600; color: #111827;">@${user.username}</div>
                </div>
            </div>
        `).join('');
        
        this.dropdown.classList.remove('hidden');
        
        // Add click handlers
        this.dropdown.querySelectorAll('.mention-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.selectUser(index);
            });
            
            item.addEventListener('mouseenter', () => {
                this.selectedIndex = parseInt(item.dataset.index);
                this.updateSelection();
            });
        });
    }
    
    hideDropdown() {
        this.dropdown.classList.add('hidden');
        this.selectedIndex = -1;
        this.users = [];
    }
    
    handleKeydown(e) {
        if (!this.dropdown.classList.contains('hidden')) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.users.length - 1);
                this.updateSelection();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.updateSelection();
            } else if (e.key === 'Enter' && this.selectedIndex >= 0) {
                e.preventDefault();
                this.selectUser(this.selectedIndex);
            } else if (e.key === 'Escape') {
                this.hideDropdown();
            }
        }
    }
    
    updateSelection() {
        this.dropdown.querySelectorAll('.mention-item').forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.style.background = '#F3F4F6';
            } else {
                item.style.background = 'white';
            }
        });
    }
    
    selectUser(index) {
        if (index < 0 || index >= this.users.length) return;
        
        const user = this.users[index];
        const text = this.textarea.value;
        const before = text.substring(0, this.mentionStart);
        const after = text.substring(this.textarea.selectionStart);
        
        this.textarea.value = `${before}@${user.username} ${after}`;
        this.textarea.selectionStart = this.textarea.selectionEnd = 
            this.mentionStart + user.username.length + 2;
        
        this.hideDropdown();
        this.textarea.focus();
    }
}

// Initialize mention system on page load
document.addEventListener('DOMContentLoaded', () => {
    // For comment forms
    const commentTextarea = document.querySelector('#id_content');
    if (commentTextarea) {
        new MentionSystem('#id_content');
    }
    
    // For post creation
    const postTextarea = document.querySelector('#id_content, textarea[name="content"]');
    if (postTextarea && !commentTextarea) {
        new MentionSystem('textarea[name="content"]');
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MentionSystem;
}
