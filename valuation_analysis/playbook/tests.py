from django.test import Client, TestCase
from django.urls import reverse

from aporte.models import Aporte, ItemAporte
from portfolio.models import Carteira
from .models import DiarioPlaybook


class DiarioTests(TestCase):
    def setUp(self):
        self.aporte = Aporte.objects.create(carteira=Carteira.objects.create())
        self.item = ItemAporte.objects.create(aporte=self.aporte, ticker='TEST3', tipo_ativo='acao',
                                            metodo_valuation='graham', preco_teto_calculado=35.678)
        self.diario = DiarioPlaybook.objects.create(aporte=self.aporte, dados_json={
            'ativos': [{'id': 'antigo', 'tese': 'Preservar', 'conviccao': 80}], 'nota': 'Original'})

    def test_excluir_diario_remove_lista_mas_preserva_aporte_e_itens(self):
        response = self.client.post(reverse('excluir_playbook', args=[self.aporte.id]), follow=True)
        self.diario.refresh_from_db()
        self.assertTrue(self.diario.excluido)
        self.assertEqual(self.diario.dados_json, {})
        self.assertNotContains(response, reverse('playbook_index', args=[self.aporte.id]))
        self.assertTrue(Aporte.objects.filter(pk=self.aporte.pk).exists())
        self.assertTrue(ItemAporte.objects.filter(pk=self.item.pk).exists())
        history = self.client.get(reverse('historico_aportes'))
        self.assertContains(history, 'Recriar Playbook')

    def test_diario_pendente_tambem_pode_ser_excluido(self):
        self.diario.delete()
        self.client.post(reverse('excluir_playbook', args=[self.aporte.id]))
        self.assertTrue(DiarioPlaybook.objects.get(aporte=self.aporte).excluido)

    def test_recriar_importa_snapshot_e_retorna_a_lista(self):
        self.client.post(reverse('excluir_playbook', args=[self.aporte.id]))
        response = self.client.post(reverse('recriar_playbook', args=[self.aporte.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST3')
        self.diario.refresh_from_db()
        self.assertFalse(self.diario.excluido)
        listing = self.client.get(reverse('playbook_list'))
        self.assertContains(listing, reverse('playbook_index', args=[self.aporte.id]))

    def test_aba_antiga_nao_ressuscita_diario_excluido(self):
        self.client.post(reverse('excluir_playbook', args=[self.aporte.id]))
        response = self.client.post(reverse('playbook_salvar', args=[self.aporte.id]),
            {'ativos': [{'id': 'antigo', 'precoTeto': 10}]}, content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertRedirects(self.client.get(reverse('playbook_index', args=[self.aporte.id])),
                             reverse('historico_aportes'))

    def test_salvar_arredonda_teto_e_preserva_campos_antigos(self):
        response = self.client.post(reverse('playbook_salvar', args=[self.aporte.id]),
            {'nota': 'Nova', 'ativos': [{'id': 'antigo', 'precoTeto': '35,678'}]},
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.diario.refresh_from_db()
        ativo = self.diario.dados_json['ativos'][0]
        self.assertEqual(ativo['precoTeto'], '35.68')
        self.assertEqual(ativo['tese'], 'Preservar')
        self.assertEqual(ativo['conviccao'], 80)

    def test_teto_invalido_nao_sobrescreve_diario(self):
        for valor in ('NaN', 'Infinity', 'abc', '-1', ''):
            with self.subTest(valor=valor):
                response = self.client.post(reverse('playbook_salvar', args=[self.aporte.id]),
                    {'ativos': [{'precoTeto': valor}]}, content_type='application/json')
                self.assertEqual(response.status_code, 400)
        self.diario.refresh_from_db()
        self.assertEqual(self.diario.dados_json['nota'], 'Original')

    def test_excluir_e_recriar_exigem_post_e_csrf(self):
        for route in ('excluir_playbook', 'recriar_playbook'):
            url = reverse(route, args=[self.aporte.id])
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(Client(enforce_csrf_checks=True).post(url).status_code, 403)

    def test_formulario_nao_exige_campos_removidos(self):
        response = self.client.get(reverse('playbook_index', args=[self.aporte.id]))
        for field in ('tese', 'conviccao', 'falseability', 'premortem', 'alternativa'):
            self.assertNotContains(response, f'data-field="{field}"')
        self.assertContains(response, 'step="0.01"')
