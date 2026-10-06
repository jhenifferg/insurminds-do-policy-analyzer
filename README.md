# InsurMinds — Plataforma de análise e comparação de apólices D&O

Protótipo académico para receber duas apólices em PDF/imagem, extrair campos D&O com um LLM, comparar resultados e apresentar diferenças com citações por página e chunk. A ingestão/OCR é local; o texto só é enviado ao provedor Gemini, Groq ou OpenAI selecionado após a pessoa confirmar autorização na interface.

## Estado do MVP

O repositório contém ingestão/OCR, schema D&O validado, agente de extração com citações verificadas, comparação determinística, interface Streamlit e histórico local SQLite opcional. O salvamento está desligado por padrão. Campos não localizados não são tratados como ausência de cobertura e resultados ambíguos são sinalizados para revisão humana.

## Integrantes

- Jheniffer Guimarães — IA, agentes e comparação.
- Matheus Neves — IA, dados e desenvolvimento.
- Demais integrantes — nomes e frentes de trabalho a preencher pelo grupo antes da entrega.

## Tecnologias

- Python 3.11 ou 3.12;
- Streamlit;
- Pydantic v2;
- pypdf, Pillow e PyMuPDF;
- pytesseract e Tesseract OCR;
- API Gemini GenerateContent como provider primário, Groq como fallback automático e OpenAI como opção manual;
- pytest.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Instale também o Tesseract OCR e o pacote de idioma português. Em macOS:

```bash
brew install tesseract tesseract-lang
```

Em Debian/Ubuntu:

```bash
sudo apt install tesseract-ocr tesseract-ocr-por
```

## Configuração e execução

Copie `.env.example` para `.env`. O padrão e a primeira opção da aplicação são Gemini; Groq é usado automaticamente como fallback quando `GROQ_API_KEY` está configurada:

```bash
cp .env.example .env
```

Abra `.env` e configure `GEMINI_API_KEY`/`GEMINI_MODEL`. Para o fallback, configure `GROQ_API_KEY`/`GROQ_MODEL`. As variáveis genéricas `LLM_API_KEY`/`LLM_MODEL` continuam aceitas por compatibilidade. `LLM_PROVIDER` aceita `Gemini`, `Groq` ou `OpenAI`; a opção OpenAI usa `OPENAI_API_KEY`/`OPENAI_MODEL`. Depois:

```bash
set -a
source .env
set +a
python -m streamlit run app/main.py
```

O modelo de referência usado na validação foi `gemini-3.1-flash-lite`, com `openai/gpt-oss-20b` como fallback Groq. Os nomes podem ser trocados por modelos disponíveis na conta configurada.

A interface usa o provider, a chave e o modelo definidos no `.env`; esses controles não são exibidos ao usuário final. A interface pede confirmação de autorização antes de enviar o texto das apólices ao provider escolhido. Não use documentos confidenciais sem autorização para processamento externo.

## Fluxo de demonstração

1. Selecione exatamente dois PDFs, PNGs ou JPEGs.
2. Confirme que o envio do texto à API está autorizado.
3. Inicie a análise. A ingestão extrai texto/OCR; o agente estrutura os campos em lotes, valida o schema e verifica as citações.
4. Consulte a tabela comparativa, as evidências por apólice e os dados estruturados.
5. Opcionalmente, solicite uma explicação por IA baseada apenas no relatório estruturado.
6. Baixe a tabela comparativa em CSV.

O app não persiste os ficheiros enviados. Se a opção de histórico local for selecionada, os dados estruturados, citações e comparação são gravados no SQLite definido por `DATABASE_PATH` (por padrão `data/insurminds.sqlite3`). A comparação é apoio à análise e não determina qual apólice é melhor. O banco contém dados derivados das apólices; proteja o dispositivo e remova o arquivo quando não for mais necessário.

## Testes e validação

```bash
PATH="$PWD/.venv/bin:$PATH" python -m pytest -q
python -m compileall src tests
python -m pip check
```

O teste de OCR real depende do executável Tesseract e do idioma português instalados no sistema. A suíte não faz chamadas reais a APIs de LLM: os adaptadores são testados com respostas simuladas; a validação real de duas apólices deve ser executada manualmente com documentos autorizados.

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `app/` | Interface Streamlit e apresentação das diferenças |
| `src/ingestion/` | Receção, PDF, OCR, limpeza e chunks com proveniência |
| `src/extraction/` | Contrato D&O, agente LLM, normalização e explicação |
| `src/llm/` | Adaptadores REST nativos Gemini, Groq e OpenAI Chat Completions, com fallback |
| `src/comparison/` | Comparação determinística e relatório estruturado |
| `src/database/` | Histórico SQLite local e consulta de análises guardadas |
| `tests/` | Testes do pipeline documental e das etapas de IA/comparação |
| `data/samples/` | Orientações para dados sintéticos/anonimizados |
| `data/do/` | Materiais de trabalho locais, ignorados pelo Git |
| `docs/` | Arquitetura, responsabilidades e notas da implementação |
| `Projeto_Final_Artefatos/` | Relatório, pitch deck, vídeo e materiais auxiliares |

## Limitações conhecidas

- a extração generativa pode errar; cada valor deve ser verificado nas evidências e por especialista;
- a taxonomia inicial cobre um conjunto limitado de sinónimos e cláusulas;
- PDFs com muitas páginas exigem várias chamadas e podem aumentar custo/tempo;
- as apólices longas são divididas em lotes de até 16 chunks e processadas sequencialmente para caber nos limites de entrada e requisições dos provedores gratuitos;
- o histórico SQLite é local, opcional e não inclui os PDFs originais;
- franquias percentuais sem base de cálculo equivalente e franquias mistas ficam para revisão;
- a avaliação com golden dataset e métricas de precisão/recall/F1 ainda precisa ser concluída;
- os artefatos audiovisuais devem ser conferidos separadamente antes da entrega final;

## Documentação e entregáveis

- [Arquitetura](docs/arquitetura.md)
- [Responsabilidades](docs/responsabilidades.md)
- [IA, agentes e comparação](docs/ia-agentes-automacao/README.md)
- Link do repositório: <https://github.com/jhenifferg/insurminds-do-policy-analyzer>
- Licença: [MIT](LICENSE)

## Segurança dos dados

A pasta `data/do/` e o ficheiro `.env` são ignorados pelo Git. Use apólices públicas, sintéticas ou autorizadas. Remova qualquer chave, dado pessoal ou documento confidencial antes de publicar artefactos.
