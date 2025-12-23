// Smart Search with Auto-complete and History

class SmartSearch {
    constructor(inputId, resultsId) {
        this.input = document.getElementById(inputId);
        this.results = document.getElementById(resultsId);
        if (!this.input) return;
        
        this.searchHistory = this.loadHistory();
        this.trendingSearches = ['Teknoloji', 'Spor', 'Eğlence', 'Eğitim', 'Günlük Hayat'];
        this.debounceTimer = null;
        
        this.init();
    }
    
    init() {
        // Create results container if not exists
        if (!this.results) {
            this.results = document.createElement('div');
            this.results.id = 'search-results';
            this.results.className = 'search-results-container';
            this.input.parentNode.appendChild(this.results);
        }
        
        // Input events
        this.input.addEventListener('focus', () => this.showResults());
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideResults();
            }
        });
    }
    
    handleInput(e) {
        clearTimeout(this.debounceTimer);
        const query = e.target.value.trim();
        
        if (query.length === 0) {
            this.showDefaultResults();
            return;
        }
        
        this.debounceTimer = setTimeout(() => {
            this.search(query);
        }, 300);
    }
    
    async search(query) {
        // Simulate API search - replace with actual endpoint
        const results = this.mockSearch(query);
        this.displayResults(results, query);
    }
    
    mockSearch(query) {
        // Mock search results - replace with actual API call
        const allTopics = [
            { type: 'topic', name: 'Teknoloji', icon: '💻', count: 45 },
            { type: 'topic', name: 'Spor', icon: '⚽', count: 32 },
            { type: 'topic', name: 'Eğlence', icon: '🎉', count: 28 },
            { type: 'topic', name: 'Eğitim', icon: '🎓', count: 21 },
            { type: 'topic', name: 'Günlük Hayat', icon: '🏡', count: 19 },
            { type: 'topic', name: 'Yaratıcı', icon: '🎨', count: 15 }
        ];
        
        return allTopics.filter(item => 
            item.name.toLowerCase().includes(query.toLowerCase())
        );
    }
    
    showDefaultResults() {
        let html = '<div class="search-results-section">';
        
        // Recent searches
        if (this.searchHistory.length > 0) {
            html += '<div class="search-section-title">Son Aramalar</div>';
            this.searchHistory.slice(0, 5).forEach(term => {
                html += `
                    <button class="search-result-item" data-query="${term}">
                        <i class="fas fa-history text-gray-400"></i>
                        <span>${term}</span>
                        <button class="search-remove" data-remove="${term}">
                            <i class="fas fa-times"></i>
                        </button>
                    </button>
                `;
            });
        }
        
        // Trending
        html += '<div class="search-section-title">Trend Aramalar</div>';
        this.trendingSearches.forEach(term => {
            html += `
                <button class="search-result-item" data-query="${term}">
                    <i class="fas fa-fire text-orange-500"></i>
                    <span>${term}</span>
                </button>
            `;
        });
        
        html += '</div>';
        this.results.innerHTML = html;
        this.attachResultEvents();
        this.showResults();
    }
    
    displayResults(results, query) {
        if (results.length === 0) {
            this.results.innerHTML = `
                <div class="search-no-results">
                    <i class="fas fa-search text-4xl text-gray-300 mb-2"></i>
                    <p class="text-gray-500">Sonuç bulunamadı</p>
                </div>
            `;
            this.showResults();
            return;
        }
        
        let html = '<div class="search-results-section">';
        html += '<div class="search-section-title">Sonuçlar</div>';
        
        results.forEach(item => {
            html += `
                <button class="search-result-item" data-query="${item.name}">
                    <span class="text-2xl">${item.icon}</span>
                    <span>${item.name}</span>
                    <span class="search-result-count">${item.count} anket</span>
                </button>
            `;
        });
        
        html += '</div>';
        this.results.innerHTML = html;
        this.attachResultEvents();
        this.showResults();
    }
    
    attachResultEvents() {
        this.results.querySelectorAll('[data-query]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const query = btn.dataset.query;
                this.selectResult(query);
            });
        });
        
        this.results.querySelectorAll('[data-remove]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const term = btn.dataset.remove;
                this.removeFromHistory(term);
            });
        });
    }
    
    selectResult(query) {
        this.input.value = query;
        this.addToHistory(query);
        this.hideResults();
        
        // Trigger search form submit or navigate
        const form = this.input.closest('form');
        if (form) {
            form.submit();
        }
    }
    
    handleKeyboard(e) {
        // TODO: Add keyboard navigation
    }
    
    showResults() {
        this.results.classList.add('show');
    }
    
    hideResults() {
        this.results.classList.remove('show');
    }
    
    addToHistory(term) {
        this.searchHistory = this.searchHistory.filter(t => t !== term);
        this.searchHistory.unshift(term);
        this.searchHistory = this.searchHistory.slice(0, 10);
        this.saveHistory();
    }
    
    removeFromHistory(term) {
        this.searchHistory = this.searchHistory.filter(t => t !== term);
        this.saveHistory();
        this.showDefaultResults();
    }
    
    loadHistory() {
        try {
            return JSON.parse(localStorage.getItem('search_history') || '[]');
        } catch {
            return [];
        }
    }
    
    saveHistory() {
        localStorage.setItem('search_history', JSON.stringify(this.searchHistory));
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new SmartSearch('search-input', 'search-results');
});

// CSS Styles
const style = document.createElement('style');
style.textContent = `
    .search-container {
        position: relative;
    }
    
    .search-results-container {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        margin-top: 8px;
        background: white;
        border: 2px solid #BFBFBF;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        max-height: 400px;
        overflow-y: auto;
        z-index: 1000;
        opacity: 0;
        transform: translateY(-10px);
        pointer-events: none;
        transition: all 0.3s ease;
    }
    
    .search-results-container.show {
        opacity: 1;
        transform: translateY(0);
        pointer-events: all;
    }
    
    .search-results-section {
        padding: 8px;
    }
    
    .search-section-title {
        font-size: 11px;
        font-weight: bold;
        color: #666A73;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 8px 12px;
        margin-top: 8px;
    }
    
    .search-section-title:first-child {
        margin-top: 0;
    }
    
    .search-result-item {
        width: 100%;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border: none;
        background: transparent;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }
    
    .search-result-item:hover {
        background: #F3F4F6;
    }
    
    .search-result-item span:nth-child(2) {
        flex: 1;
        font-size: 14px;
        color: #000;
    }
    
    .search-result-count {
        font-size: 12px;
        color: #666A73;
    }
    
    .search-remove {
        padding: 4px 8px;
        background: transparent;
        border: none;
        color: #666A73;
        cursor: pointer;
        border-radius: 6px;
        transition: all 0.2s;
    }
    
    .search-remove:hover {
        background: #EF4444;
        color: white;
    }
    
    .search-no-results {
        padding: 40px 20px;
        text-align: center;
    }
    
    @media (max-width: 640px) {
        .search-results-container {
            position: fixed;
            top: auto;
            bottom: 0;
            left: 0;
            right: 0;
            margin: 0;
            border-radius: 16px 16px 0 0;
            max-height: 60vh;
        }
    }
`;
document.head.appendChild(style);
