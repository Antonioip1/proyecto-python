import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from assets.models import ActivoTecnologico, CategoriaActivo
from tickets.models import Ticket

User = get_user_model()

# Marcas que identifican lo creado por este comando (así --limpiar no toca datos reales)
PREFIJO_USUARIO = 'demo_'
PREFIJO_TICKET = '[PRUEBA] '
PREFIJO_ACTIVO = 'DEMO-'

TECNICOS = [
    ('demo_tec1', 'Carlos', 'Mendoza'),
    ('demo_tec2', 'Ana', 'Rodríguez'),
    ('demo_tec3', 'Luis', 'Pérez'),
    ('demo_tec4', 'María', 'González'),
    ('demo_tec5', 'José', 'Ramírez'),
]
SOLICITANTES = [
    ('demo_usr1', 'Laura', 'Sánchez', 'Contabilidad'),
    ('demo_usr2', 'Pedro', 'Díaz', 'Recursos Humanos'),
    ('demo_usr3', 'Rosa', 'Torres', 'Administración'),
    ('demo_usr4', 'Miguel', 'Herrera', 'Ventas'),
]

TITULOS = {
    'hardware': ['El equipo no enciende', 'Pantalla con rayas verticales', 'Teclado con teclas que no responden', 'Ruido fuerte en el ventilador', 'Mouse sin respuesta'],
    'software': ['Excel se congela al abrir archivos', 'Error al instalar actualización', 'La aplicación se cierra sola', 'Necesito licencia de Office', 'Programa muy lento'],
    'red': ['Sin conexión a internet', 'WiFi se cae constantemente', 'No accedo a la carpeta compartida', 'Cable de red dañado', 'Router sin señal'],
    'correo': ['No puedo enviar correos', 'Bandeja de entrada llena', 'Correo no recibe adjuntos', 'Olvidé la contraseña del correo', 'Mucho spam en la cuenta'],
    'sistema': ['Windows no arranca', 'Pantalla azul al iniciar', 'Controlador de video desactualizado', 'Actualización de Windows falló', 'El equipo tarda en iniciar'],
    'periferico': ['La impresora no imprime', 'Escáner no detectado', 'Proyector sin imagen', 'Micrófono no funciona en videollamadas', 'USB no reconocido'],
    'otro': ['Solicitud de equipo nuevo', 'Consulta sobre accesos', 'Revisión general del puesto de trabajo'],
}

# (valor, peso)
PRIORIDADES = [('critica', 8), ('alta', 22), ('media', 45), ('baja', 25)]
CATEGORIAS = [('hardware', 22), ('software', 24), ('red', 18), ('correo', 12), ('sistema', 8), ('periferico', 12), ('otro', 4)]
SATISFACCION = [(1, 5), (2, 8), (3, 17), (4, 35), (5, 35)]


def elegir(opciones, rng):
    valores, pesos = zip(*opciones)
    return rng.choices(valores, weights=pesos, k=1)[0]


class Command(BaseCommand):
    help = (
        'Crea datos de prueba (técnicos, tickets de los últimos 90 días y activos) '
        'para ver el dashboard con información. Todo queda marcado para poder borrarlo con --limpiar.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=120, help='Tickets a crear (por defecto 120)')
        parser.add_argument('--dias', type=int, default=90, help='Rango de días hacia atrás desde hoy (por defecto 90)')
        parser.add_argument('--password', default='123456', help='Contraseña de los usuarios de prueba')
        parser.add_argument('--limpiar', action='store_true', help='Borra antes los datos de prueba creados por este comando')
        parser.add_argument('--solo-limpiar', action='store_true', help='Solo borra los datos de prueba y termina')
        parser.add_argument('--semilla', type=int, default=None, help='Semilla para repetir exactamente los mismos datos')

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts['limpiar'] or opts['solo_limpiar']:
            self.limpiar()
            if opts['solo_limpiar']:
                return

        rng = random.Random(opts['semilla'])
        ahora = timezone.now()
        dias = max(1, opts['dias'])

        tecnicos = [self.usuario(u, n, a, 'tecnico', 'Soporte técnico', opts['password']) for u, n, a in
                    [(t[0], t[1], t[2]) for t in TECNICOS]]
        solicitantes = [self.usuario(u, n, a, 'usuario', d, opts['password']) for u, n, a, d in SOLICITANTES]
        activos = self.crear_activos(rng, ahora)
        creados = self.crear_tickets(rng, ahora, dias, opts['cantidad'], tecnicos, solicitantes, activos)

        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(tecnicos)} técnicos, {len(solicitantes)} solicitantes, {len(activos)} activos y {creados} tickets '
            f'creados (últimos {dias} días, contados desde hoy).'
        ))
        self.stdout.write(
            f'     Usuarios de prueba: demo_tec1..demo_tec{len(tecnicos)} y demo_usr1..demo_usr{len(solicitantes)} '
            f'(clave: {opts["password"]})\n'
            f'     Para borrarlos: python manage.py crear_datos_prueba --solo-limpiar'
        )

    def limpiar(self):
        t, _ = Ticket.objects.filter(titulo__startswith=PREFIJO_TICKET).delete()
        a, _ = ActivoTecnologico.objects.filter(codigo_inventario__startswith=PREFIJO_ACTIVO).delete()
        u, _ = User.objects.filter(username__startswith=PREFIJO_USUARIO).delete()
        self.stdout.write(self.style.WARNING(f'[OK] Datos de prueba anteriores borrados ({t} tickets/relacionados, {a} activos, {u} usuarios).'))

    def usuario(self, username, nombre, apellido, rol, departamento, password):
        user, creado = User.objects.get_or_create(username=username, defaults={
            'first_name': nombre, 'last_name': apellido, 'role': rol,
            'departamento': departamento, 'email': f'{username}@prueba.local',
        })
        if creado:
            user.set_password(password)
            user.save()
        return user

    def crear_activos(self, rng, ahora):
        hoy = ahora.date()
        categorias = {n: CategoriaActivo.objects.get_or_create(nombre=n)[0] for n in ('Computadoras', 'Impresoras', 'Redes')}
        estados = [('operativo', 60), ('mantenimiento', 14), ('reparacion', 12), ('obsoleto', 9), ('baja', 5)]
        modelos = {'Computadoras': ['Dell OptiPlex 7090', 'HP ProDesk 400', 'Lenovo ThinkCentre M70'],
                   'Impresoras': ['HP LaserJet Pro M404', 'Epson L3250'],
                   'Redes': ['TP-Link Archer C6', 'Cisco SG350']}
        activos = []
        for i in range(1, 13):
            cat = rng.choice(list(categorias))
            adquirido = hoy - timedelta(days=rng.randint(60, 1800))
            activo, _ = ActivoTecnologico.objects.get_or_create(
                codigo_inventario=f'{PREFIJO_ACTIVO}{i:03d}',
                defaults={
                    'nombre': f'{cat[:-1] if cat.endswith("s") else cat} {i:02d}',
                    'categoria': categorias[cat],
                    'modelo': rng.choice(modelos[cat]),
                    'serie': f'SN{rng.randint(100000, 999999)}',
                    'estado': elegir(estados, rng),
                    'ubicacion': rng.choice(['Oficina 1', 'Oficina 2', 'Sala de reuniones', 'Almacén']),
                    'fecha_adquisicion': adquirido,
                    'fecha_ultimo_mantenimiento': hoy - timedelta(days=rng.randint(10, 500)) if rng.random() < 0.8 else None,
                    'garantia_hasta': adquirido + timedelta(days=365 * rng.choice([1, 2, 3])),
                },
            )
            activos.append(activo)
        return activos

    def crear_tickets(self, rng, ahora, dias, cantidad, tecnicos, solicitantes, activos):
        total = 0
        for _ in range(cantidad):
            # Un poco más de tickets recientes que antiguos
            edad = timedelta(days=dias * (rng.random() ** 1.1), hours=rng.uniform(0, 8))
            if edad.days >= dias:
                edad = timedelta(days=dias - 1, hours=rng.uniform(0, 23))
            creado = ahora - edad
            categoria = elegir(CATEGORIAS, rng)
            prioridad = elegir(PRIORIDADES, rng)

            # Los tickets viejos casi siempre ya están resueltos; unos pocos siguen abiertos (los "envejecidos")
            if edad.days > 14:
                estado = elegir([('resuelto', 40), ('cerrado', 40), ('rechazado', 8), ('en_progreso', 7), ('abierto', 5)], rng)
            else:
                estado = elegir([('resuelto', 28), ('cerrado', 22), ('abierto', 20), ('asignado', 12), ('en_progreso', 13), ('rechazado', 5)], rng)

            tecnico = None if estado in ('abierto', 'rechazado') and rng.random() < 0.9 else rng.choice(tecnicos)
            if estado in ('asignado', 'en_progreso', 'resuelto', 'cerrado'):
                tecnico = tecnico or rng.choice(tecnicos)

            fecha_asignacion = fecha_resolucion = minutos = satisfaccion = None
            if tecnico:
                fecha_asignacion = min(ahora, creado + timedelta(minutes=rng.randint(5, 240)))
            if estado in ('resuelto', 'cerrado'):
                horas = min(rng.expovariate(1 / 14) + 0.5, 120)  # media ~14 h, con cola larga
                fecha_resolucion = min(ahora, creado + timedelta(hours=horas))
                minutos = int((fecha_resolucion - creado).total_seconds() / 60)
                if rng.random() < 0.7:
                    satisfaccion = elegir(SATISFACCION, rng)

            ticket = Ticket.objects.create(
                titulo=PREFIJO_TICKET + rng.choice(TITULOS[categoria]),
                descripcion='Ticket generado automáticamente para pruebas del dashboard.',
                categoria=categoria,
                prioridad=prioridad,
                estado=estado,
                usuario=rng.choice(solicitantes),
                tecnico_asignado=tecnico,
                activo_relacionado=rng.choice(activos) if categoria in ('hardware', 'periferico') and rng.random() < 0.6 else None,
                clasificacion_automatica=categoria,
                confianza_clasificacion=round(rng.uniform(0.4, 0.98), 2),
                tiempo_respuesta_minutos=minutos,
                satisfaccion_usuario=satisfaccion,
            )
            # fecha_creacion es auto_now_add: se corrige con update() para simular el pasado
            Ticket.objects.filter(pk=ticket.pk).update(
                fecha_creacion=creado, fecha_asignacion=fecha_asignacion, fecha_resolucion=fecha_resolucion,
            )
            total += 1
        return total
