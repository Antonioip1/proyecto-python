// Sesión: token guardado por login.html, cabeceras de la API, usuario en la barra superior y cierre de sesión.
let token = localStorage.getItem('access_token');
let userData = JSON.parse(localStorage.getItem('user_data') || '{}');

if (!token) {
    window.location.href = 'login.html';
}

export function getHeaders() {
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=UTF-8'
    };
}

document.getElementById('userName').textContent = `👤 ${userData.username || 'Usuario'}`;
document.getElementById('userRole').textContent = userData.role_display || userData.role || 'usuario';

document.getElementById('logoutBtn').addEventListener('click', function() {
    if (confirm('¿Cerrar sesión?')) {
        localStorage.clear();
        window.location.href = 'login.html';
    }
});
