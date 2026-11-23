from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UserViewSet, basename='user')
router.register(r'tickets', views.TicketViewSet, basename='ticket')
router.register(r'activos', views.ActivoViewSet, basename='activo')
router.register(r'categorias', views.CategoriaActivoViewSet, basename='categoria')

urlpatterns = [
    path('', include(router.urls)),
]