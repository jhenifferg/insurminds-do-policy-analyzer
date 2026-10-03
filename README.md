# InsurMinds — Plataforma de análise e comparação de apólices D&O

Protótipo académico para receber duas apólices em PDF/imagem, extrair campos D&O com um LLM, comparar resultados e apresentar diferenças com citações por página e chunk. A ingestão/OCR é local; o texto só é enviado ao provedor Gemini ou OpenAI selecionado após a pessoa confirmar autorização na interface.

## Estado do MVP

O repositório contém ingestão/OCR, schema D&O validado, agente de extração com citações verificadas, comparação determinística, interface Streamlit e histórico local SQLite opcional. O salvamento está desligado por padrão. Campos não localizados não são tratados como ausência de cobertura e resultados ambíguos são sinalizados para revisão humana.

## Integrantes

- Jheniffer Guimarães — IA, agentes e comparação.
- Demais integrantes — nomes e frentes de trabalho a preencher pelo grupo antes da entrega.

## Tecnologias

- Python 3.11 ou 3.12;
- Streamlit;
- Pydantic v2;
- pypdf, Pillow e PyMuPDF;
- pytesseract e Tesseract OCR;
- API Gemini GenerateContent (ou OpenAI Chat Completions) para extração estruturada e explicação opcional;
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

Copie `.env.example` para `.env`, informe uma chave Gemini do Google AI Studio e um modelo habilitado na sua conta. Carregue as variáveis e inicie a interface:

```bash
cp .env.example .env
```

Abra `.env` e preencha `LLM_API_KEY` e `LLM_MODEL` (por padrão, `gemini-3.8-flash`). `LLM_PROVIDER` aceita `Gemini` ou `OpenAI`. Depois:

```bash
set -a
source .env
set +a
python -m streamlit run app/main.py
```

Também é possível selecionar o provedor e informar chave e modelo na barra lateral do app. A interface pede confirmação de autorização antes de enviar o texto das apólices ao provedor escolhido. Não use documentos confidenciais sem autorização para processamento externo.

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
python -m pytest -q
python -m compileall src tests
python -m pip check
```

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `app/` | Interface Streamlit e apresentação das diferenças |
| `src/ingestion/` | Receção, PDF, OCR, limpeza e chunks com proveniência |
| `src/extraction/` | Contrato D&O, agente LLM, normalização e explicação |
| `src/llm/` | Adaptadores REST nativo Gemini e OpenAI Chat Completions |
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
- o histórico SQLite é local, opcional e não inclui os PDFs originais;
- franquias percentuais sem base de cálculo equivalente e franquias mistas ficam para revisão;
- a avaliação com golden dataset e métricas de precisão/recall/F1 ainda precisa ser concluída;
- o nome dos demais integrantes, relatório técnico, pitch deck e vídeo ainda precisam ser acrescentados pelo grupo.

## Documentação e entregáveis

- [Arquitetura](docs/arquitetura.md)
- [Responsabilidades](docs/responsabilidades.md)
- [IA, agentes e comparação](docs/ia-agentes-automacao/README.md)
- Link do repositório: <https://github.com/jhenifferg/insurminds-do-policy-analyzer>
- Licença: [MIT](LICENSE)

## Segurança dos dados

A pasta `data/do/` e o ficheiro `.env` são ignorados pelo Git. Use apólices públicas, sintéticas ou autorizadas. Remova qualquer chave, dado pessoal ou documento confidencial antes de publicar artefactos.
