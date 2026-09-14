from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from portfolio.models import Acao, AtivoNaCarteira, Carteira
from playbook.models import DiarioPlaybook
from .models import Aporte, ItemAporte


class FluxosAporteTests(TestCase):
    def setUp(self):
        self.carteira = Carteira.objects.create(banda_mais=60)
        self.acao = Acao.objects.create(ticket='TEST3', nome='Teste', preco_atual=10)
        self.posicao = AtivoNaCarteira.objects.create(
            carteira=self.carteira, acao=self.acao, quantidade=10, preco_teto=20)
        outra = Acao.objects.create(ticket='OUTR3', nome='Outra', preco_atual=90)
        AtivoNaCarteira.objects.create(carteira=self.carteira, acao=outra, quantidade=10, preco_teto=50)

    def test_raiz_abre_tela_unificada_com_filtros(self):
        response = self.client.get('/', follow=True)
        self.assertRedirects(response, reverse('simulador_aporte'))
        for field in ('tipos_permitidos', 'limite_ativos', 'ativos_excluidos'):
            self.assertContains(response, f'name="{field}"')
        self.assertContains(response, '> Aporte')
        navigation = response.content.decode().split('<nav class="sidebar-nav">')[1].split('</nav>')[0]
        self.assertNotIn('Simulador', navigation)

    @patch('aporte.views.PlaybookAPIClient')
    def test_atualizar_cotacoes_na_tela_unificada(self, client_class):
        client_class.return_value.get_price.return_value = 12
        response = self.client.post(reverse('simulador_aporte'), {'atualizar_precos': ''})
        self.assertRedirects(response, reverse('simulador_aporte'))
        self.acao.refresh_from_db()
        self.assertEqual(self.acao.preco_atual, 12)
        self.assertFalse(Aporte.objects.exists())

    @patch('aporte.views.PlaybookAPIClient')
    def test_calcular_tetos_na_tela_unificada(self, client_class):
        client_class.return_value.get_graham_price.return_value = 25
        self.client.post(reverse('simulador_aporte'), {'calcular_tetos': ''})
        self.posicao.refresh_from_db()
        self.assertEqual(self.posicao.preco_teto, 25)
        self.assertFalse(Aporte.objects.exists())

    def test_simulacao_so_salva_snapshot_apos_confirmacao(self):
        response = self.client.post(reverse('simulador_aporte'), {
            'calcular_aporte': '', 'valor': '100', 'estrategia': 'concentrado',
            'tipos_permitidos': ['acao'], 'limite_ativos': '1', 'ativos_excluidos': ['OUTR3'],
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Aporte.objects.exists())
        self.assertContains(response, 'Resumo da simulação')
        token = response.context['resumo']['token']
        # A confirmação deve salvar o que foi revisado, mesmo com nova cotação.
        self.acao.preco_atual = 18
        self.acao.save()
        self.client.post(reverse('salvar_simulacao'), {'simulacao_token': token, 'valor_total': '9999'})
        aporte = Aporte.objects.get()
        self.assertEqual(aporte.status, 'em_analise')
        self.assertEqual(aporte.ativos.get().ticker, 'TEST3')
        self.assertEqual(aporte.ativos.get().valor_aportado, 100)
        self.assertEqual(aporte.ativos.get().preco_atual_momento, 10)
        self.assertEqual(aporte.valor_total, 100)

    def simular(self, **extra):
        data = {'calcular_aporte': '', 'valor': '100', 'estrategia': 'dividido', 'tipos_permitidos': ['acao']}
        data.update(extra)
        return self.client.post(reverse('simulador_aporte'), data)

    def test_fechar_sem_confirmar_nao_cria_historico(self):
        self.simular()
        self.client.get(reverse('simulador_aporte'))
        self.assertFalse(Aporte.objects.exists())
        self.assertFalse(ItemAporte.objects.exists())

    def test_confirmacao_repetida_nao_duplica_aporte(self):
        token = self.simular().context['resumo']['token']
        for _ in range(2):
            self.client.post(reverse('salvar_simulacao'), {'simulacao_token': token})
        self.assertEqual(Aporte.objects.count(), 1)
        self.assertEqual(ItemAporte.objects.count(), 1)

    def test_token_invalido_ou_outra_sessao_nao_salva(self):
        token = self.simular().context['resumo']['token']
        self.client.post(reverse('salvar_simulacao'), {'simulacao_token': 'inventado'})
        Client().post(reverse('salvar_simulacao'), {'simulacao_token': token})
        self.assertFalse(Aporte.objects.exists())

    def test_sem_elegiveis_nao_oferece_salvamento(self):
        response = self.simular(ativos_excluidos=['TEST3', 'OUTR3'])
        self.assertContains(response, 'Nenhum ativo atende')
        self.assertNotContains(response, 'id="confirmar-aporte"')
        self.client.post(reverse('salvar_simulacao'), {'simulacao_token': response.context['resumo']['token']})
        self.assertFalse(Aporte.objects.exists())

    def test_simulacao_expirada_nao_salva(self):
        token = self.simular().context['resumo']['token']
        session = self.client.session
        drafts = session['simulacoes_aporte']
        drafts[token]['criado_em'] = 0
        session['simulacoes_aporte'] = drafts
        session.save()
        self.client.post(reverse('salvar_simulacao'), {'simulacao_token': token})
        self.assertFalse(Aporte.objects.exists())

    def test_valores_invalidos_e_salvamento_sem_csrf(self):
        for value in ('NaN', 'Infinity', '-10', '0'):
            response = self.simular(valor=value)
            self.assertIsNone(response.context['resumo'])
        self.assertFalse(Aporte.objects.exists())
        url = reverse('salvar_simulacao')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(url).status_code, 403)

    def test_exclusao_aporte_em_todos_os_status_preserva_carteira(self):
        for status in ('em_analise', 'cancelado', 'efetuado'):
            with self.subTest(status=status):
                aporte = Aporte.objects.create(carteira=self.carteira, status=status)
                ItemAporte.objects.create(aporte=aporte, ticker='TEST3')
                DiarioPlaybook.objects.create(aporte=aporte, dados_json={'nota': 'Teste'})
                response = self.client.post(reverse('excluir_aporte', args=[aporte.id]))
                self.assertRedirects(response, reverse('historico_aportes'))
                self.assertFalse(Aporte.objects.filter(pk=aporte.pk).exists())
                self.assertFalse(ItemAporte.objects.filter(aporte_id=aporte.pk).exists())
                self.assertFalse(DiarioPlaybook.objects.filter(aporte_id=aporte.pk).exists())
        self.posicao.refresh_from_db()
        self.assertEqual(self.posicao.quantidade, 10)

    def test_exclusao_exige_post_e_csrf(self):
        aporte = Aporte.objects.create(carteira=self.carteira)
        url = reverse('excluir_aporte', args=[aporte.id])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(url).status_code, 403)
        self.assertTrue(Aporte.objects.filter(pk=aporte.pk).exists())

    def test_historico_oferece_exclusao_para_cancelado(self):
        aporte = Aporte.objects.create(carteira=self.carteira, status='cancelado')
        response = self.client.get(reverse('historico_aportes'))
        self.assertContains(response, reverse('excluir_aporte', args=[aporte.id]))
