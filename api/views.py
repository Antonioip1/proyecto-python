from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
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