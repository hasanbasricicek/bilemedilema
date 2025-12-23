/**
 * Kayıtsız kullanıcı oy verdikten sonra kayıt CTA'sı göster
 */

// Oy verme sonrası CTA modal'ı göster
document.addEventListener('DOMContentLoaded', function() {
    // Poll voting event'ini dinle
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            // Vote poll endpoint'ini kontrol et
            if (args[0] && args[0].includes('/vote/')) {
                response.clone().json().then(data => {
                    if (data.success && data.show_register_cta) {
                        // Kısa bir gecikme ile CTA göster
                        setTimeout(() => {
                            showRegisterCTA();
                        }, 1500);
                    }
                }).catch(() => {});
            }
            return response;
        });
    };
});

function showRegisterCTA() {
    // Zaten gösterilmişse tekrar gösterme
    if (document.getElementById('register-cta-modal')) return;
    
    const modal = document.createElement('div');
    modal.id = 'register-cta-modal';
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fade-in';
    
    modal.innerHTML = `
        <div class="bg-white rounded-2xl max-w-md w-full p-8 relative animate-scale-in">
            <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600" onclick="this.closest('#register-cta-modal').remove()">
                <i class="fas fa-times text-xl"></i>
            </button>
            
            <div class="text-center mb-6">
                <div class="w-20 h-20 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-check text-white text-3xl"></i>
                </div>
                <h3 class="text-2xl font-bold text-gray-900 mb-2">Oyun Kaydedildi! 🎉</h3>
                <p class="text-gray-600">Sonuçları görmek ister misin?</p>
            </div>
            
            <div class="space-y-3 mb-4">
                <a href="/register/" class="block w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl font-semibold text-center transition duration-200">
                    <i class="fas fa-user-plus mr-2"></i>
                    Ücretsiz Kayıt Ol
                </a>
                
                <a href="/login/" class="block w-full py-3 px-6 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-xl font-semibold text-center transition duration-200">
                    Zaten Hesabım Var
                </a>
            </div>
            
            <div class="text-center">
                <button onclick="this.closest('#register-cta-modal').remove()" class="text-sm text-gray-500 hover:text-gray-700">
                    Şimdi değil, sonuçları göster
                </button>
            </div>
            
            <div class="mt-6 pt-6 border-t border-gray-200">
                <p class="text-xs text-gray-500 text-center">
                    ✨ Kayıt olarak tüm anketlere oy verebilir, yorum yapabilir ve kendi anketlerini oluşturabilirsin!
                </p>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Modal dışına tıklayınca kapat
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// CSS animasyonları
const style = document.createElement('style');
style.textContent = `
    @keyframes fade-in {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes scale-in {
        from { 
            opacity: 0;
            transform: scale(0.9);
        }
        to { 
            opacity: 1;
            transform: scale(1);
        }
    }
    
    .animate-fade-in {
        animation: fade-in 0.3s ease-out;
    }
    
    .animate-scale-in {
        animation: scale-in 0.3s ease-out;
    }
`;
document.head.appendChild(style);
