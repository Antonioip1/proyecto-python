from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer, TicketSerializer, TicketCreateSerializer,
    ActivoSerializer, ComentarioSerializer, CategoriaActivoSerializer
)
from tickets.models import Ticket, ComentarioTicket
from assets.models import ActivoTecnologico, CategoriaActivo

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """API para gestión de usuarios"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'departamento']

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def perfil(self, request):
        """Perfil del usuario autenticado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def cambiar_password(self, request):
        """Cambia la contraseña del usuario"""
        user = request.user
        pass_actual = request.data.get('password_actual')
        pass_nueva = request.data.get('password_nueva')
        pass_confirm = request.data.get('password_confirmacion')

        if not all([pass_actual, pass_nueva, pass_confirm]):
            return Response(
                {'error': 'Todos los campos son obligatorios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(pass_actual):
            return Response(
                {'error': 'La contraseña actual es incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if pass_nueva != pass_confirm:
            return Response(
                {'error': 'Las contraseñas nuevas no coinciden'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(pass_nueva) < 6:
            return Response(
                {'error': 'La contraseña debe tener al menos 6 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if pass_actual == pass_nueva:
            return Response(
                {'error': 'La nueva contraseña debe ser diferente a la actual'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(pass_nueva)
        user.debe_cambiar_password = False
        user.save()

        return Response({
            'mensaje': 'Contraseña actualizada exitosamente',
            'requiere_reauth': True
        })


class TicketViewSet(viewsets.ModelViewSet):
    """API para gestión de tickets"""
    queryset = Ticket.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'prioridad', 'categoria']
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'prioridad']
    ordering = ['-fecha_creacion']

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        return TicketSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'admin':
            return queryset
        elif self.request.user.role == 'tecnico':
            return queryset.filter(
                Q(tecnico_asignado=self.request.user) | Q(estado='abierto')
            )
        return queryset.filter(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def asignar_tecnico(self, request, pk=None):
        ticket = self.get_object()
        if request.user.role not in ['admin', 'tecnico']:
            return Response(
                {'error': 'Sin permisos para asignar'},
                status=status.HTTP_403_FORBIDDEN
            )

        tecnico_id = request.data.get('tecnico_id')
        if not tecnico_id:
            return Response(
                {'error': 'Se requiere tecnico_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tecnico = User.objects.get(id=tecnico_id, role='tecnico')
            ticket.tecnico_asignado = tecnico
            ticket.estado = 'asignado'
            ticket.fecha_asignacion = timezone.now()
            ticket.save()
            return Response(TicketSerializer(ticket).data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Técnico no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        ticket = self.get_object()
        if ticket.estado in ['resuelto', 'cerrado']:
            return Response(
                {'error': f'El ticket ya está {ticket.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.estado = 'resuelto'
        ticket.fecha_resolucion = timezone.now()
        if ticket.fecha_creacion:
            delta = ticket.fecha_resolucion - ticket.fecha_creacion
            ticket.tiempo_respuesta_minutos = int(delta.total_seconds() / 60)
        ticket.save()
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    def calificar(self, request, pk=None):
        ticket = self.get_object()
        if request.user != ticket.usuario:
            return Response(
                {'error': 'Solo el creador puede calificar'},
                status=status.HTTP_403_FORBIDDEN
            )

        puntuacion = request.data.get('puntuacion')
        if not puntuacion or int(puntuacion) not in range(1, 6):
            return Response(
                {'error': 'Puntuación entre 1 y 5'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.satisfaccion_usuario = int(puntuacion)
        ticket.save()
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['get', 'post'])
    def comentarios(self, request, pk=None):
        ticket = self.get_object()
        if request.method == 'GET':
            comentarios = ticket.comentarios.all()
            if request.user.role not in ['admin', 'tecnico']:
                comentarios = comentarios.filter(es_interno=False)
            serializer = ComentarioSerializer(comentarios, many=True)
            return Response(serializer.data)

        texto = request.data.get('texto')
        if not texto:
            return Response(
                {'error': 'El comentario no puede estar vacío'},
                status=status.HTTP_400_BAD_REQUEST
            )

        es_interno = request.data.get('es_interno', False)
        if es_interno and request.user.role not in ['admin', 'tecnico']:
            return Response(
                {'error': 'Sin permisos para comentarios internos'},
                status=status.HTTP_403_FORBIDDEN
            )

        comentario = ComentarioTicket.objects.create(
            ticket=ticket, usuario=request.user, texto=texto, es_interno=es_interno
        )
        return Response(ComentarioSerializer(comentario).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def metricas(self, request):
        tickets_por_estado = Ticket.objects.values('estado').annotate(count=Count('id'))
        tickets_por_prioridad = Ticket.objects.values('prioridad').annotate(count=Count('id'))

        tickets_resueltos = Ticket.objects.filter(tiempo_respuesta_minutos__isnull=False)
        tiempo_promedio = tickets_resueltos.aggregate(
            avg=Avg('tiempo_respuesta_minutos')
        )['avg'] or 0

        satisfaccion = Ticket.objects.filter(
            satisfaccion_usuario__isnull=False
        ).aggregate(avg=Avg('satisfaccion_usuario'))['avg'] or 0

        return Response({
            'tickets_por_estado': list(tickets_por_estado),
            'tickets_por_prioridad': list(tickets_por_prioridad),
            'tiempo_promedio_resolucion_minutos': int(tiempo_promedio),
            'satisfaccion_promedio': round(float(satisfaccion), 2),
            'total_tickets': Ticket.objects.count(),
            'tickets_abiertos': Ticket.objects.filter(estado='abierto').count(),
            'tickets_resueltos': Ticket.objects.filter(estado='resuelto').count(),
        })

    @action(detail=False, methods=['get'], url_path='metricas/detalle')
    def metricas_detalle(self, request):
        """KPIs de gestión, variación contra el período anterior y series para los gráficos.

        ?dias=N (7, 30 o 90; por defecto 30). Igual que `metricas`, cuenta todos los tickets.
        """
        try:
            dias = int(request.query_params.get('dias', 30))
        except (TypeError, ValueError):
            dias = 30
        if dias not in (7, 30, 90):
            dias = 30

        ahora = timezone.now()
        inicio = ahora - timedelta(days=dias)
        inicio_prev = inicio - timedelta(days=dias)
        ABIERTOS = ['abierto', 'asignado', 'en_progreso']
        UMBRAL_ENVEJECIDO_DIAS = 7
        UMBRAL_CONFIANZA = 0.6

        def variacion(actual, previo):
            """% de cambio; None si no hay base (previo vacío o cero)."""
            if previo in (None, 0) or actual is None:
                return None
            return round((actual - previo) / previo * 100, 1)

        def horas_resolucion(desde, hasta):
            pares = Ticket.objects.filter(
                fecha_resolucion__gte=desde, fecha_resolucion__lt=hasta
            ).values_list('fecha_creacion', 'fecha_resolucion')
            horas = [(r - c).total_seconds() / 3600 for c, r in pares if c and r]
            return round(sum(horas) / len(horas), 1) if horas else None

        def periodo(desde, hasta):
            creados = Ticket.objects.filter(fecha_creacion__gte=desde, fecha_creacion__lt=hasta)
            sat = creados.filter(satisfaccion_usuario__isnull=False).aggregate(
                avg=Avg('satisfaccion_usuario'))['avg']
            conf = creados.aggregate(avg=Avg('confianza_clasificacion'))['avg']
            return {
                'creados': creados.count(),
                'resueltos': Ticket.objects.filter(
                    fecha_resolucion__gte=desde, fecha_resolucion__lt=hasta
                ).count(),
                'horas_resolucion': horas_resolucion(desde, hasta),
                'satisfaccion': round(float(sat), 2) if sat is not None else None,
                'confianza': round(float(conf) * 100, 1) if conf is not None else None,
            }

        actual = periodo(inicio, ahora)
        previo = periodo(inicio_prev, inicio)

        abiertos = Ticket.objects.filter(estado__in=ABIERTOS)
        en_periodo = Ticket.objects.filter(fecha_creacion__gte=inicio)
        total_periodo = en_periodo.count()
        baja_confianza = en_periodo.filter(confianza_clasificacion__lt=UMBRAL_CONFIANZA).count()

        # Serie diaria: creados vs resueltos
        creados_dia = {
            f['d']: f['n'] for f in en_periodo.annotate(d=TruncDate('fecha_creacion'))
            .values('d').annotate(n=Count('id'))
        }
        resueltos_dia = {
            f['d']: f['n'] for f in Ticket.objects.filter(fecha_resolucion__gte=inicio)
            .annotate(d=TruncDate('fecha_resolucion')).values('d').annotate(n=Count('id'))
        }
        hoy = timezone.localdate()
        serie = []
        for i in range(dias - 1, -1, -1):
            dia = hoy - timedelta(days=i)
            serie.append({
                'fecha': dia.isoformat(),
                'creados': creados_dia.get(dia, 0),
                'resueltos': resueltos_dia.get(dia, 0),
            })

        etiquetas_prioridad = dict(Ticket.PRIORIDADES)
        etiquetas_categoria = dict(Ticket.CATEGORIAS)
        por_prioridad = [
            {'clave': f['prioridad'], 'nombre': etiquetas_prioridad.get(f['prioridad'], f['prioridad']), 'total': f['n']}
            for f in Ticket.objects.values('prioridad').annotate(n=Count('id'))
        ]
        por_categoria = sorted(
            [
                {'clave': f['categoria'], 'nombre': etiquetas_categoria.get(f['categoria'], f['categoria']), 'total': f['n']}
                for f in Ticket.objects.values('categoria').annotate(n=Count('id'))
            ],
            key=lambda x: x['total'], reverse=True,
        )

        return Response({
            'dias': dias,
            'creados': {'valor': actual['creados'], 'variacion': variacion(actual['creados'], previo['creados'])},
            'resueltos': {'valor': actual['resueltos'], 'variacion': variacion(actual['resueltos'], previo['resueltos'])},
            'satisfaccion': {'valor': actual['satisfaccion'], 'variacion': variacion(actual['satisfaccion'], previo['satisfaccion'])},
            'horas_resolucion': {
                'valor': actual['horas_resolucion'],
                'variacion': variacion(actual['horas_resolucion'], previo['horas_resolucion']),
            },
            'tasa_resolucion': round(actual['resueltos'] / actual['creados'] * 100, 1) if actual['creados'] else None,
            'sin_asignar': abiertos.filter(tecnico_asignado__isnull=True).count(),
            'envejecidos': abiertos.filter(
                fecha_creacion__lt=ahora - timedelta(days=UMBRAL_ENVEJECIDO_DIAS)
            ).count(),
            'umbral_envejecido_dias': UMBRAL_ENVEJECIDO_DIAS,
            'ia': {
                'confianza_media': actual['confianza'],
                'baja_confianza': baja_confianza,
                'baja_confianza_pct': round(baja_confianza / total_periodo * 100, 1) if total_periodo else None,
                'umbral_pct': int(UMBRAL_CONFIANZA * 100),
            },
            'serie_diaria': serie,
            'por_prioridad': por_prioridad,
            'por_categoria': por_categoria,
        })


class ActivoViewSet(viewsets.ModelViewSet):
    """API para gestión de activos"""
    queryset = ActivoTecnologico.objects.all()
    serializer_class = ActivoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['estado', 'categoria']
    search_fields = ['nombre', 'codigo_inventario', 'modelo', 'serie']

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        return Response({
            'total': ActivoTecnologico.objects.count(),
            'por_estado': list(
                ActivoTecnologico.objects.values('estado').annotate(count=Count('id'))
            ),
        })


class CategoriaActivoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaActivo.objects.all()
    serializer_class = CategoriaActivoSerializer
    permission_classes = [permissions.IsAuthenticated]