# Mapa do projeto PlayBook — MVP V2

Levantamento: 2026-09-13. Referência persistente para futuras alterações.
Base: leitura do código desta cópia, sem consultar serviços externos ou registros do banco.
Os caminhos abaixo são relativos à raiz do workspace. Este mapa descreve o estado
encontrado, não uma arquitetura futura nem uma validação financeira das fórmulas.

## 1. Estrutura e execução

- `valuation_analysis/`: aplicação Django. `manage.py` é a entrada administrativa;
  `config/settings.py` configura apps, SQLite e estáticos; `config/urls.py` agrega rotas.
- `valuation-api/`: serviço FastAPI. `main.py` registra `/valuation`, `/assets` e `/market`.
  Possui `.git` próprio. O status Git não foi obtido porque o sandbox acusou ownership diferente.
- `venv/`: ambiente local cujo `pyvenv.cfg` informa Python 3.13.1.
- `valuation_analysis/db.sqlite3`: persistência local, não inspecionada nem modificada.
- Existem `.env` nas duas aplicações; seus valores não fazem parte deste mapa.

Dependências declaradas, sem versões fixadas:

- Django: django, python-dotenv, starlette, requests, groq.
- API: fastapi, uvicorn, python-dotenv, aiohttp, beautifulsoup4, httpx, yfinance, brapi, redis.
- Não foi encontrado pipeline Node/React de aplicação, Docker ou CI entre os arquivos levantados.
  A interface é renderizada pelo Django e complementada por JavaScript nos templates.

Entradas de execução deduzidas do código, ainda não validadas neste ambiente:

```powershell
# Terminal na raiz: Django independente
.\venv\Scripts\python.exe valuation_analysis/manage.py runserver 8000

# Outro terminal, dentro de valuation-api
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8001
```

Esse modo não atende automaticamente aos consumidores de `localhost:8000/api`.
`config/asgi.py` pretende montar FastAPI em `/api` e Django em `/`, mas importa
`app.main` e procura `app/.env`; a pasta `app` não existe na estrutura encontrada.
O cliente padrão aponta para `http://localhost:8001`, enquanto atualização individual
e cadastro usam explicitamente `http://localhost:8000/api`. O Panorama chama a porta
8001 diretamente no navegador. Resolver a topologia antes de presumir integração completa.

## 2. Módulos e pontos de alteração

### Portfolio

- `portfolio/models.py`: carteira, posições, preços, câmbio e propriedades calculadas.
- `portfolio/views.py`: dashboard, configurações, atualização individual e cadastro/remoção.
- `portfolio/services/api_client.py`: `PlaybookAPIClient`, chamadas síncronas com `requests`.
- `portfolio/templates/portfolio/`: `dashboard.html`, `configuracoes.html`, `gerenciar_ativos.html`.
- `portfolio/templates/base/base.html`: estrutura visual compartilhada e navegação.
- `static/portfolio/css/style.css`: CSS compartilhado; há também estilos nos templates.

Rotas: `/`, `/configuracoes/`, `/atualizar-ativo/<id>/`, `/gerenciar-ativos/`,
`/gerenciar-ativos/adicionar/`, `/gerenciar-ativos/remover/<id>/`.
As views normalmente selecionam `Carteira.objects.first()`; não há seleção por usuário
nesses fluxos. A gestão cria uma carteira se necessário e cadastra ações com quantidade zero.
Atualização de preços e cálculo de tetos percorrem as ações; somente resultados positivos
substituem valores persistidos. O dashboard ordena por margem de segurança decrescente.

### Aporte

- `aporte/services/strategy.py`: `StrategyConcentrado`, `StrategyDividido`, DTO de recomendação.
- `aporte/services/bandas_aporte.py`: limite financeiro para a banda e elegibilidade por peso.
- `aporte/views.py`: simulação, gravação, histórico, mudança de status e edição de itens.
- `aporte/models.py`: `Aporte` e `ItemAporte`.
- Templates: `aporte/simulador.html` e `aporte/historico.html`.

Rotas: `/aporte/simulador/`, `/aporte/historico/`, `/aporte/status/<id>/`,
`/aporte/editar-item/<id>/`.

O simulador filtra classes/tickers e aceita limite de ativos. Quando há alocação positiva,
grava automaticamente um aporte `em_analise` e seus itens positivos. O histórico permite
`em_analise`, `cancelado`, `efetuado`. Mudar status não compra ativos nem altera posições.
A edição de item exige `em_analise` e recalcula o total do aporte pela soma dos itens.

### Playbook

- `playbook/models.py`: `DiarioPlaybook`, relação um-para-um com `Aporte`.
- `playbook/views.py`: lista, inicialização a partir dos itens, tradução de parâmetros e salvamento.
- `playbook/templates/playbook/index.html`: editor interativo, `ASSET_TYPES`, estado JavaScript,
  campos de tese/convicção/premortem e geração de texto para copiar como prompt de IA.
- `playbook/templates/playbook/list.html`: acesso aos diários por aporte.

Rotas: `/playbook/`, `/playbook/<aporte_id>/`, `/playbook/<aporte_id>/salvar/`.
O JSON salvo contém `{nota, ativos}`. Cada ativo inclui identificador, ticker, tipo,
quantidade, preços, campos do diário e `values` de parâmetros. Na primeira abertura,
a view cria o diário e importa os itens; se já existe estado válido, ele é reutilizado.
Não foi encontrada chamada ativa à Groq nesse fluxo; o cliente HTTP apenas importa a biblioteca.

### Panorama

- `panorama/views.py` renderiza `panorama/templates/panorama/panorama.html`.
- Rota `/panorama/`; o navegador consulta moedas, índices, commodities, futuros,
  juros americanos e cripto em `/market` na porta 8001.
- Verificar formato dos retornos da API junto das funções JavaScript de renderização.

## 3. Modelo de dados e regras

`Carteira` tem nome, margem mínima e bandas superior/inferior. Seu total soma seis
relações: `ativos`, `fiis`, `criptos`, `rendas_fixas`, `etfs_br`, `etfs_internacionais`.

- Ações: `Acao` + `AtivoNaCarteira`; quantidade inteira, preço-teto, método e parâmetros.
- FIIs: `FII` + `FIINaCarteira`; quantidade inteira, segmento e métodos Bazin/valor patrimonial.
- Cripto: `Cripto` + `CriptoNaCarteira`; quantidade fracionária e cotação USD.
- Renda fixa: `RendaFixa` ligada diretamente à carteira; valor atual informado, tipo,
  indexador, taxa e datas. Não há precificação automática nesse modelo.
- ETF Brasil: `ETF` + `ETFNaCarteira`; quantidade inteira, preço BRL.
- ETF internacional: `ETFInternacional` + `ETFInternacionalNaCarteira`; frações e preço USD.
- `CotacaoDolar.atual()` usa o primeiro registro, ou 5.0 na ausência dele.

Cripto e ETF internacional convertem USD para BRL para compor o patrimônio.
Margem das ações/FIIs: `(teto - preço) / teto * 100`, com retorno zero para preços inválidos.
Peso: `valor da posição / valor total da carteira * 100`.
Limite de aporte: `(banda_decimal * total - posição) / (1 - banda_decimal)`.

Concentrado ordena por margem, limita a lista, verifica banda/margem e consome o orçamento.
Dividido seleciona por margem, divide igualmente e limita cada valor pela banda, sem
redistribuir sobras. Renda fixa não entra na seleção. Cripto/ETFs não têm margem própria
e recebem zero via `getattr`, ficando inelegíveis com a margem mínima positiva padrão.
A banda inferior é configurável, mas não participa das estratégias lidas.

`ItemAporte` guarda ticker/tipo como texto, preços, valor e parâmetros específicos em JSON.
É um snapshot parcial: parâmetros genéricos são recuperados da posição atual ao inicializar
o Playbook. Portanto o diário pode refletir configuração posterior à simulação.

## 4. API, cálculos e fontes

- `api/endpoints/valuation.py`: preços e métodos; parâmetros via query string.
- `api/endpoints/assets.py`: fundamentos por ticker.
- `api/endpoints/market.py`: cripto, moedas, juros, futuros, índices e commodities.
- `services/valuation_engine/asset_service.py`: orquestrador chamado literalmente
  `AssertService`, com singleton `assert_service`.
- `services/valuation_engine/valuation_formulas/`: Graham, Bazin, Peter Lynch, DFC, Projetivo.
- `services/valuation_engine/assets_formulas/`: BBAS, BBSE, BRBI, FLRY, GRND, ITSA,
  KLBN, PETR, SAPR, TAEE, VALE, WEGE e FIIs de papel/tijolo.
- `services/market_service.py`: acesso direto a provedores para cripto genérica e dólar.
- `models/stock.py`: dataclasses `ModelStock`, `Acao`, `Stock`; não são models Django.

Endpoints incluem `/valuation/get-price/{ticker}`, `/valuation/get-dpa/{ticker}`,
`/valuation/{metodo}/{ticker}` e `/assets/{ticker}`. Peter Lynch usa segmento `peter`;
o método persistido no Django é `lynch`. DFC usa chave de resposta `preco_teto_dcf`.
Os específicos retornam chaves como `preco_teto_bbas`. O cliente trata alguns resultados
numéricos e dicionários aninhados; preservar esses contratos ao mudar provedores.

`data_providers/data_provider.py` centraliza fallback:

- Ação brasileira: Brapi → Fundamentus → Yahoo → Alpha Vantage.
- Ação americana: Alpha Vantage → Yahoo.
- Moedas: AwesomeAPI; cripto: CoinGecko; juros: FRED; futuros: Yahoo;
  índices: TwelveData; commodities: CommodityPriceApiProvider.

O fallback aceita o primeiro retorno diferente de `None`, inclusive zero/estruturas vazias.
`BRAPI_API_KEY` e `ALPHA_VANTAGE_API_KEY` são exigidas durante importação dos provedores.
Há leitura de `COMMODITY_PRICE_API_KEY`; TwelveData atualmente lê `ALPHA_VANTAGE_API_KEY`.
Conferir a configuração específica de FRED no provider antes de alterar sua autenticação.

Cache em `infra/cache/`: conexão Redis assíncrona, repositório, decorator e gerador de chaves.
Variáveis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`. O decorator tolera falhas de leitura/gravação.
TTLs: preços/cripto 5 min; fundamentos 24 h; moedas/futuros/índices 15 min;
juros 6 h; commodities 1 h. Nem toda chamada de mercado passa pelo decorator.

## 5. Cuidados concretos para futuras alterações

- Unidades: `configuracoes.html` converte campos `data-percent="true"` entre percentual
  exibido e decimal persistido. Conferir cada fórmula antes de uniformizar taxas.
- Novo método: revisar choices/model, formulário, view, cliente, endpoint, serviço,
  calculadora, tradução em `playbook/views.py` e `ASSET_TYPES` do editor.
- Nova classe de ativo: a existência do model não implica suporte completo nas telas,
  atualização de preços, estratégia ou snapshot. Verificar cada etapa.
- ETF internacional no snapshot usa busca por `preco_atual`, embora o model possua
  `preco_atual_usd`/`preco_atual_brl`; pode registrar preço zero.
- A estratégia dividida pode produzir limite negativo para posição acima da banda.
  Confirmar comportamento esperado antes de corrigir; não houve correção neste levantamento.
- Chamadas `requests` do cliente não têm timeout explícito e o processamento é sequencial.
- Settings são de desenvolvimento: DEBUG ativo, hosts vazios e chave embutida.
  A atualização individual está marcada `csrf_exempt`; não inferir controles de produção.
- Há migrações em portfolio (0001–0007), aporte e playbook (0001).
  Mudanças de schema exigem migração; não reescrever histórico aplicado sem verificar.

## 6. Validação e manutenção deste contexto

Os arquivos de testes encontrados em portfolio/playbook são esqueletos sem casos.
Não foram encontrados testes da API no inventário de código da aplicação.
A tentativa `venv/Scripts/python.exe valuation_analysis/manage.py check` falhou com
“Acesso negado” ao iniciar o interpretador, antes da checagem Django.
Não foram iniciados servidores nem testados serviços externos ou navegação.
As inconsistências acima vêm da leitura estática, não de reprodução ponta a ponta.

Após futuras alterações, executar verificações adequadas ao escopo: Django check e
migrações pendentes para models; testes de limites/unidades para cálculos e estratégias;
contratos cliente/API para integrações; navegação e persistência para telas.
Atualizar este mapa quando as observações deixarem de corresponder ao código.
