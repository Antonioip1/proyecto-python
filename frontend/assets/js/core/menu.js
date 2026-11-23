// Menú lateral: abierto/cerrado en móvil, compacto en escritorio (corte a 960px), foco y teclado.
const appLayout = document.getElementById('appLayout');
const sidebar = document.getElementById('sidebar');
const appMain = document.getElementById('appMain');
const menuToggle = document.getElementById('menuToggle');
const menuClose = document.getElementById('menuClose');
const menuBackdrop = document.getElementById('menuBackdrop');
const desktopMenu = window.matchMedia('(min-width: 960px)');
const sidebarPreferenceKey = 'soporte_sidebar_collapsed';
let sidebarCollapsed = false;
let mobileMenuOpen = false;

try {
    sidebarCollapsed = localStorage.getItem(sidebarPreferenceKey) === 'true';
} catch (error) {
    // El menú también funciona si el navegador bloquea guardar preferencias.
}

function renderMenu() {
    const mobileOpen = !desktopMenu.matches && mobileMenuOpen;
    const expanded = desktopMenu.matches ? !sidebarCollapsed : mobileOpen;
    const label = desktopMenu.matches
        ? (expanded ? 'Contraer menú' : 'Expandir menú')
        : (expanded ? 'Cerrar menú' : 'Abrir menú');

    appLayout.classList.toggle('sidebar-collapsed', desktopMenu.matches && sidebarCollapsed);
    appLayout.classList.toggle('menu-open', mobileOpen);
    document.body.classList.toggle('menu-open', mobileOpen);
    sidebar.inert = !desktopMenu.matches && !mobileOpen;
    sidebar.setAttribute('aria-hidden', String(sidebar.inert));
    appMain.inert = mobileOpen;
    menuBackdrop.hidden = !mobileOpen;
    menuToggle.setAttribute('aria-expanded', String(expanded));
    menuToggle.setAttribute('aria-label', label);
    menuToggle.title = label;

    if (mobileOpen) {
        sidebar.setAttribute('role', 'dialog');
        sidebar.setAttribute('aria-modal', 'true');
        sidebar.setAttribute('aria-labelledby', 'sidebarTitle');
    } else {
        sidebar.removeAttribute('role');
        sidebar.removeAttribute('aria-modal');
        sidebar.removeAttribute('aria-labelledby');
    }
}

export function closeMobileMenu() {
    if (!mobileMenuOpen) return;
    mobileMenuOpen = false;
    renderMenu();
    menuToggle.focus();
}

menuToggle.addEventListener('click', function() {
    if (desktopMenu.matches) {
        sidebarCollapsed = !sidebarCollapsed;
        try {
            localStorage.setItem(sidebarPreferenceKey, String(sidebarCollapsed));
        } catch (error) {
            // Se conserva el estado en esta página aunque no pueda guardarse.
        }
        renderMenu();
    } else if (mobileMenuOpen) {
        closeMobileMenu();
    } else {
        mobileMenuOpen = true;
        renderMenu();
        menuClose.focus();
    }
});

menuClose.addEventListener('click', closeMobileMenu);
menuBackdrop.addEventListener('click', closeMobileMenu);
sidebar.querySelectorAll('a[href]:not([href="#"])').forEach(link => {
    link.addEventListener('click', closeMobileMenu);
});

document.addEventListener('keydown', function(event) {
    if (!mobileMenuOpen || desktopMenu.matches) return;
    if (event.key === 'Escape') {
        event.preventDefault();
        closeMobileMenu();
    } else if (event.key === 'Tab') {
        const controls = Array.from(sidebar.querySelectorAll('a[href], button:not([disabled])'))
            .filter(control => control.getClientRects().length > 0);
        const first = controls[0];
        const last = controls[controls.length - 1];
        const outside = !sidebar.contains(document.activeElement);
        if (event.shiftKey && (document.activeElement === first || outside)) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && (document.activeElement === last || outside)) {
            event.preventDefault();
            first.focus();
        }
    }
});

desktopMenu.addEventListener('change', function() {
    const focusedInSidebar = sidebar.contains(document.activeElement);
    const focusedOnClose = document.activeElement === menuClose;
    const wasMobileOpen = mobileMenuOpen;
    mobileMenuOpen = false;
    renderMenu();
    if (wasMobileOpen || (focusedInSidebar && (!desktopMenu.matches || focusedOnClose))) menuToggle.focus();
});

renderMenu();
