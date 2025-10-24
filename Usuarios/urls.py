from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginAPIView, LogoutAPIView,
    PerfilUsuarioAPIView, CambioPasswordAPIView, RecuperarPasswordAPIView,
    ResetPasswordAPIView, ActivarUsuarioAPIView,
    UsuarioListCreateAPIView, UsuarioDetailAPIView, RegenerarTokenUsuarioAPIView,
    ActivarDesactivarUsuarioAPIView,
    ListarPermisosAPIView, RolesRBACListCreateAPIView, RolesRBACDetailAPIView,
    ClonarRolAPIView, AsignarRolUsuarioAPIView, RemoverRolUsuarioAPIView
)

urlpatterns = [
    path('api/auth/login', LoginAPIView.as_view(), name='login'),
    path('api/auth/logout', LogoutAPIView.as_view(), name='logout'),
    path('api/auth/actualizar_token', TokenRefreshView.as_view(), name='actualizarToken'),
    path('api/auth/perfil', PerfilUsuarioAPIView.as_view(), name='perfil'),
    path('api/auth/cambiar_password', CambioPasswordAPIView.as_view(), name='cambiarPassword'),
    path('api/auth/recuperar_password', RecuperarPasswordAPIView.as_view(), name='recuperarPassword'),
    path('api/auth/restablecer_password', ResetPasswordAPIView.as_view(), name='restablecerPassword'),
    path('api/auth/activar_cuenta', ActivarUsuarioAPIView.as_view(), name='activarCuenta'),
    path('api/usuarios', UsuarioListCreateAPIView.as_view(), name='listarCrearUsuarios'),
    path('api/usuarios/<int:pk>', UsuarioDetailAPIView.as_view(), name='detalleUsuario'),
    path('api/usuarios/<int:pk>/regenerar_token', RegenerarTokenUsuarioAPIView.as_view(), name='regenerarTokenUsuario'),
    path('api/usuarios/<int:pk>/activar_desactivar', ActivarDesactivarUsuarioAPIView.as_view(), name='activarDesactivarUsuario'),
    path('api/rbac/permisos', ListarPermisosAPIView.as_view(), name='listarPermisos'),
    path('api/rbac/roles', RolesRBACListCreateAPIView.as_view(), name='rolesRBAC'),
    path('api/rbac/roles/<int:pk>', RolesRBACDetailAPIView.as_view(), name='detalleRolRBAC'),
    path('api/rbac/roles/clonar', ClonarRolAPIView.as_view(), name='clonarRol'),
    path('api/rbac/usuarios/<int:pk>/asignar_rol', AsignarRolUsuarioAPIView.as_view(), name='asignarRol'),
    path('api/rbac/usuarios/<int:pk>/remover_rol', RemoverRolUsuarioAPIView.as_view(), name='removerRol'),
]
