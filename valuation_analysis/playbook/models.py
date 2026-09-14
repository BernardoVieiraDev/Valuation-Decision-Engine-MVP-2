from django.db import models
from aporte.models import Aporte

class DiarioPlaybook(models.Model):
    excluido = models.BooleanField(default=False)
    aporte = models.OneToOneField(Aporte, on_delete=models.CASCADE, related_name='diario_playbook')
    dados_json = models.JSONField(default=dict, help_text="Guarda todo o state.ativos do frontend")
    data_registro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Playbook do Aporte #{self.aporte.id}"
