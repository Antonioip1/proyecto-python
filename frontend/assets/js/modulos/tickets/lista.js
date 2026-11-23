// Todos los tickets: búsqueda, orden por columna y paginación hechos en el servidor.
import { API_URL } from '../../core/config.js';
import { getHeaders } from '../../core/sesion.js';
import { esc, PRIORIDAD_PILL, pageHeading } from '../../core/ui.js';

const TICKET_SORTS = {
    id: ['id'],
    categoria: ['categoria'],
    prioridad: ['prioridad_orden'], // orden por gravedad (crítica primero), no alfabético
    estado: ['estado'],
    tecnico: ['tecnico_asignado__first_name', 'tecnico_asignado__last_name', 'tecnico_asignado__username'],
    fecha: ['fecha_creacion']
};
const TICKET_COLUMNS = [
    { key: 'id', label: 'ID', sort: true },
    { key: 'titulo', label: 'Título' },
    { key: 'categoria', label: 'Categoría', sort: true },
    { key: 'prioridad', label: 'Prioridad', sort: true },
    { key: 'estado', label: 'Estado', sort: true },
    { key: 'tecnico', label: 'Técnico', sort: true },
    { key: 'fecha', label: 'Fecha de creación', sort: true },
    { key: 'ia', label: 'Confianza IA' }
];
const PAGE_SIZES = [25, 50, 100];
const ticketsState = { page: 1, size: 25, search: '', sort: 'id', dir: 'desc', request: 0 };

try {
    const guardado = Number(localStorage.getItem('soporte_tickets_page_size'));
    if (PAGE_SIZES.includes(guardado)) ticketsState.size = guardado;
} catch (error) {
    // Sin almacenamiento: se usa 25.
}

const fechaHora = new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
const entero = new Intl.NumberFormat('es-ES');

function ticketOrdering() {
    const prefijo = ticketsState.dir === 'desc' ? '-' : '';
    return TICKET_SORTS[ticketsState.sort].map(campo => prefijo + campo).join(',');
}

function ticketsTableHtml(data) {
    const tickets = data.results || [];
    const total = data.count || 0;
    const paginas = Math.max(1, Math.ceil(total / ticketsState.size));
    const desde = total ? (ticketsState.page - 1) * ticketsState.size + 1 : 0;
    const hasta = Math.min(total, ticketsState.page * ticketsState.size);

    const cabecera = TICKET_COLUMNS.map(col => {
        if (!col.sort) return `<th scope="col">${col.label}</th>`;
        const activa = ticketsState.sort === col.key;
        const aria = activa ? (ticketsState.dir === 'asc' ? 'ascending' : 'descending') : 'none';
        const icono = activa ? (ticketsState.dir === 'asc' ? 'bi-sort-up' : 'bi-sort-down') : 'bi-arrow-down-up';
        return `<th scope="col" aria-sort="${aria}"><button type="button" class="sort-btn${activa ? ' activa' : ''}" data-sort="${col.key}">${col.label} <i class="bi ${icono}" aria-hidden="true"></i></button></th>`;
    }).join('');

    const filas = tickets.map(t => `<tr>
        <td>#${t.id}</td>
        <td>${esc(t.titulo)}</td>
        <td><span class="pill">${esc(t.categoria_display)}</span></td>
        <td><span class="pill ${PRIORIDAD_PILL[t.prioridad] || ''}">${esc(t.prioridad_display)}</span></td>
        <td><span class="pill">${esc(t.estado_display)}</span></td>
        <td>${t.tecnico_nombre ? esc(t.tecnico_nombre) : '<span class="texto-apagado">Sin asignar</span>'}</td>
        <td class="nowrap">${fechaHora.format(new Date(t.fecha_creacion))}</td>
        <td>${((t.confianza_clasificacion || 0) * 100).toFixed(0)}%</td>
    </tr>`).join('');

    const vacio = ticketsState.search
        ? `Sin resultados para «${esc(ticketsState.search)}».`
        : 'No hay tickets.';

    return `<div class="table-responsive"><table class="club-table club-table-wide">
            <caption class="visually-hidden">Listado de tickets</caption>
            <thead><tr>${cabecera}</tr></thead>
            <tbody>${filas || `<tr><td colspan="${TICKET_COLUMNS.length}" class="sin-datos">${vacio}</td></tr>`}</tbody>
        </table></div>
        <div class="table-footer">
            <p class="table-count">${total ? `Mostrando ${entero.format(desde)}–${entero.format(hasta)} de ${entero.format(total)} ${total === 1 ? 'ticket' : 'tickets'}` : '0 tickets'} · Página ${entero.format(ticketsState.page)} de ${entero.format(paginas)}</p>
            <nav class="pager" aria-label="Paginación de tickets">
                <button type="button" class="btn-club" data-page="${ticketsState.page - 1}" ${ticketsState.page <= 1 ? 'disabled' : ''}><i class="bi bi-chevron-left" aria-hidden="true"></i> Anterior</button>
                <button type="button" class="btn-club" data-page="${ticketsState.page + 1}" ${ticketsState.page >= paginas ? 'disabled' : ''}>Siguiente <i class="bi bi-chevron-right" aria-hidden="true"></i></button>
            </nav>
        </div>`;
}

async function fetchTickets() {
    const caja = document.getElementById('ticketsTable');
    if (!caja) return;
    const turno = ++ticketsState.request;
    caja.setAttribute('aria-busy', 'true');

    const pedir = page => {
        const params = new URLSearchParams({ page, page_size: ticketsState.size, ordering: ticketOrdering() });
        if (ticketsState.search) params.set('search', ticketsState.search);
        return fetch(`${API_URL}/tickets/?${params}`, { headers: getHeaders() });
    };

    try {
        let res = await pedir(ticketsState.page);
        // Si la página pedida ya no existe (por ejemplo tras borrar tickets), vuelve a la primera
        if (res.status === 404 && ticketsState.page > 1) {
            ticketsState.page = 1;
            res = await pedir(1);
        }
        if (!res.ok) throw new Error('No se pudieron cargar los tickets');
        const data = await res.json();
        if (turno !== ticketsState.request) return; // llegó una respuesta más nueva
        caja.innerHTML = ticketsTableHtml(data);
    } catch (e) {
        if (turno !== ticketsState.request) return;
        caja.innerHTML = `<div class="panel-body"><div class="alert alert-danger mb-0">${esc(e.message)}
            <button type="button" class="btn btn-sm btn-primary ms-2" id="reintentarTickets">Reintentar</button></div></div>`;
        document.getElementById('reintentarTickets').addEventListener('click', fetchTickets);
    } finally {
        if (turno === ticketsState.request) caja.setAttribute('aria-busy', 'false');
    }
}

export function loadTickets() {
    const container = document.getElementById('mainContent');
    ticketsState.page = 1;
    ticketsState.search = '';

    container.innerHTML = `<div class="main-inner">
        ${pageHeading('Gestión', 'Todos los tickets', 'Busca, ordena y recorre todos los tickets con su técnico asignado y fecha de creación.')}
        <article class="panel">
            <div class="panel-header with-tools">
                <div><h2>Tickets</h2><p>Haz clic en el título de una columna para ordenar.</p></div>
                <div class="table-tools">
                    <form id="ticketsBuscar" role="search" class="search-box" aria-label="Buscar tickets">
                        <i class="bi bi-search" aria-hidden="true"></i>
                        <input type="search" id="ticketsBuscarInput" class="form-control" maxlength="100" autocomplete="off"
                               placeholder="Buscar por ID, título, técnico…" aria-label="Buscar tickets">
                    </form>
                    <label class="size-select" for="ticketsSize">Mostrar
                        <select id="ticketsSize" class="form-select form-select-sm">
                            ${PAGE_SIZES.map(n => `<option value="${n}" ${n === ticketsState.size ? 'selected' : ''}>${n}</option>`).join('')}
                        </select>
                    </label>
                </div>
            </div>
            <div id="ticketsTable" class="tickets-table" aria-live="polite" aria-busy="true"></div>
        </article>
    </div>`;

    const buscador = document.getElementById('ticketsBuscarInput');
    let espera;
    const buscar = () => {
        const texto = buscador.value.trim();
        if (texto === ticketsState.search) return;
        ticketsState.search = texto;
        ticketsState.page = 1;
        fetchTickets();
    };
    buscador.addEventListener('input', () => { clearTimeout(espera); espera = setTimeout(buscar, 300); });
    document.getElementById('ticketsBuscar').addEventListener('submit', e => { e.preventDefault(); clearTimeout(espera); buscar(); });

    document.getElementById('ticketsSize').addEventListener('change', function () {
        ticketsState.size = Number(this.value);
        ticketsState.page = 1;
        try { localStorage.setItem('soporte_tickets_page_size', String(ticketsState.size)); } catch (error) { /* sin almacenamiento */ }
        fetchTickets();
    });

    document.getElementById('ticketsTable').addEventListener('click', function (e) {
        const orden = e.target.closest('[data-sort]');
        const pagina = e.target.closest('[data-page]');
        if (orden) {
            const clave = orden.dataset.sort;
            if (ticketsState.sort === clave) {
                ticketsState.dir = ticketsState.dir === 'asc' ? 'desc' : 'asc';
            } else {
                ticketsState.sort = clave;
                ticketsState.dir = 'asc';
            }
            ticketsState.page = 1;
            fetchTickets().then(() => document.querySelector(`#ticketsTable [data-sort="${clave}"]`)?.focus());
        } else if (pagina && !pagina.disabled) {
            ticketsState.page = Number(pagina.dataset.page);
            fetchTickets();
        }
    });

    fetchTickets();
}
