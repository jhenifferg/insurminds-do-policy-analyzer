# InsurMinds — D&O Policy Analyzer

Plataforma para análise e comparação de apólices D&O (Directors and Officers). A camada consolidada neste momento é o núcleo de ingestão e Document Intelligence, responsável por transformar PDFs e imagens em conteúdo textual estruturado, limpo, segmentado e rastreável.

## Estado atual

O pipeline documental está implementado e validado com testes unitários, testes de integração e documentos reais. Extração estruturada de campos D&O, comparação de apólices, persistência, integração com LLM e fluxo de análise na interface pertencem às etapas seguintes.

## Pipeline atual

```text
PDF / Imagem
      ↓
Classificação
      ↓
Extração nativa / OCR
      ↓
Limpeza conservadora
      ↓
Páginas
      ↓
Chunks
      ↓
Proveniência
      ↓
Conteúdo utilizável
```

Para PDFs, a extração nativa é tentada primeiro. Se nenhuma página produzir texto útil, o documento original é enviado ao OCR. Imagens PNG e JPEG seguem diretamente para OCR. PDFs parcialmente textuais preservam o documento nativo completo; OCR seletivo por página não faz parte do comportamento atual.

## Capacidades implementadas

- contratos validados com Pydantic v2;
- classificação de `application/pdf`, `image/png` e `image/jpeg`;
- extração nativa de PDF por página;
- fallback de PDF sem texto útil para OCR;
- OCR local de PNG, JPEG e PDF rasterizado;
- limpeza estrutural conservadora;
- preservação da numeração e ordem das páginas;
- chunking determinístico sem overlap;
- rastreabilidade por `document_id`, `page_number` e `chunk_index`;
- tratamento tipado de erros de entrada, PDF e OCR;
- testes unitários e de integração;
- validação externa com PDFs públicos reais e imagens derivadas de páginas reais.

## Rastreabilidade

Cada processamento gera um `Document` com `document_id` UUID. Cada `Page` preserva o número da página de origem e o método de extração. Cada `Chunk` referencia o documento, a página, sua posição e o texto correspondente.

```text
Document.document_id
        ↓
Page.page_number
        ↓
Chunk.chunk_index + Chunk.text
```

Essa relação permite que as etapas posteriores associem qualquer informação extraída à localização original na apólice.

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `app/` | Tela Streamlit inicial, ainda sem upload funcional |
| `src/ingestion/` | Entrada, classificação, PDF, OCR, limpeza, chunking e pipeline |
| `src/extraction/` | Espaço reservado para etapas futuras de extração estruturada |
| `src/comparison/` | Espaço reservado para comparação futura |
| `src/database/` | Espaço reservado para persistência futura |
| `src/utils/` | Utilitários do projeto |
| `tests/ingestion/` | Testes unitários do pipeline documental |
| `tests/integration/` | Testes integrados com documentos gerados em runtime |
| `data/samples/` | Orientações para dados de exemplo locais |
| `docs/` | Arquitetura e responsabilidades |
| `Projeto_Final_Artefatos/` | Artefatos do projeto final |

## Tecnologias

- Python;
- Streamlit;
- Pydantic v2;
- pypdf;
- Pillow;
- PyMuPDF;
- pytesseract;
- Tesseract OCR;
- pytest.

## Preparação local

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

### OCR local

O OCR utiliza Pillow, PyMuPDF, `pytesseract` e o executável Tesseract. Instale também o Tesseract e os dados de idioma necessários no sistema. Em Debian/Ubuntu:

```bash
sudo apt install tesseract-ocr tesseract-ocr-por
```

O processamento é local e não usa APIs externas. O idioma padrão do adaptador é `por`; para validar a instalação:

```bash
tesseract --version
tesseract --list-langs
```

Se o executável ou os dados de idioma não estiverem disponíveis, o pipeline falha explicitamente com `OCRProcessingError`.

## Testes

```bash
python -m pytest -q
python -m pytest tests/ingestion -q
python -m pytest tests/integration -q
python -m compileall src tests
python -m pip check
```

No ambiente validado, a suíte apresentou `109 passed, 1 skipped`. O skip corresponde ao teste negativo de ausência do Tesseract enquanto o executável está disponível. Os testes de integração usam documentos pequenos gerados em runtime e não versionam apólices reais.

## Limitações conhecidas

- a interface Streamlit ainda não possui upload nem processamento integrado;
- extração estruturada, comparação, persistência e LLM ainda estão fora deste escopo;
- a homologação externa não conseguiu obter uma amostra pública íntegra de PDF digitalizado para comprovar empiricamente o fallback automático;
- a homologação externa também não obteve um PDF híbrido público íntegro;
- o alias `fitz` usado pelo PyMuPDF emite uma advertência de depreciação, sem impacto funcional observado; a substituição futura por `pymupdf` é uma tarefa de manutenção.

## Dados e credenciais

O repositório é público. Não inclua apólices reais, dados pessoais ou credenciais. Arquivos locais de dados, `.env` e ambientes virtuais são ignorados pelo Git. O `.env.example` é mantido para etapas futuras e não é lido pelo pipeline atual.

## Documentação

- [Arquitetura](docs/arquitetura.md)
- [Responsabilidades](docs/responsabilidades.md)

## Licença

Código disponibilizado sob a licença [MIT](LICENSE).
