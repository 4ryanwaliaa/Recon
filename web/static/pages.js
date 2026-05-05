/* ══════════════════════════════════════════════════════════════
   RECON OSINT — Pages JavaScript
   Reading progress bar, navbar scroll, counter animation,
   mobile toggle, smooth scroll
   ══════════════════════════════════════════════════════════════ */

// ── Navbar Scroll Effect ────────────────────────────────────
(function() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(function() {
                navbar.classList.toggle('scrolled', window.scrollY > 20);
                ticking = false;
            });
            ticking = true;
        }
    });
})();

// ── Mobile Nav Toggle ───────────────────────────────────────
(function() {
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    const cta = document.querySelector('.nav-cta');
    if (!toggle || !links) return;
    toggle.addEventListener('click', function() {
        links.classList.toggle('open');
        if (cta) cta.classList.toggle('open');
        // Animate hamburger
        const spans = toggle.querySelectorAll('span');
        const isOpen = links.classList.contains('open');
        if (isOpen) {
            spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
            spans[1].style.opacity = '0';
            spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
        } else {
            spans[0].style.transform = '';
            spans[1].style.opacity = '';
            spans[2].style.transform = '';
        }
    });
    // Close on link click
    links.querySelectorAll('.nav-link').forEach(function(link) {
        link.addEventListener('click', function() {
            links.classList.remove('open');
            if (cta) cta.classList.remove('open');
            const spans = toggle.querySelectorAll('span');
            spans[0].style.transform = '';
            spans[1].style.opacity = '';
            spans[2].style.transform = '';
        });
    });
})();

// ── Reading Progress Bar ────────────────────────────────────
(function() {
    const bar = document.getElementById('readingProgress');
    if (!bar) return;
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(function() {
                const docHeight = document.documentElement.scrollHeight - window.innerHeight;
                const scrolled = (window.scrollY / docHeight) * 100;
                bar.style.width = Math.min(scrolled, 100) + '%';
                ticking = false;
            });
            ticking = true;
        }
    });
})();

// ── Counter Animation (Home Page Stats) ─────────────────────
(function() {
    const counters = document.querySelectorAll('[data-count]');
    if (counters.length === 0) return;

    function animateCounter(el) {
        const target = parseInt(el.getAttribute('data-count'), 10);
        const suffix = el.getAttribute('data-suffix') || '';
        const duration = 2000;
        const start = performance.now();

        function update(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(eased * target);
            el.textContent = current + suffix;
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = target + suffix;
            }
        }
        requestAnimationFrame(update);
    }

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(function(el) { observer.observe(el); });
})();

// ── Smooth Scroll for Anchor Links ──────────────────────────
document.addEventListener('click', function(e) {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    const target = document.querySelector(link.getAttribute('href'));
    if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});

// ── Fade-in Animation on Scroll ─────────────────────────────
(function() {
    const elements = document.querySelectorAll('.glass-card, .feature-card, .blog-card, .guide-card, .step-card, .about-card, .whatnext-card');
    if (elements.length === 0) return;

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    elements.forEach(function(el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
})();
