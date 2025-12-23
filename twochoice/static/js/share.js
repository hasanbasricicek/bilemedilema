/**
 * Social Media Share Functionality
 */

// Share on Twitter
function shareOnTwitter(url, text) {
    const twitterUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
    window.open(twitterUrl, '_blank', 'width=550,height=420');
}

// Share on Facebook
function shareOnFacebook(url) {
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    window.open(facebookUrl, '_blank', 'width=550,height=420');
}

// Share on WhatsApp
function shareOnWhatsApp(url, text) {
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`;
    window.open(whatsappUrl, '_blank');
}

// Share on Telegram
function shareOnTelegram(url, text) {
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
    window.open(telegramUrl, '_blank');
}

// Share on LinkedIn
function shareOnLinkedIn(url) {
    const linkedinUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
    window.open(linkedinUrl, '_blank', 'width=550,height=420');
}

// Copy link to clipboard
async function copyLink(url, button) {
    try {
        await navigator.clipboard.writeText(url);
        
        // Show success feedback
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Kopyalandı!';
        button.classList.add('bg-green-500');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('bg-green-500');
        }, 2000);
        
        // Show toast
        if (typeof showToast === 'function') {
            showToast('Link kopyalandı!', 'success');
        }
    } catch (err) {
        console.error('Failed to copy:', err);
        if (typeof showToast === 'function') {
            showToast('Link kopyalanamadı', 'error');
        }
    }
}

// Native share API (mobile)
async function nativeShare(url, title, text) {
    if (navigator.share) {
        try {
            await navigator.share({
                title: title,
                text: text,
                url: url
            });
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Share failed:', err);
            }
        }
    } else {
        // Fallback to copy link
        copyLink(url);
    }
}

// Initialize share buttons
document.addEventListener('DOMContentLoaded', () => {
    // Twitter share buttons
    document.querySelectorAll('[data-share-twitter]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.dataset.shareUrl || window.location.href;
            const text = button.dataset.shareText || document.title;
            shareOnTwitter(url, text);
        });
    });
    
    // Facebook share buttons
    document.querySelectorAll('[data-share-facebook]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.dataset.shareUrl || window.location.href;
            shareOnFacebook(url);
        });
    });
    
    // WhatsApp share buttons
    document.querySelectorAll('[data-share-whatsapp]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.dataset.shareUrl || window.location.href;
            const text = button.dataset.shareText || document.title;
            shareOnWhatsApp(url, text);
        });
    });
    
    // Telegram share buttons
    document.querySelectorAll('[data-share-telegram]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.dataset.shareUrl || window.location.href;
            const text = button.dataset.shareText || document.title;
            shareOnTelegram(url, text);
        });
    });
    
    // LinkedIn share buttons
    document.querySelectorAll('[data-share-linkedin]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.dataset.shareUrl || window.location.href;
            shareOnLinkedIn(url);
        });
    });
    
    // Copy link buttons
    document.querySelectorAll('[data-share-copy]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.dataset.shareUrl || window.location.href;
            copyLink(url, button);
        });
    });
    
    // Native share buttons
    document.querySelectorAll('[data-share-native]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.dataset.shareUrl || window.location.href;
            const title = button.dataset.shareTitle || document.title;
            const text = button.dataset.shareText || '';
            nativeShare(url, title, text);
        });
    });
});
