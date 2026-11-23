// Dashboard: tarjetas KPI, indicadores de gestión, gráficos y tickets recientes.
import { API_URL } from '../../core/config.js';
import { getHeaders } from '../../core/sesion.js';
import { esc, pageHeading, metricCard, variationBadge, nf, formatHoras, panel } from '../../core/ui.js';
import { disposeCharts, renderCharts } from './graficos.js';
import { ticketsTable } from '../tickets/tabla-reciente.js';

let periodoDias = 30;

function chartPanel(title, sub, id, extraClass = '') {
    return `<div class="${extraClass}">${panel(title, sub, `<div class="panel-body"><div class="chart-box" id="${id}"></div></div>`)}</div>`;
}

export async function loadDashboard() {
    const container = document.getElementById('mainContent');
    disposeCharts();
    container.innerHTML = '<div class="main-inner text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2">Cargando...</p></div>';

    try {
        const [mRes, dRes, tRes] = await Promise.all([
            fetch(`${API_URL}/tickets/metricas/`, { headers: getHeaders() }),
            fetch(`${API_URL}/tickets/metricas/detalle/?dias=${periodoDias}`, { headers: getHeaders() }),
            fetch(`${API_URL}/tickets/`, { headers: getHeaders() })
        ]);
        if (!mRes.ok || !dRes.ok) throw new Error('No se pudieron cargar las métricas');
        const metrics = await mRes.json();
        const d = await dRes.json();
        const ticketsData = await tRes.json();
        const tickets = ticketsData.results || ticketsData || [];
        const dias = d.dias;
        const ia = d.ia;

        container.innerHTML = `<div class="main-inner">
            ${pageHeading('Visión general', 'Resultados del soporte técnico', 'Lectura ejecutiva de los tickets, su resolución y la satisfacción de los usuarios.')}
            <div class="toolbar">
                <label for="periodoDias">Período</label>
                <select id="periodoDias" class="form-select form-select-sm">
                    ${[7, 30, 90].map(n => `<option value="${n}" ${n === dias ? 'selected' : ''}>Últimos ${n} días</option>`).join('')}
                </select>
                <span class="toolbar-note">La variación se compara con los ${dias} días anteriores.</span>
            </div>

            <section aria-labelledby="kpi-vol">
                <h2 class="section-title" id="kpi-vol">Volumen y resultados</h2>
                <div class="metric-grid">
                    ${metricCard('Total tickets', metrics.total_tickets || 0, 'bi-ticket-perforated',
                        `${d.creados.valor} nuevos en los últimos ${dias} días.`, true, variationBadge(d.creados.variacion))}
                    ${metricCard('Abiertos', metrics.tickets_abiertos || 0, 'bi-hourglass-split', 'Tickets pendientes de resolver hoy.')}
                    ${metricCard('Resueltos', metrics.tickets_resueltos || 0, 'bi-check2-circle',
                        `${d.resueltos.valor} en el período` + (d.tasa_resolucion !== null ? ` · tasa de resolución ${nf.format(d.tasa_resolucion)}%.` : '.'),
                        false, variationBadge(d.resueltos.variacion))}
                    ${metricCard('Satisfacción', d.satisfaccion.valor === null ? '—' : nf.format(d.satisfaccion.valor), 'bi-star',
                        'Promedio de calificaciones (1 a 5) del período.', false, variationBadge(d.satisfaccion.variacion))}
                </div>
            </section>

            <section aria-labelledby="kpi-ges">
                <h2 class="section-title" id="kpi-ges">Indicadores de gestión</h2>
                <div class="metric-grid">
                    ${metricCard('Tiempo medio de resolución', formatHoras(d.horas_resolucion.valor), 'bi-stopwatch',
                        'Desde que se crea el ticket hasta que se resuelve.', false, variationBadge(d.horas_resolucion.variacion, true))}
                    ${metricCard('Sin asignar', d.sin_asignar, 'bi-person-exclamation',
                        'Tickets abiertos que aún no tienen técnico.', false, '', d.sin_asignar > 0)}
                    ${metricCard('Envejecidos', d.envejecidos, 'bi-hourglass-bottom',
                        `Sin resolver hace más de ${d.umbral_envejecido_dias} días.`, false, '', d.envejecidos > 0)}
                    ${metricCard('Precisión de la IA', ia.confianza_media === null ? '—' : `${nf.format(ia.confianza_media)}%`, 'bi-robot',
                        ia.baja_confianza_pct === null ? 'Sin tickets en el período.'
                            : `${ia.baja_confianza} tickets (${nf.format(ia.baja_confianza_pct)}%) bajo ${ia.umbral_pct}% de confianza: revisar a mano.`)}
                </div>
            </section>

            <section aria-labelledby="graf-tit">
                <h2 class="section-title" id="graf-tit">Tendencias</h2>
                <div class="chart-grid">
                    ${chartPanel('Creados vs. resueltos', `Tickets por día, últimos ${dias} días.`, 'chartSerie', 'span-2')}
                    ${chartPanel('Por prioridad', 'Todos los tickets.', 'chartPrioridad')}
                    ${chartPanel('Por categoría', 'Dónde se concentran los problemas.', 'chartCategoria', 'span-3')}
                </div>
            </section>

            <h2 class="section-title">Últimos tickets</h2>
            ${panel('Tickets recientes', 'Los 10 más nuevos.', ticketsTable(tickets.slice(0, 10), false))}
        </div>`;

        document.getElementById('periodoDias').addEventListener('change', function () {
            periodoDias = Number(this.value);
            loadDashboard();
        });
        renderCharts(d);
    } catch (e) {
        container.innerHTML = `<div class="main-inner"><div class="alert alert-danger">Error: ${esc(e.message)}</div></div>`;
    }
}
