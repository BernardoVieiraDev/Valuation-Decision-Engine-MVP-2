from django.urls import path
from . import views

urlpatterns = [
    path('salvar-simulacao/', views.salvar_simulacao, name='salvar_simulacao'),
    path('excluir/<int:aporte_id>/', views.excluir_aporte, name='excluir_aporte'),
    path('simulador/', views.simulador_aporte, name='simulador_aporte'),
    path('historico/', views.historico_aportes, name='historico_aportes'),
    path('status/<int:aporte_id>/', views.mudar_status_aporte, name='mudar_status_aporte'),
    path('editar-item/<int:item_id>/', views.editar_item_aporte, name='editar_item_aporte'),
]
