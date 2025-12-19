/* =================================
   DEVISA-FX - Main JavaScript
   Interactions et Animations
   ================================= */

document.addEventListener('DOMContentLoaded', function() {
    
    // === Animation au scroll ===
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observer les cartes et éléments
    document.querySelectorAll('.card, .feature-card, .quick-action-btn').forEach(el => {
        observer.observe(el);
    });
    
    // === Effet de particules sur le hero ===
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        createParticles(heroSection);
    }
    
    function createParticles(container) {
        const particlesCount = 20;
        
        for (let i = 0; i < particlesCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: ${Math.random() * 4 + 2}px;
                height: ${Math.random() * 4 + 2}px;
                background: ${Math.random() > 0.5 ? 'var(--bleu-ciel)' : 'var(--or)'};
                border-radius: 50%;
                opacity: ${Math.random() * 0.5 + 0.2};
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                animation: float ${Math.random() * 10 + 5}s linear infinite;
                box-shadow: 0 0 ${Math.random() * 20 + 10}px currentColor;
            `;
            container.appendChild(particle);
        }
    }
    
    // Ajouter le style d'animation des particules
    if (!document.querySelector('#particle-animation-style')) {
        const style = document.createElement('style');
        style.id = 'particle-animation-style';
        style.textContent = `
            @keyframes float {
                0% {
                    transform: translateY(0) translateX(0);
                }
                50% {
                    transform: translateY(-20px) translateX(10px);
                }
                100% {
                    transform: translateY(0) translateX(0);
                }
            }
            
            .particle {
                pointer-events: none;
                z-index: 0;
            }
        `;
        document.head.appendChild(style);
    }
    
    // === Animation des compteurs ===
    function animateCounter(element, target, duration = 2000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = formatNumber(target);
                clearInterval(timer);
            } else {
                element.textContent = formatNumber(Math.floor(current));
            }
        }, 16);
    }
    
    function formatNumber(num) {
        return num.toLocaleString('fr-FR');
    }
    
    // Animer les valeurs statistiques
    document.querySelectorAll('.stats-value').forEach(el => {
        const target = parseInt(el.textContent.replace(/[^0-9]/g, ''));
        if (!isNaN(target)) {
            const observerCounter = new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animateCounter(el, target);
                        observerCounter.unobserve(el);
                    }
                });
            });
            observerCounter.observe(el);
        }
    });
    
    // === Effet de brillance sur les badges ===
    document.querySelectorAll('.badge, .status-badge').forEach(badge => {
        badge.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
            this.style.transition = 'all 0.3s ease';
        });
        
        badge.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // === Effet de vague sur les boutons ===
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.5);
                top: ${y}px;
                left: ${x}px;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Ajouter le style de l'animation ripple
    if (!document.querySelector('#ripple-animation-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-animation-style';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // === Toast notifications améliorées ===
    window.showToast = function(message, type = 'info') {
        const colors = {
            success: { bg: '#00d4a1', shadow: '0 0 20px rgba(0, 212, 161, 0.5)' },
            error: { bg: '#ff4757', shadow: '0 0 20px rgba(255, 71, 87, 0.5)' },
            warning: { bg: '#ffd700', shadow: '0 0 20px rgba(255, 215, 0, 0.5)' },
            info: { bg: '#00d4ff', shadow: '0 0 20px rgba(0, 212, 255, 0.5)' }
        };
        
        const color = colors[type] || colors.info;
        
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--noir-card);
            color: var(--gris-clair);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            border-left: 4px solid ${color.bg};
            box-shadow: ${color.shadow}, var(--shadow-card);
            z-index: 9999;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
            backdrop-filter: blur(10px);
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };
    
    // Ajouter les styles d'animation des toasts
    if (!document.querySelector('#toast-animation-style')) {
        const style = document.createElement('style');
        style.id = 'toast-animation-style';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // === Amélioration des formulaires ===
    document.querySelectorAll('.form-control, .form-select').forEach(input => {
        // Animation au focus
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
            this.parentElement.style.transition = 'transform 0.3s ease';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
        
        // Validation visuelle
        input.addEventListener('input', function() {
            if (this.value.length > 0) {
                this.style.borderColor = 'var(--bleu-ciel)';
            }
        });
    });
    
    // === Effet parallaxe léger sur les cartes ===
    document.querySelectorAll('.card, .quick-action-btn').forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            
            this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
        });
    });
    
    // === Copier au clipboard avec feedback ===
    window.copyToClipboard = function(text, button) {
        navigator.clipboard.writeText(text).then(() => {
            const originalText = button.textContent;
            const originalBg = button.style.background;
            
            button.textContent = '✓ Copié!';
            button.style.background = 'var(--gradient-bleu-or)';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = originalBg;
            }, 2000);
            
            showToast('Copié dans le presse-papier!', 'success');
        }).catch(err => {
            showToast('Erreur lors de la copie', 'error');
        });
    };
    
    // === Smooth scroll pour les ancres ===
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // === Navbar transparence au scroll ===
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > 100) {
                navbar.style.background = 'rgba(10, 10, 10, 0.98)';
                navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.8)';
            } else {
                navbar.style.background = 'rgba(10, 10, 10, 0.95)';
                navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.5)';
            }
            
            lastScroll = currentScroll;
        });
    }
    
    // === Chargement progressif des images ===
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
    
    // === Animation de chargement ===
    window.showLoading = function() {
        const loader = document.createElement('div');
        loader.id = 'page-loader';
        loader.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(10, 10, 10, 0.95);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 99999;
                backdrop-filter: blur(5px);
            ">
                <div style="text-align: center;">
                    <div style="
                        width: 60px;
                        height: 60px;
                        border: 4px solid transparent;
                        border-top-color: var(--bleu-ciel);
                        border-right-color: var(--or);
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 1rem;
                    "></div>
                    <p style="color: var(--gris-clair); font-weight: 600;">Chargement...</p>
                </div>
            </div>
        `;
        document.body.appendChild(loader);
        
        // Ajouter l'animation de rotation
        if (!document.querySelector('#spin-animation-style')) {
            const style = document.createElement('style');
            style.id = 'spin-animation-style';
            style.textContent = `
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
    };
    
    window.hideLoading = function() {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.style.opacity = '0';
            loader.style.transition = 'opacity 0.3s ease';
            setTimeout(() => loader.remove(), 300);
        }
    };
    
    // === Log pour confirmer le chargement ===
    console.log('%c🚀 Devisa-FX Design System Loaded', 'color: #00d4ff; font-size: 16px; font-weight: bold;');
    console.log('%c✨ Premium UI Active', 'color: #ffd700; font-size: 14px;');
});

// === Utilitaires globaux ===
window.formatCurrency = function(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'decimal',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
};

window.formatDate = function(date) {
    return new Intl.DateTimeFormat('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
};
