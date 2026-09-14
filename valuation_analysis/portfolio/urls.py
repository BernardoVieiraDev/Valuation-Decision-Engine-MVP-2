from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("configuracoes/", views.configuracoes, name="configuracoes"),
    path("atualizar-ativo/<int:ativo_id>/", views.atualizar_ativo_api, name="atualizar_ativo_api"),
    path("gerenciar-ativos/", views.gerenciar_ativos, name="gerenciar_ativos"),
    path("gerenciar-ativos/adicionar/", views.adicionar_ativo, name="adicionar_ativo"),
    path("gerenciar-ativos/remover/<int:ativo_id>/", views.remover_ativo, name="remover_ativo"),
]