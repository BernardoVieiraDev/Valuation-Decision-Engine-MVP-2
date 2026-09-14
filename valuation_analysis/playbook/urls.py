from django.urls import path
from . import views

urlpatterns = [
    path('<int:aporte_id>/analisar/', views.analisar_playbook, name='playbook_analisar'),
    path('<int:aporte_id>/excluir/', views.excluir_playbook, name='excluir_playbook'),
    path('<int:aporte_id>/recriar/', views.recriar_playbook, name='recriar_playbook'),
    path('', views.playbook_list, name='playbook_list'),
    path('<int:aporte_id>/', views.preencher_playbook, name='playbook_index'),
    path('<int:aporte_id>/salvar/', views.salvar_playbook, name='playbook_salvar'),
]
