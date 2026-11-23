// Piezas de interfaz compartidas: escape de texto, encabezado de página, tarjeta KPI, panel y formatos.
export const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const PRIORIDAD_PILL = { critica: 'pill-rojo', alta: 'pill-ambar', media: 'pill-azul', baja: 'pill-verde' };

export function pageHeading(kicker, title, sub) {
    return `<header class="page-heading">
        <div class="page-kicker"><span aria-hidden="true"></span><p class="page-eyebrow">${kicker}</p></div>
        <h1>${title}</h1>
        <p class="page-sub">${sub}</p>
        <div class="page-axis" aria-hidden="true"><span></span><span></span><span></span></div>
    </header>`;
}

export function metricCard(label, value, icon, helper, accent, badge = '', alerta = false) {
    return `<article class="metric-card${accent ? ' accent' : ''}${alerta ? ' alerta' : ''}">
        <div class="metric-icon"><i class="bi ${icon}" aria-hidden="true"></i></div>
        <p class="metric-label">${label}</p>
        <div class="metric-row"><strong class="metric-value">${value}</strong>${badge}</div>
        <p class="metric-helper">${helper}</p>
    </article>`;
}

// Insignia de variación. inverso = true cuando bajar es bueno (p. ej. el tiempo de resolución).
export function variationBadge(variacion, inverso = false) {
    if (variacion === null || variacion === undefined) {
        return '<span class="metric-change neutro" title="Sin período comparable">Sin base</span>';
    }
    const n = Math.abs(variacion).toLocaleString('es-ES', { maximumFractionDigits: 1 });
    if (variacion === 0) return '<span class="metric-change neutro">— 0%</span>';
    const sube = variacion > 0;
    const bueno = sube !== inverso;
    return `<span class="metric-change ${bueno ? 'positivo' : 'negativo'}" title="${sube ? 'Subió' : 'Bajó'} ${n} % frente al período anterior">${sube ? '▲ +' : '▼ −'}${n}%</span>`;
}

export const nf = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 });
export function formatHoras(h) {
    if (h === null || h === undefined) return '—';
    if (h < 1) return `${Math.round(h * 60)} min`;
    if (h >= 48) return `${nf.format(h / 24)} d`;
    return `${nf.format(h)} h`;
}

export function panel(title, sub, inner) {
    return `<article class="panel">
        <div class="panel-header"><h2>${title}</h2>${sub ? `<p>${sub}</p>` : ''}</div>
        ${inner}
    </article>`;
}
