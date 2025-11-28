from django.urls import path
from . import views

app_name = 'redeco_frontend'

urlpatterns = [
    path('', views.index, name='index'),
    path('catalogs/medios/', views.catalogs_medios, name='catalogs_medios'),
    path('catalogs/niveles-atencion/', views.catalogs_niveles_atencion, name='catalogs_niveles_atencion'),
    path('catalogs/estados/', views.catalogs_estados, name='catalogs_estados'),
    path('catalogs/codigos-postales/', views.catalogs_codigos_postales, name='catalogs_codigos_postales'),
    path('catalogs/municipios/', views.catalogs_municipios, name='catalogs_municipios'),
    path('catalogs/colonias/', views.catalogs_colonias, name='catalogs_colonias'),
    path('catalogs/productos/', views.catalogs_productos, name='catalogs_productos'),
    path('catalogs/causas/', views.catalogs_causas, name='catalogs_causas'),
    path('reune/consultas/', views.reune_consultas, name='reune_consultas'),
    path('reune/consultar-folios/', views.reune_consultar_folios, name='reune_consultar_folios'),
    path('reune/eliminar-folio/', views.reune_eliminar_folio, name='reune_eliminar_folio'),
    path('quejas/crear/', views.create_queja, name='create_queja'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # CRUD de Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/crear/', views.clientes_create, name='clientes_create'),
    path('clientes/<int:cliente_id>/editar/', views.clientes_edit, name='clientes_edit'),
    path('clientes/<int:cliente_id>/eliminar/', views.clientes_delete, name='clientes_delete'),
]
