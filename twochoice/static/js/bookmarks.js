/**
 * Bookmark functionality
 */

// Get CSRF token from cookie
function getCookie(name) {
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

async function toggleBookmark(postId, button) {
    const url = `/post/${postId}/bookmark/`;
    const csrfToken = getCookie('csrftoken');
    
    // Disable button during request
    button.disabled = true;
    const originalHTML = button.innerHTML;
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update button state
            if (data.bookmarked) {
                button.innerHTML = '<i class="fas fa-bookmark"></i> Favorilerde';
                button.classList.remove('bg-gray-600', 'hover:bg-gray-700');
                button.classList.add('bg-yellow-500', 'hover:bg-yellow-600');
            } else {
                button.innerHTML = '<i class="far fa-bookmark"></i> Favorilere Ekle';
                button.classList.remove('bg-yellow-500', 'hover:bg-yellow-600');
                button.classList.add('bg-gray-600', 'hover:bg-gray-700');
            }
            
            // Show toast
            if (typeof showToast === 'function') {
                showToast(data.message, 'success');
            }
        } else {
            throw new Error(data.error || 'Bir hata oluştu');
        }
    } catch (error) {
        console.error('Bookmark error:', error);
        if (typeof showToast === 'function') {
            showToast('Bir hata oluştu', 'error');
        }
        button.innerHTML = originalHTML;
    } finally {
        button.disabled = false;
    }
}

// Initialize bookmark buttons
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-bookmark-toggle]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const postId = button.dataset.postId;
            toggleBookmark(postId, button);
        });
    });
});
