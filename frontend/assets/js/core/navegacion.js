// Navegación: qué módulo se carga al elegir una opción del menú.
// Los módulos se registran desde main.js, así este archivo no depende de ninguno.
import { closeMobileMenu } from './menu.js';

let secciones = {};
let porDefecto = null;
let antesDeCambiar = () => {};

export function configurarNavegacion(config) {
    secciones = config.secciones;
    porDefecto = config.porDefecto;
    antesDeCambiar = config.antesDeCambiar || antesDeCambiar;
}

export function loadSection(section) {
    antesDeCambiar();
    (secciones[section] || secciones[porDefecto])();
}

document.querySelectorAll('.sidebar .nav-link[data-section]').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.sidebar .nav-link').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        document.getElementById('sectionTitle').textContent = this.textContent.trim();
        loadSection(this.dataset.section);
        closeMobileMenu();
    });
});
