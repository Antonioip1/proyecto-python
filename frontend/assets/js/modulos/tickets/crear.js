// Formulario para crear un ticket (el servidor lo clasifica con IA).
import { API_URL } from '../../core/config.js';
import { getHeaders } from '../../core/sesion.js';
import { pageHeading, panel } from '../../core/ui.js';
import { loadTickets } from './lista.js';

export async function loadNuevoTicket() {
    const container = document.getElementById('mainContent');
    container.innerHTML = `<div class="main-inner">
        ${pageHeading('Gestión', 'Crear nuevo ticket', 'Describe el problema y el sistema lo clasificará automáticamente.')}
        ${panel('Datos del ticket', '', `<div class="panel-body"><form id="formTicket">
            <div class="mb-3">
                <label class="form-label">Título *</label>
                <input type="text" class="form-control" id="titulo" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Descripción *</label>
                <textarea class="form-control" id="descripcion" rows="4" required></textarea>
            </div>
            <div class="alert alert-info"><i class="bi bi-robot"></i> El sistema clasificará automáticamente tu ticket con IA.</div>
            <button type="submit" class="btn btn-primary">Enviar ticket</button>
        </form></div>`)}
    </div>`;

    document.getElementById('formTicket').addEventListener('submit', async function(e) {
        e.preventDefault();
        const titulo = document.getElementById('titulo').value;
        const descripcion = document.getElementById('descripcion').value;

        try {
            const res = await fetch(`${API_URL}/tickets/`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({ titulo, descripcion })
            });

            if (res.ok) {
                alert('✅ Ticket creado exitosamente');
                loadTickets();
            } else {
                const err = await res.json();
                alert('❌ Error: ' + JSON.stringify(err));
            }
        } catch (e) {
            alert('Error: ' + e.message);
        }
    });
}
