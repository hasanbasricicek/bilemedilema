// Emoji Picker for Comment Forms

const emojis = {
    'Yüzler': ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥', '😌', '😔', '😪', '🤤', '😴'],
    'Duygular': ['😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕'],
    'Jestler': ['👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '👇', '☝️', '👏', '🙌', '👐', '🤲', '🤝', '🙏', '✍️', '💪', '🦾', '🦿', '🦵', '🦶', '👂', '🦻', '👃', '🧠', '🦷', '🦴', '👀', '👁️', '👅', '👄'],
    'Kalpler': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟'],
    'Nesneler': ['⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱', '🪀', '🏓', '🏸', '🏒', '🏑', '🥍', '🏏', '🪃', '🥅', '⛳', '🪁', '🏹', '🎣', '🤿', '🥊', '🥋', '🎽', '🛹', '🛼', '🛷', '⛸️', '🥌', '🎿', '⛷️', '🏂'],
    'Semboller': ['✅', '❌', '⭐', '🌟', '✨', '💫', '🔥', '💯', '🎉', '🎊', '🎈', '🎁', '🏆', '🥇', '🥈', '🥉', '⚡', '💥', '💢', '💨', '💦', '💤', '🕳️', '🎯', '🎲', '🎰', '🎮', '🎴', '🃏', '🀄', '🎭', '🎨', '🧵', '🪡', '🧶', '🪢']
};

document.addEventListener('DOMContentLoaded', function() {
    const emojiTrigger = document.getElementById('emoji-trigger');
    const textarea = document.getElementById('id_content');
    
    if (!emojiTrigger || !textarea) return;
    
    let pickerElement = null;
    let isOpen = false;
    
    // Create picker
    function createPicker() {
        const picker = document.createElement('div');
        picker.className = 'emoji-picker-panel';
        picker.innerHTML = `
            <div class="emoji-picker-header">
                <div class="emoji-categories">
                    ${Object.keys(emojis).map(cat => `<button type="button" class="emoji-cat-btn" data-category="${cat}">${cat}</button>`).join('')}
                </div>
            </div>
            <div class="emoji-picker-body">
                ${Object.entries(emojis).map(([cat, emojiList]) => `
                    <div class="emoji-category" data-category="${cat}">
                        ${emojiList.map(emoji => `<button type="button" class="emoji-btn">${emoji}</button>`).join('')}
                    </div>
                `).join('')}
            </div>
        `;
        
        // Position picker
        const rect = textarea.getBoundingClientRect();
        picker.style.position = 'absolute';
        picker.style.bottom = '100%';
        picker.style.right = '0';
        picker.style.marginBottom = '8px';
        
        return picker;
    }
    
    // Toggle picker
    emojiTrigger.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (isOpen) {
            closePicker();
        } else {
            openPicker();
        }
    });
    
    function openPicker() {
        if (pickerElement) {
            pickerElement.remove();
        }
        
        pickerElement = createPicker();
        emojiTrigger.parentElement.appendChild(pickerElement);
        isOpen = true;
        
        // Show first category
        const firstCat = pickerElement.querySelector('.emoji-category');
        if (firstCat) firstCat.style.display = 'grid';
        
        // Category buttons
        pickerElement.querySelectorAll('.emoji-cat-btn').forEach((btn, index) => {
            btn.addEventListener('click', function() {
                const category = this.dataset.category;
                pickerElement.querySelectorAll('.emoji-category').forEach(cat => {
                    cat.style.display = cat.dataset.category === category ? 'grid' : 'none';
                });
                pickerElement.querySelectorAll('.emoji-cat-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
            if (index === 0) btn.classList.add('active');
        });
        
        // Emoji buttons
        pickerElement.querySelectorAll('.emoji-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                insertEmoji(this.textContent);
                closePicker();
            });
        });
    }
    
    function closePicker() {
        if (pickerElement) {
            pickerElement.remove();
            pickerElement = null;
        }
        isOpen = false;
    }
    
    function insertEmoji(emoji) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        
        textarea.value = text.substring(0, start) + emoji + text.substring(end);
        textarea.selectionStart = textarea.selectionEnd = start + emoji.length;
        textarea.focus();
    }
    
    // Close on outside click
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.emoji-picker-panel') && e.target !== emojiTrigger) {
            closePicker();
        }
    });
});

// Reply functionality
document.addEventListener('DOMContentLoaded', function() {
    const replyButtons = document.querySelectorAll('.reply-comment-btn');
    const replyIndicator = document.getElementById('reply-indicator');
    const replyToName = document.getElementById('reply-to-name');
    const cancelReply = document.getElementById('cancel-reply');
    const textarea = document.getElementById('id_content');
    
    if (!replyButtons.length || !replyIndicator || !textarea) return;
    
    replyButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const author = this.dataset.author;
            replyToName.textContent = author;
            replyIndicator.classList.remove('hidden');
            textarea.value = `@${author} `;
            textarea.focus();
            textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });
    
    if (cancelReply) {
        cancelReply.addEventListener('click', function() {
            replyIndicator.classList.add('hidden');
            textarea.value = '';
        });
    }
});

// CSS Styles for Emoji Picker
const style = document.createElement('style');
style.textContent = `
    .emoji-picker-panel {
        position: absolute;
        bottom: 100%;
        right: 0;
        margin-bottom: 8px;
        background: white;
        border: 2px solid #BFBFBF;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        width: 320px;
        max-height: 350px;
        z-index: 1000;
        overflow: hidden;
    }
    
    .emoji-picker-header {
        border-bottom: 1px solid #E5E7EB;
        padding: 8px;
        background: #F9FAFB;
    }
    
    .emoji-categories {
        display: flex;
        gap: 4px;
        overflow-x: auto;
        scrollbar-width: none;
    }
    
    .emoji-categories::-webkit-scrollbar {
        display: none;
    }
    
    .emoji-cat-btn {
        padding: 6px 12px;
        border: none;
        background: transparent;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        color: #666A73;
        cursor: pointer;
        white-space: nowrap;
        transition: all 0.2s;
    }
    
    .emoji-cat-btn:hover {
        background: #E5E7EB;
        color: #000;
    }
    
    .emoji-cat-btn.active {
        background: #8B5CF6;
        color: white;
    }
    
    .emoji-picker-body {
        padding: 12px;
        max-height: 280px;
        overflow-y: auto;
    }
    
    .emoji-category {
        display: none;
        grid-template-columns: repeat(8, 1fr);
        gap: 4px;
    }
    
    .emoji-btn {
        background: transparent;
        border: none;
        font-size: 24px;
        padding: 8px;
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .emoji-btn:hover {
        background: #F3F4F6;
        transform: scale(1.2);
    }
    
    .emoji-btn:active {
        transform: scale(1.1);
    }
    
    @media (max-width: 640px) {
        .emoji-picker-panel {
            width: 280px;
            max-height: 300px;
        }
        
        .emoji-category {
            grid-template-columns: repeat(6, 1fr);
        }
        
        .emoji-btn {
            font-size: 20px;
            padding: 6px;
        }
    }
`;
document.head.appendChild(style);
