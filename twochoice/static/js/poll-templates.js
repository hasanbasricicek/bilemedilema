/**
 * Anket oluşturma şablonları ve emoji önerileri
 */

const POLL_TEMPLATES = [
    {
        title: "Hangisini seçerdin?",
        options: ["Seçenek A", "Seçenek B"]
    },
    {
        title: "Sence hangisi daha mantıklı?",
        options: ["İlk seçenek", "İkinci seçenek"]
    },
    {
        title: "Böyle bir durumda ne yapardın?",
        options: ["Birinci yol", "İkinci yol"]
    },
    {
        title: "Hangisi daha iyi?",
        options: ["A", "B"]
    },
    {
        title: "Tercih hangisi olurdu?",
        options: ["Birinci", "İkinci"]
    }
];

const EMOJI_SUGGESTIONS = {
    food: ["🍕", "🍔", "🍟", "🌮", "🍜", "🍱", "🍣", "🍰", "🍦", "☕"],
    travel: ["✈️", "🚗", "🏖️", "🏔️", "🗼", "🏰", "🌍", "🗺️", "🧳", "🎒"],
    tech: ["💻", "📱", "⌚", "🎮", "🖥️", "⌨️", "🖱️", "💾", "📷", "🎧"],
    sports: ["⚽", "🏀", "🎾", "🏐", "🏈", "⚾", "🏓", "🏸", "🥊", "🏊"],
    entertainment: ["🎬", "🎮", "🎵", "🎸", "🎤", "🎭", "🎪", "🎨", "📺", "🎯"],
    emotions: ["😊", "😂", "🤔", "😍", "🤩", "😎", "🥳", "😢", "😡", "🤗"],
    nature: ["🌸", "🌺", "🌻", "🌹", "🌷", "🌲", "🌳", "🌴", "🌵", "🍀"],
    animals: ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯"],
    objects: ["⭐", "💎", "🔥", "💧", "⚡", "🌟", "✨", "💫", "🎁", "🎈"]
};

document.addEventListener('DOMContentLoaded', function() {
    const titleInput = document.getElementById('id_title');
    const option1Input = document.getElementById('id_poll_option_1');
    const option2Input = document.getElementById('id_poll_option_2');
    
    if (!titleInput) return;
    
    // Şablon seçici oluştur
    const templateSelector = createTemplateSelector();
    titleInput.parentElement.insertBefore(templateSelector, titleInput);
    
    // Emoji picker'ları ekle
    addEmojiPicker(option1Input);
    addEmojiPicker(option2Input);
    
    const option3Input = document.getElementById('id_poll_option_3');
    const option4Input = document.getElementById('id_poll_option_4');
    if (option3Input) addEmojiPicker(option3Input);
    if (option4Input) addEmojiPicker(option4Input);
});

function createTemplateSelector() {
    const container = document.createElement('div');
    container.className = 'mb-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200';
    
    container.innerHTML = `
        <div class="flex items-center gap-2 mb-3">
            <i class="fas fa-magic text-purple-600"></i>
            <h4 class="text-sm font-bold text-gray-900">✨ Hızlı Şablonlar</h4>
        </div>
        <div class="flex flex-wrap gap-2">
            ${POLL_TEMPLATES.map((template, idx) => `
                <button type="button" 
                        class="template-btn px-3 py-2 bg-white hover:bg-purple-100 border border-purple-200 rounded-lg text-xs font-medium text-gray-700 transition duration-200"
                        data-template-idx="${idx}">
                    ${template.title}
                </button>
            `).join('')}
        </div>
    `;
    
    // Template butonlarına click event ekle
    container.querySelectorAll('.template-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const idx = parseInt(this.dataset.templateIdx);
            const template = POLL_TEMPLATES[idx];
            
            document.getElementById('id_title').value = template.title;
            document.getElementById('id_poll_option_1').value = template.options[0];
            document.getElementById('id_poll_option_2').value = template.options[1];
            
            // Animasyon efekti
            this.classList.add('scale-95');
            setTimeout(() => this.classList.remove('scale-95'), 100);
            
            showToast('Şablon uygulandı! ✨');
        });
    });
    
    return container;
}

function addEmojiPicker(input) {
    if (!input) return;
    
    const container = input.parentElement;
    const emojiBtn = document.createElement('button');
    emojiBtn.type = 'button';
    emojiBtn.className = 'mt-2 px-3 py-1.5 bg-gradient-to-r from-yellow-400 to-orange-400 hover:from-yellow-500 hover:to-orange-500 text-white rounded-lg text-xs font-medium transition duration-200';
    emojiBtn.innerHTML = '<i class="fas fa-smile"></i> Emoji Ekle';
    
    emojiBtn.addEventListener('click', function() {
        showEmojiPicker(input);
    });
    
    container.appendChild(emojiBtn);
}

function showEmojiPicker(targetInput) {
    // Modal oluştur
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4';
    
    modal.innerHTML = `
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-xl font-bold text-gray-900">Emoji Seç</h3>
                <button class="close-modal text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            
            <div class="space-y-4">
                ${Object.entries(EMOJI_SUGGESTIONS).map(([category, emojis]) => `
                    <div>
                        <h4 class="text-sm font-semibold text-gray-700 mb-2 capitalize">${getCategoryName(category)}</h4>
                        <div class="grid grid-cols-10 gap-2">
                            ${emojis.map(emoji => `
                                <button type="button" 
                                        class="emoji-btn text-2xl hover:scale-125 transition duration-200 p-2 rounded-lg hover:bg-gray-100"
                                        data-emoji="${emoji}">
                                    ${emoji}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal
    modal.querySelector('.close-modal').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
    
    // Emoji seçimi
    modal.querySelectorAll('.emoji-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const emoji = this.dataset.emoji;
            targetInput.value += emoji;
            modal.remove();
            showToast('Emoji eklendi! ' + emoji);
        });
    });
}

function getCategoryName(category) {
    const names = {
        food: '🍕 Yemek',
        travel: '✈️ Seyahat',
        tech: '💻 Teknoloji',
        sports: '⚽ Spor',
        entertainment: '🎬 Eğlence',
        emotions: '😊 Duygular',
        nature: '🌸 Doğa',
        animals: '🐶 Hayvanlar',
        objects: '⭐ Nesneler'
    };
    return names[category] || category;
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 2000);
}
