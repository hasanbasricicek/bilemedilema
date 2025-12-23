/**
 * Advanced Theme Switcher with Multiple Themes
 */

const THEMES = {
    light: {
        name: 'Açık Tema',
        icon: '☀️',
        colors: {
            bg: '#FFFFFF',
            text: '#111827',
            primary: '#8B5CF6',
            secondary: '#F3F4F6',
            border: '#E5E7EB'
        }
    },
    dark: {
        name: 'Koyu Tema',
        icon: '🌙',
        colors: {
            bg: '#1F2937',
            text: '#F9FAFB',
            primary: '#A78BFA',
            secondary: '#374151',
            border: '#4B5563'
        }
    },
    midnight: {
        name: 'Gece Yarısı',
        icon: '🌃',
        colors: {
            bg: '#0F172A',
            text: '#F1F5F9',
            primary: '#818CF8',
            secondary: '#1E293B',
            border: '#334155'
        }
    },
    ocean: {
        name: 'Okyanus',
        icon: '🌊',
        colors: {
            bg: '#0C4A6E',
            text: '#F0F9FF',
            primary: '#38BDF8',
            secondary: '#075985',
            border: '#0369A1'
        }
    },
    forest: {
        name: 'Orman',
        icon: '🌲',
        colors: {
            bg: '#14532D',
            text: '#F0FDF4',
            primary: '#4ADE80',
            secondary: '#166534',
            border: '#15803D'
        }
    }
};

class ThemeSwitcher {
    constructor() {
        this.currentTheme = this.loadTheme();
        this.autoSwitch = this.loadAutoSwitch();
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        this.createThemeMenu();
        this.attachEventListeners();
        
        if (this.autoSwitch) {
            this.startAutoSwitch();
        }
    }
    
    loadTheme() {
        return localStorage.getItem('bilemedilema-theme') || 'light';
    }
    
    loadAutoSwitch() {
        return localStorage.getItem('bilemedilema-auto-switch') === 'true';
    }
    
    saveTheme(theme) {
        localStorage.setItem('bilemedilema-theme', theme);
    }
    
    saveAutoSwitch(enabled) {
        localStorage.setItem('bilemedilema-auto-switch', enabled);
    }
    
    applyTheme(theme) {
        this.currentTheme = theme;
        const colors = THEMES[theme].colors;
        
        // Apply CSS variables
        document.documentElement.style.setProperty('--theme-bg', colors.bg);
        document.documentElement.style.setProperty('--theme-text', colors.text);
        document.documentElement.style.setProperty('--theme-primary', colors.primary);
        document.documentElement.style.setProperty('--theme-secondary', colors.secondary);
        document.documentElement.style.setProperty('--theme-border', colors.border);
        
        // Set data-theme attribute
        document.body.setAttribute('data-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
        
        // Add/remove dark class for compatibility
        if (theme !== 'light') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        
        this.saveTheme(theme);
        this.updateThemeButton();
    }
    
    createThemeMenu() {
        const menu = document.createElement('div');
        menu.id = 'theme-menu';
        menu.className = 'hidden';
        menu.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 1rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            padding: 1rem;
            z-index: 1000;
            min-width: 250px;
        `;
        
        const title = document.createElement('h3');
        title.textContent = 'Tema Seç';
        title.style.cssText = 'font-weight: 700; margin-bottom: 1rem; font-size: 1rem;';
        menu.appendChild(title);
        
        Object.entries(THEMES).forEach(([key, theme]) => {
            const btn = document.createElement('button');
            btn.className = 'theme-option';
            btn.dataset.theme = key;
            btn.style.cssText = `
                width: 100%;
                padding: 0.75rem;
                margin-bottom: 0.5rem;
                border: 2px solid ${key === this.currentTheme ? '#8B5CF6' : '#E5E7EB'};
                border-radius: 0.5rem;
                background: ${key === this.currentTheme ? 'rgba(139, 92, 246, 0.1)' : 'white'};
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                transition: all 0.2s;
            `;
            
            btn.innerHTML = `
                <span style="font-size: 1.5rem;">${theme.icon}</span>
                <span style="font-weight: 600;">${theme.name}</span>
            `;
            
            btn.addEventListener('click', () => {
                this.applyTheme(key);
                this.updateThemeOptions();
            });
            
            menu.appendChild(btn);
        });
        
        const divider = document.createElement('div');
        divider.style.cssText = 'height: 1px; background: #E5E7EB; margin: 1rem 0;';
        menu.appendChild(divider);
        
        const autoSwitch = document.createElement('label');
        autoSwitch.style.cssText = 'display: flex; align-items: center; gap: 0.5rem; cursor: pointer;';
        autoSwitch.innerHTML = `
            <input type="checkbox" id="auto-switch" ${this.autoSwitch ? 'checked' : ''} style="cursor: pointer;">
            <span style="font-size: 0.875rem;">Otomatik geçiş (gece/gündüz)</span>
        `;
        menu.appendChild(autoSwitch);
        
        document.body.appendChild(menu);
    }
    
    updateThemeOptions() {
        document.querySelectorAll('.theme-option').forEach(btn => {
            const theme = btn.dataset.theme;
            const isActive = theme === this.currentTheme;
            btn.style.border = `2px solid ${isActive ? '#8B5CF6' : '#E5E7EB'}`;
            btn.style.background = isActive ? 'rgba(139, 92, 246, 0.1)' : 'white';
        });
    }
    
    updateThemeButton() {
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            const theme = THEMES[this.currentTheme];
            btn.innerHTML = `${theme.icon} <span class="hidden sm:inline">${theme.name}</span>`;
        }
    }
    
    attachEventListeners() {
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleMenu();
            });
        }
        
        document.addEventListener('click', (e) => {
            const menu = document.getElementById('theme-menu');
            if (menu && !menu.contains(e.target) && e.target.id !== 'theme-toggle') {
                menu.classList.add('hidden');
            }
        });
        
        const autoSwitchCheckbox = document.getElementById('auto-switch');
        if (autoSwitchCheckbox) {
            autoSwitchCheckbox.addEventListener('change', (e) => {
                this.autoSwitch = e.target.checked;
                this.saveAutoSwitch(this.autoSwitch);
                
                if (this.autoSwitch) {
                    this.startAutoSwitch();
                } else {
                    this.stopAutoSwitch();
                }
            });
        }
    }
    
    toggleMenu() {
        const menu = document.getElementById('theme-menu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
    }
    
    startAutoSwitch() {
        this.checkTimeAndSwitch();
        this.autoSwitchInterval = setInterval(() => {
            this.checkTimeAndSwitch();
        }, 60000); // Check every minute
    }
    
    stopAutoSwitch() {
        if (this.autoSwitchInterval) {
            clearInterval(this.autoSwitchInterval);
        }
    }
    
    checkTimeAndSwitch() {
        const hour = new Date().getHours();
        
        // 6 AM - 6 PM: Light theme
        // 6 PM - 6 AM: Dark theme
        if (hour >= 6 && hour < 18) {
            if (this.currentTheme !== 'light') {
                this.applyTheme('light');
            }
        } else {
            if (this.currentTheme === 'light') {
                this.applyTheme('dark');
            }
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new ThemeSwitcher();
});
