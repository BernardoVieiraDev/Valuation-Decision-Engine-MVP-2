# Contexto persistente do PlayBook — MVP V2

Este arquivo se aplica a todo o workspace. Leia `docs/MAPA_DO_PROJETO.md` antes de
alterações para recuperar a arquitetura, os fluxos e as limitações observadas.
O mapa foi levantado em 2026-09-13; confirme no código os pontos que for alterar.

- Produto: gestão de carteira, valuation, simulação de aportes e diário de decisão.
- `valuation_analysis/`: Django, SQLite, templates HTML e JavaScript embutido.
- `valuation-api/`: FastAPI, fórmulas, provedores de mercado e cache Redis.
- `venv/`: ambiente Python local; não é código da aplicação.
- Há um repositório Git dentro de `valuation-api/`; não presumir que a raiz ou o Django estejam versionados.
- Fluxo: carteira → preço/teto → estratégia de aporte → Aporte/ItemAporte → DiarioPlaybook.
- Telas e gestão de carteira usam principalmente ações; os modelos incluem outras classes.
- A API usa tanto `localhost:8001` quanto `localhost:8000/api` em consumidores distintos.
  O ASGI referencia `app.main`, mas a pasta encontrada é `valuation-api/`.
- Preservar os contratos entre models, views, parâmetros HTML, cliente HTTP e API.
- Não confundir `ticket` nos models Django com `ticker` na API e no histórico.
- Conferir unidade de cada taxa: métodos genéricos e específicos não têm uma convenção única.
- Preservar snapshots do histórico e o formato JSON do diário ao alterar esses fluxos.
- Não modificar banco SQLite, segredos de `.env` ou dados reais para fazer verificações.
- Não assumir execução operacional validada: o levantamento foi estático; o Python
  do venv retornou acesso negado ao tentar `manage.py check`.
- Atualizar o mapa quando uma alteração mudar arquitetura, contratos ou fluxos.
- Comunicar alterações ao usuário em português.
