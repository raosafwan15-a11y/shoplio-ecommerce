// 3D Effects and Animations for SHOPLIO

document.addEventListener('DOMContentLoaded', function() {
    // Parallax effect for hero section
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * 0.5;
            hero.style.transform = `translateY(${rate}px)`;
        });
    }

    // 3D tilt effect for product cards (disabled to prevent click interference)
    // Note: CSS hover effects handle the 3D transforms instead
    // This prevents JavaScript from interfering with click events

    // Floating animation for category icons
    const categoryIcons = document.querySelectorAll('.category-icon');
    categoryIcons.forEach((icon, index) => {
        icon.style.animation = `float 3s ease-in-out infinite`;
        icon.style.animationDelay = `${index * 0.2}s`;
    });

    // Add CSS for float animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0%, 100% {
                transform: translateY(0px);
            }
            50% {
                transform: translateY(-10px);
            }
        }
    `;
    document.head.appendChild(style);

    // Image loading with fade-in effect
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        if (img.complete) {
            img.style.opacity = '1';
        } else {
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.5s';
            img.addEventListener('load', function() {
                img.style.opacity = '1';
            });
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

