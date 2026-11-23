// Punto de entrada del panel: sesión, menú, navegación y módulos.
import './core/sesion.js';
import './core/menu.js';
import { configurarNavegacion } from './core/navegacion.js';
import { loadDashboard } from './modulos/dashboard/index.js';
import { disposeCharts } from './modulos/dashboard/graficos.js';
import { loadTickets } from './modulos/tickets/lista.js';
import { loadNuevoTicket } from './modulos/tickets/crear.js';
import { loadActivos } from './modulos/activos/lista.js';

configurarNavegacion({
    secciones: {
        'dashboard': loadDashboard,
        'tickets': loadTickets,
        'nuevo-ticket': loadNuevoTicket,
        'activos': loadActivos
    },
    porDefecto: 'dashboard',
    antesDeCambiar: disposeCharts // libera los gráficos al salir del dashboard
});

loadDashboard();
