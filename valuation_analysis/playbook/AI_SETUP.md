# Análise da IA no Playbook

O botão Análise da IA envia os dados atuais do editor para POST
`/playbook/<aporte_id>/analisar/`. A resposta aparece na página. “Salvar análise
e Playbook” ou “Salvar Playbook” grava também o último resultado gerado.
Sem clicar em salvar, uma análise nova não é preservada ao sair da página.
O resultado salvo reaparece no editor com data e modelo. Guarda os dados enviados
à IA, para não confundir a análise com alterações posteriores do diário.
Uma nova tentativa que falhe mantém o resultado anterior.

Durante a consulta, o painel exibe animação e tempo decorrido, sem estimar
percentual de conclusão. Os botões de salvar ficam desativados até a resposta.
O backend assina o resultado e valida a assinatura e o aporte ao salvar
(prazo de sete dias para salvar a nova análise). O registro fica em
`DiarioPlaybook.dados_json.analise_ia`, sem nova migração. Salvamentos posteriores
sem resultado novo preservam a análise existente.

## Configuração

Adicione ao `.env` de `valuation_analysis/` as variáveis do arquivo
`../.env.example`, preservando as configurações existentes. Preencha as chaves
de API `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` e `MOONSHOT_API_KEY` dos provedores
que deseja ativar. Reinicie o Django após configurar. É possível usar apenas um.

Os modelos são configuráveis por `AI_CLAUDE_MODEL`, `AI_GPT_MODEL` e
`AI_KIMI_MODEL`. Os valores padrão estão no exemplo. As chaves ficam no servidor.
A dependência `litellm==1.100.1` está em `requirements.txt`.

### Modelo Kimi indisponível

Uma chave válida pode retornar HTTP 404 quando o modelo não está disponível
para a conta. Nesta configuração, a API não disponibilizou `kimi-k2.5`;
o `.env` local passou a usar `AI_KIMI_MODEL=moonshot/kimi-k2.6`, listado pela API.
Após alterar o `.env`, reinicie o Django para carregar o modelo e limpar a espera
do cache local. Não é necessário trocar uma chave válida por esse motivo.

`validation/kimi_connection.py --models` consulta os modelos da conta sem gerar
texto. Sem esse argumento, o script faz uma chamada real de teste com até 32
tokens de saída; não envia dados do Playbook nem imprime a chave. Essa resposta
curta pode terminar por limite de tokens, pois o modelo também pode raciocinar.

## Fluxo e extensão

- `services/ai_analysis.py`: `AIAgent` descreve um agente e `PlaybookAIAnalyzer`
  executa agentes sequencialmente. A ordem padrão é Claude → GPT → Kimi.
  O seletor permite escolher outro primeiro agente, mantendo os demais como reserva.
- Para adicionar agentes, acrescente entradas em `PLAYBOOK_AI_AGENTS` de
  `config/settings.py`, com `id` único, `name`, `model` LiteLLM e `key_env`.
  Também é possível injetar uma lista de `AIAgent` no construtor para outros usos.
- `services/analysis_instructions.txt` mantém o escopo do prompt anterior.
  `analysis_prompt.py` valida os dados e monta as mensagens no servidor.
- `services/asset_types.json` compartilha as metodologias e campos entre editor
  e prompt. Atualize esse arquivo ao acrescentar uma metodologia.

## Limites e falhas

O serviço detecta cota/créditos esgotados e limites temporários pelos erros
retornados pelo provedor; não consulta o saldo de tokens antecipadamente.
Agentes sem configuração são ignorados. Ao obter uma resposta, encerra as tentativas.
Se todos os agentes configurados atingirem cota ou limite, retorna aviso HTTP 429.
Falhas de chave/modelo, indisponibilidade e contexto têm motivos distintos na tela.
Uma resposta cortada pelo limite de saída é exibida com aviso de análise parcial.

Os padrões em settings são 180 segundos por agente e 4096 tokens de saída.
`PLAYBOOK_AI_TIMEOUT` no `.env` pode ajustar a espera entre 30 e 600 segundos.
Timeout tem mensagem própria e não é classificado como falta de créditos.
Há espera de 60 segundos após limite temporário e 3600 segundos após falta de
créditos; `Retry-After` válido do provedor prevalece, limitado a 24 horas.
Após uma recarga, é possível limpar a espera no shell Django:

```python
from playbook.services.ai_analysis import PlaybookAIAnalyzer
PlaybookAIAnalyzer().reset_limits('claude')
```

A espera e o bloqueio de análise simultânea por aporte usam o cache Django.
O cache padrão é local ao processo e reinicia com ele. Para múltiplos processos,
configure um cache compartilhado que suporte `add` atômico, como Redis.

## Validação

`manage.py test aporte playbook --noinput`: 44 testes aprovados.
`validation/preview.py` usa SQLite em memória, chaves fictícias e intercepta
LiteLLM; `validation/browser-check.cjs` verifica análise, troca de agente,
aviso de cotas, indicador de espera, salvar/reabrir análise e regressões das telas
em desktop e celular. `validation/kimi_connection.py --analysis` faz uma chamada
real com o prompt completo e dados fictícios; não envia os registros do usuário.

Referências: [exceções LiteLLM](https://docs.litellm.ai/docs/exception_mapping),
[Anthropic](https://docs.litellm.ai/docs/providers/anthropic),
[OpenAI](https://docs.litellm.ai/docs/providers/openai),
[Moonshot/Kimi](https://docs.litellm.ai/docs/providers/moonshot).
