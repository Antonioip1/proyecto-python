// Gráficos del dashboard (ECharts, cargado desde el CDN como window.echarts).
const COLORES = { rojo: '#BE1E2D', noche: '#343B4D', gris: '#626975', linea: '#DEDAD5', tinta: '#161D29' };
let charts = [];
export function disposeCharts() {
    charts.forEach(c => { c.observer.disconnect(); c.chart.dispose(); });
    charts = [];
}
function makeChart(id, option) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!window.echarts) {
        el.innerHTML = '<p class="sin-datos">No se pudo cargar la librería de gráficos.</p>';
        return;
    }
    const chart = echarts.init(el, null, { renderer: 'canvas' });
    chart.setOption({
        textStyle: { fontFamily: "'DM Sans', sans-serif" },
        animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
        ...option
    });
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(el);
    charts.push({ chart, observer });
}

export function renderCharts(d) {
    const tooltip = { backgroundColor: '#fff', borderColor: COLORES.linea, textStyle: { color: COLORES.tinta, fontSize: 12 } };
    const fechas = d.serie_diaria.map(x => x.fecha.slice(5).split('-').reverse().join('/'));

    makeChart('chartSerie', {
        color: [COLORES.rojo, COLORES.noche],
        tooltip: { ...tooltip, trigger: 'axis' },
        legend: { bottom: 0, itemWidth: 14, itemHeight: 3, textStyle: { color: COLORES.gris } },
        grid: { top: 16, left: 8, right: 16, bottom: 34, containLabel: true },
        xAxis: { type: 'category', data: fechas, boundaryGap: false, axisLine: { lineStyle: { color: COLORES.linea } }, axisLabel: { color: COLORES.gris } },
        yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: COLORES.linea, type: 'dashed' } }, axisLabel: { color: COLORES.gris } },
        series: [
            { name: 'Creados', type: 'line', smooth: true, showSymbol: false, data: d.serie_diaria.map(x => x.creados),
              areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(190,30,45,.22)' }, { offset: 1, color: 'rgba(190,30,45,0)' }]) } },
            { name: 'Resueltos', type: 'line', smooth: true, showSymbol: false, data: d.serie_diaria.map(x => x.resueltos) }
        ]
    });

    const colorPrioridad = { critica: '#8F0E26', alta: '#D73246', media: '#343B4D', baja: '#B4B9C2' };
    makeChart('chartPrioridad', {
        tooltip: { ...tooltip, trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0, icon: 'circle', itemWidth: 8, textStyle: { color: COLORES.gris } },
        series: [{
            type: 'pie', radius: ['52%', '74%'], center: ['50%', '45%'], avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2 }, label: { show: false },
            data: d.por_prioridad.map(x => ({ name: x.nombre, value: x.total, itemStyle: { color: colorPrioridad[x.clave] || COLORES.gris } }))
        }]
    });

    const cats = d.por_categoria.slice().reverse();
    makeChart('chartCategoria', {
        color: [COLORES.rojo],
        tooltip: { ...tooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { top: 8, left: 8, right: 32, bottom: 4, containLabel: true },
        xAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: COLORES.linea, type: 'dashed' } }, axisLabel: { color: COLORES.gris } },
        yAxis: { type: 'category', data: cats.map(x => x.nombre), axisLine: { lineStyle: { color: COLORES.linea } }, axisTick: { show: false }, axisLabel: { color: COLORES.tinta } },
        series: [{ type: 'bar', barWidth: 14, data: cats.map(x => x.total), itemStyle: { borderRadius: [0, 6, 6, 0] }, label: { show: true, position: 'right', color: COLORES.gris } }]
    });
}
