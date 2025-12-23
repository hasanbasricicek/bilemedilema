// Lazy Loading for Images and Content

// Intersection Observer for lazy loading images
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            const src = img.dataset.src;
            
            if (src) {
                // Create a new image to preload
                const tempImg = new Image();
                tempImg.onload = () => {
                    img.src = src;
                    img.classList.add('loaded');
                    img.classList.remove('lazy');
                };
                tempImg.src = src;
            }
            
            observer.unobserve(img);
        }
    });
}, {
    rootMargin: '50px 0px', // Start loading 50px before entering viewport
    threshold: 0.01
});

// Intersection Observer for lazy loading content
const contentObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const element = entry.target;
            element.classList.add('fade-in');
            observer.unobserve(element);
        }
    });
}, {
    rootMargin: '100px 0px',
    threshold: 0.1
});

// Initialize lazy loading
function initLazyLoading() {
    // Lazy load images
    const lazyImages = document.querySelectorAll('img[data-src]');
    lazyImages.forEach(img => {
        img.classList.add('lazy');
        imageObserver.observe(img);
    });
    
    // Lazy load content sections
    const lazyContent = document.querySelectorAll('[data-lazy-content]');
    lazyContent.forEach(element => {
        contentObserver.observe(element);
    });
}

// Infinite scroll for posts
let isLoadingMore = false;
let currentPage = 1;
let hasMorePosts = true;

function initInfiniteScroll() {
    const scrollContainer = document.querySelector('[data-infinite-scroll]');
    if (!scrollContainer) return;
    
    const loadMoreTrigger = document.createElement('div');
    loadMoreTrigger.className = 'load-more-trigger';
    loadMoreTrigger.style.height = '100px';
    scrollContainer.appendChild(loadMoreTrigger);
    
    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !isLoadingMore && hasMorePosts) {
                loadMorePosts();
            }
        });
    }, {
        rootMargin: '200px 0px'
    });
    
    scrollObserver.observe(loadMoreTrigger);
}

async function loadMorePosts() {
    if (isLoadingMore || !hasMorePosts) return;
    
    isLoadingMore = true;
    currentPage++;
    
    // Show loading indicator
    showLoadingIndicator();
    
    try {
        const url = new URL(window.location.href);
        url.searchParams.set('page', currentPage);
        
        const response = await fetch(url.toString(), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load posts');
        }
        
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        const newPosts = doc.querySelectorAll('[data-post-item]');
        
        if (newPosts.length === 0) {
            hasMorePosts = false;
            hideLoadingIndicator();
            return;
        }
        
        const container = document.querySelector('[data-infinite-scroll]');
        const loadMoreTrigger = container.querySelector('.load-more-trigger');
        
        newPosts.forEach(post => {
            container.insertBefore(post, loadMoreTrigger);
            
            // Reinitialize lazy loading for new images
            const images = post.querySelectorAll('img[data-src]');
            images.forEach(img => {
                img.classList.add('lazy');
                imageObserver.observe(img);
            });
        });
        
        hideLoadingIndicator();
        
    } catch (error) {
        console.error('Error loading more posts:', error);
        hideLoadingIndicator();
    } finally {
        isLoadingMore = false;
    }
}

function showLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.classList.remove('hidden');
    }
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.classList.add('hidden');
    }
}

// Debounce function for scroll events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Optimize scroll performance
let ticking = false;
function optimizeScroll(callback) {
    if (!ticking) {
        window.requestAnimationFrame(() => {
            callback();
            ticking = false;
        });
        ticking = true;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initLazyLoading();
    initInfiniteScroll();
});

// Reinitialize when new content is added dynamically
window.reinitLazyLoading = initLazyLoading;

// CSS for lazy loading animation
const style = document.createElement('style');
style.textContent = `
    img.lazy {
        opacity: 0;
        transition: opacity 0.3s ease-in-out;
    }
    
    img.loaded {
        opacity: 1;
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in-out;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .load-more-trigger {
        pointer-events: none;
    }
`;
document.head.appendChild(style);
