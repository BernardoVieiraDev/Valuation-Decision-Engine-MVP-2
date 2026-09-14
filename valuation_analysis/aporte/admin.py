from django.contrib import admin
from .models import Aporte, ItemAporte

class ItemAporteInline(admin.TabularInline):
    model = ItemAporte
    extra = 0
    readonly_fields = ('ticker', 'tipo_ativo', 'metodo_valuation', 'preco_teto_calculado', 'preco_atual_momento', 'valor_aportado')

@admin.register(Aporte)
class AporteAdmin(admin.ModelAdmin):
    list_display = ('id', 'carteira', 'valor_total', 'estrategia_utilizada', 'status', 'data_criacao')
    list_filter = ('status', 'estrategia_utilizada', 'data_criacao')
    inlines = [ItemAporteInline]