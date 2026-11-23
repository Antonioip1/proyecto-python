// Tabla sencilla de tickets (la usa el dashboard para "Tickets recientes").
import { esc, PRIORIDAD_PILL } from '../../core/ui.js';

export function ticketsTable(tickets, conIA) {
    const cols = conIA ? 6 : 5;
    return `<div class="table-responsive"><table class="club-table">
        <thead><tr><th>ID</th><th>Título</th><th>Categoría</th><th>Prioridad</th><th>Estado</th>${conIA ? '<th>Confianza IA</th>' : ''}</tr></thead>
        <tbody>${tickets.map(t => `<tr>
            <td>#${t.id}</td>
            <td>${esc(t.titulo)}</td>
            <td><span class="pill">${esc(t.categoria_display)}</span></td>
            <td><span class="pill ${PRIORIDAD_PILL[t.prioridad] || ''}">${esc(t.prioridad_display)}</span></td>
            <td><span class="pill">${esc(t.estado_display)}</span></td>
            ${conIA ? `<td>${((t.confianza_clasificacion || 0) * 100).toFixed(0)}%</td>` : ''}
        </tr>`).join('') || `<tr><td colspan="${cols}" class="sin-datos">No hay tickets.</td></tr>`}</tbody>
    </table></div>`;
}
