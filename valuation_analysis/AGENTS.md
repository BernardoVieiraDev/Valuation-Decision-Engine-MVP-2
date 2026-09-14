# Contexto atualizado do Django

Leia `ALTERACOES.md` para o comportamento atual das telas e os comandos de validação.
Leia `playbook/AI_SETUP.md` para configurar ou alterar a integração LiteLLM.
- Análise da IA substitui Gerar Prompt; POST `/playbook/<id>/analisar/` analisa
  o rascunho sem salvar. `PlaybookAIAnalyzer` alterna Claude → GPT → Kimi.
- Prompt está em `playbook/services/analysis_instructions.txt`; metodologias em
  `asset_types.json`, compartilhadas pelo backend e editor. Chaves apenas no `.env`.
- Validação atual: 44 testes Django e navegador com respostas de IA simuladas.
- A análise gerada retorna token assinado por aporte; salvar grava o resultado e
  os dados analisados em `dados_json.analise_ia`. O editor restaura a análise salva.
  Não aceitar texto de IA arbitrário do navegador como resultado gerado.
- Indicador de espera usa animação e tempo decorrido; timeout padrão 180s por agente.
Estas observações substituem os trechos anteriores do mapa que descreviam as telas duplicadas:

- Aporte e Simulador são uma única tela em `/aporte/simulador/`; `/` redireciona para ela.
- Simular abre um modal e não cria Aporte/ItemAporte. O snapshot fica na sessão por 30 minutos
  (até 5 simulações), e POST `salvar_simulacao` confirma os valores revisados.
- `Aporte.simulacao_id` é único para impedir gravação duplicada da mesma confirmação.
- O tema do editor Playbook está em `static/portfolio/css/playbook.css`, usando os tokens globais.
- Atualização de cotações/tetos é compartilhada em `portfolio/services/portfolio_updates.py`.
- A exclusão de Aporte é definitiva e inclui itens e diário; não altera posições.
- Excluir Playbook limpa o JSON e marca `DiarioPlaybook.excluido`, preservando Aporte.
  O Histórico permite recriar o diário; não remover essa marca sem considerar a listagem.
- Os campos antigos do diário retirados da interface são preservados ao salvar registros existentes.
- O preço-teto do diário é salvo com duas casas; isso não muda fórmulas da API.
- A migração `playbook.0002` foi aplicada nesta cópia após backup do SQLite.
- Testes: `manage.py test aporte playbook`; a prévia de `validation/` usa banco em memória.
- Não usar exclusões em registros reais para validar alterações.
