// Activos tecnológicos: listado de equipos.
import { API_URL } from '../../core/config.js';
import { getHeaders } from '../../core/sesion.js';
import { esc, pageHeading, panel } from '../../core/ui.js';

export async function loadActivos() {
    const container = document.getElementById('mainContent');
    try {
        const res = await fetch(`${API_URL}/activos/`, { headers: getHeaders() });
        const data = await res.json();
        const activos = data.results || data || [];

        container.innerHTML = `<div class="main-inner">
            ${pageHeading('Inventario', 'Activos tecnológicos', 'Equipos registrados y su estado actual.')}
            ${panel('Activos', `${activos.length} en total`, `<div class="table-responsive"><table class="club-table">
                <thead><tr><th>Código</th><th>Nombre</th><th>Modelo</th><th>Estado</th></tr></thead>
                <tbody>${activos.map(a => `<tr>
                    <td>${esc(a.codigo_inventario)}</td><td>${esc(a.nombre)}</td><td>${esc(a.modelo)}</td>
                    <td><span class="pill">${esc(a.estado_display)}</span></td>
                </tr>`).join('') || '<tr><td colspan="4" class="sin-datos">No hay activos.</td></tr>'}</tbody>
            </table></div>`)}
        </div>`;
    } catch (e) {
        container.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
    }
}
