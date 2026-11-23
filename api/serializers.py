from rest_framework import serializers
from django.contrib.auth import get_user_model
from tickets.models import Ticket, ComentarioTicket
from tickets.triaje import procesar_ticket_con_ia
from assets.models import ActivoTecnologico, CategoriaActivo

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'telefono', 'departamento',
            'debe_cambiar_password'
        ]
        read_only_fields = ['id']


class CategoriaActivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaActivo
        fields = ['id', 'nombre', 'descripcion']


class ActivoSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    usuario_asignado_nombre = serializers.CharField(
        source='usuario_asignado.username', read_only=True, default=None
    )
    esta_en_garantia = serializers.BooleanField(read_only=True)

    class Meta:
        model = ActivoTecnologico
        fields = '__all__'
        read_only_fields = ['id', 'fecha_registro']


class TicketSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    tecnico_nombre = serializers.CharField(
        source='tecnico_asignado.username', read_only=True, default=None
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = [
            'id', 'fecha_creacion', 'clasificacion_automatica',
            'confianza_clasificacion', 'tiempo_respuesta_minutos'
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear tickets con triaje automático"""

    class Meta:
        model = Ticket
        fields = ['titulo', 'descripcion', 'activo_relacionado']

    def create(self, validated_data):
        resultado = procesar_ticket_con_ia(
            validated_data['titulo'],
            validated_data['descripcion']
        )

        return Ticket.objects.create(
            titulo=validated_data['titulo'],
            descripcion=validated_data['descripcion'],
            activo_relacionado=validated_data.get('activo_relacionado'),
            categoria=resultado['categoria'],
            prioridad=resultado['prioridad'],
            clasificacion_automatica=resultado['categoria'],
            confianza_clasificacion=resultado['confianza'],
            usuario=self.context['request'].user
        )


class ComentarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = ComentarioTicket
        fields = ['id', 'ticket', 'usuario', 'usuario_nombre', 'texto', 'fecha', 'es_interno']
        read_only_fields = ['id', 'fecha', 'usuario']