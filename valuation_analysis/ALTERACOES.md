# Refatoração de Aporte, Playbook e Panorama — 2026-09-13

Todas as alterações desta etapa estão dentro de `valuation_analysis/`.

## Atualização: Análise da IA

Nova atualização: indicador animado com tempo decorrido durante a consulta,
timeout configurável (padrão 180 segundos) e mensagem específica de tempo esgotado.
O botão “Salvar análise e Playbook” persiste a última análise com modelo, data e
snapshot analisado em `dados_json.analise_ia`, validando assinatura do servidor.
Ao reabrir o editor, a análise salva é exibida. Erros de novas consultas preservam
a resposta anterior. Não há migração. Validação: 44 testes Django e navegador,
incluindo espera, falha, gravação e reabertura.
Teste real com Kimi K2.6, prompt completo e dados fictícios: resposta completa
em 123 segundos, sem erro. Isso excede o timeout anterior de 45 segundos.

Correção da configuração local Kimi: a chave foi aceita na listagem de modelos,
mas `kimi-k2.5` retornou HTTP 404. O `.env` foi configurado com `kimi-k2.6`,
disponível para a conta. O diagnóstico `validation/kimi_connection.py` consulta
modelos com `--models` ou executa um teste curto real, sem dados do Playbook.

Gerar Prompt foi substituído por Análise da IA, com seletor de agente e resultado
na página. `PlaybookAIAnalyzer` usa LiteLLM e tenta Claude, GPT e Kimi em sequência,
com troca automática em caso de cota, limite ou indisponibilidade. O painel informa
os motivos das trocas e avisa quando todos atingem os limites. O prompt anterior
foi transferido para o servidor e as metodologias agora usam um JSON compartilhado.

Não há nova migração nem gravação antes da confirmação de salvar. Configuração e arquitetura
estão em `playbook/AI_SETUP.md`; variáveis de ambiente em `.env.example`.
Foram aprovados 42 testes Django e validação no navegador em desktop e celular,
incluindo troca de agente e cotas esgotadas. Não houve chamadas reais aos modelos.

## Atualização: confirmação da simulação e tema do Playbook

- Simular agora abre `aporte/resumo_modal.html`, com valores por ativo, total alocado e caixa.
  Fechar, pressionar Escape ou escolher “Não salvar” não cria registros no Histórico.
- POST `/aporte/salvar-simulacao/` salva o snapshot revisado da sessão, com CSRF e transação.
  Os rascunhos expiram em 30 minutos e são limitados a cinco por sessão. Campos financeiros
  enviados pelo navegador não substituem o snapshot do servidor.
- Migração `aporte.0002_aporte_simulacao_id` adiciona UUID opcional e único para impedir
  duplicações da mesma confirmação; aportes existentes mantêm esse campo vazio.
- Campos e filtros do formulário são mantidos após simular. Sem elegíveis, o modal
  explica o resultado e não oferece o botão de salvar.
- O CSS do Playbook está em `static/portfolio/css/playbook.css`. Usa os tokens do site,
  removendo o visual de papel, fontes serifadas e tons dourados. É responsivo.
- Validação desta atualização: 21 testes Django aprovados e navegação com dados fictícios
  para modal, descarte, confirmação, tema, salvamento e regressões anteriores.
- A migração `aporte.0002` foi aplicada nesta cópia após backup em
  `backups/db.before-simulation-confirmation-20260913.sqlite3`, sem excluir registros reais.

- A navegação tem uma única aba Aporte, em `/aporte/simulador/`. A raiz redireciona
  para ela. O template antigo apenas herda o unificado.
- Cotações e tetos usam `portfolio/services/portfolio_updates.py`, compartilhado
  com atualização individual. Os consumidores Django alterados usam o cliente
  padrão em `localhost:8001`, consistente com o dashboard anterior.
- O layout da carteira ocupa aproximadamente 60% e o formulário 40%; em telas
  menores eles ficam empilhados. A tabela permite rolagem horizontal quando necessário.
- POST `/aporte/excluir/<id>/` exclui aporte, itens e diário por cascade, sem mudar posições.
- POST `/playbook/<id>/excluir/` limpa o diário e marca `excluido=True`, preservando aporte
  e itens. A marca evita o reaparecimento como pendente na lista de Playbooks.
- POST `/playbook/<id>/recriar/`, acessível no Histórico, permite abrir novo diário
  importando o snapshot. Diários excluídos rejeitam salvamento de abas antigas.
- Os cinco campos removidos não são exibidos nem exigidos. Valores previamente
  persistidos são preservados por identificador ao salvar um diário existente.
- O preço-teto é normalizado para duas casas no editor e no backend; o JSON salva
  uma string decimal, interpretada numericamente pelo editor. Não altera a precisão
  dos cálculos da API nem os snapshots antigos.
- Panorama usa `static/portfolio/js/panorama.js`: destaques, filtros regionais,
  atualização manual, timeout e estados de indisponibilidade. Os endpoints da API
  externa não foram alterados. A interface informa o horário da consulta.

## Migração

`playbook/migrations/0002_diarioplaybook_excluido.py` adiciona a marca de exclusão.
Necessária antes de usar as novas telas com um banco já existente:

```powershell
# Executar na raiz do workspace
.\venv\Scripts\python.exe valuation_analysis/manage.py migrate playbook 0002
```

## Verificação

Nesta cópia, a migração foi aplicada com sucesso após criar
`backups/db.before-playbook-exclusion-20260913.sqlite3`. Nenhum registro real foi excluído.
Foram aprovados 15 testes Django, a checagem de modelos/migrações e os testes de navegador
em 1600px e 390px, com respostas simuladas de sucesso e falha. Capturas em `validation/`.

```powershell
.\venv\Scripts\python.exe valuation_analysis/manage.py test aporte playbook --noinput
.\venv\Scripts\python.exe valuation_analysis/manage.py makemigrations --check --dry-run
```

`validation/preview.py` inicia uma prévia em 127.0.0.1:8766, com SQLite em memória
e dados fictícios. `validation/browser-check.cjs` usa Playwright/Edge headless para
testar layout, dados de mercado simulados, falhas, salvar/excluir/recriar Playbook
e excluir aporte. O caminho do Playwright no script corresponde ao runtime local.
Reinicie a prévia antes de repetir o teste completo, pois ele altera apenas os dados fictícios.

As verificações externas usam respostas simuladas; disponibilidade real da API e
credenciais dos provedores não foram validadas por estes testes.
