/**
 * Premium Animations Controller
 * Handles page transitions, scroll animations, and micro-interactions
 */

(function() {
    'use strict';
    
    // Intersection Observer for scroll animations
    function initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        // Observe all premium cards
        document.querySelectorAll('.premium-card, .glass-card').forEach(card => {
            observer.observe(card);
        });
    }
    
    // Smooth scroll to top button
    function initScrollToTop() {
        const scrollBtn = document.createElement('button');
        scrollBtn.className = 'fixed bottom-6 right-6 w-12 h-12 rounded-full gradient-bg-primary text-white shadow-xl hover-lift opacity-0 transition-opacity duration-300 z-40';
        scrollBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
        scrollBtn.setAttribute('aria-label', 'Yukarı çık');
        scrollBtn.style.display = 'none';
        
        scrollBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
        
        document.body.appendChild(scrollBtn);
        
        // Show/hide on scroll
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            
            if (window.scrollY > 300) {
                scrollBtn.style.display = 'flex';
                scrollBtn.style.alignItems = 'center';
                scrollBtn.style.justifyContent = 'center';
                setTimeout(() => {
                    scrollBtn.style.opacity = '1';
                }, 10);
            } else {
                scrollBtn.style.opacity = '0';
                scrollTimeout = setTimeout(() => {
                    scrollBtn.style.display = 'none';
                }, 300);
            }
        });
    }
    
    // Add ripple effect to buttons
    function addRippleEffect() {
        document.addEventListener('click', (e) => {
            const target = e.target.closest('.btn-premium, .poll-option');
            if (!target) return;
            
            const ripple = document.createElement('span');
            const rect = target.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.5);
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
                transform: scale(0);
                animation: ripple 600ms ease-out;
            `;
            
            target.style.position = 'relative';
            target.style.overflow = 'hidden';
            target.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
        
        // Add ripple animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Smooth page transitions
    function initPageTransitions() {
        document.body.style.opacity = '0';
        
        window.addEventListener('load', () => {
            setTimeout(() => {
                document.body.style.transition = 'opacity 300ms ease-in';
                document.body.style.opacity = '1';
            }, 10);
        });
    }
    
    // Initialize all animations
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                initScrollAnimations();
                initScrollToTop();
                addRippleEffect();
                initPageTransitions();
            });
        } else {
            initScrollAnimations();
            initScrollToTop();
            addRippleEffect();
            initPageTransitions();
        }
    }
    
    init();
})();
