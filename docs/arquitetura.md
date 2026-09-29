# Arquitetura do pipeline documental

Este documento descreve a implementação atual de Ingestion / Document Intelligence. A responsabilidade desta camada termina na produção de texto limpo, segmentado por página e rastreável para as etapas seguintes.

## Fluxo atual

```text
DocumentInput
     ↓
InputClassifier
     ↓
PDFProcessor / OCRDocumentProcessor
     ↓
Document → Page
     ↓
TextCleaner
     ↓
Chunker
     ↓
Document com provenance
```

O pipeline aceita PDFs, PNGs e JPEGs. A classificação utiliza exclusivamente o `media_type` declarado no `DocumentInput`.

## Contratos

Os modelos de domínio são definidos com Pydantic v2 em `src/ingestion/models.py`:

- `DocumentInput` contém `filename`, `media_type` e `content` em bytes. Metadados textuais e conteúdo não podem ser vazios.
- `ExtractionMethod` distingue `native` e `ocr`.
- `Page` representa uma página física. `page_number` deve ser positivo, `text` é sempre `str` e pode ser vazio ou conter somente whitespace. A lista de chunks é independente por instância.
- `Chunk` contém `chunk_id`, `document_id`, `page_number`, `chunk_index` e `text`. O texto deve ter pelo menos um caractere, inclusive quando esse caractere é whitespace.
- `Document` contém um `document_id` UUID, metadados, `total_pages` e páginas não vazias. A quantidade de páginas deve coincidir com `total_pages`, sem números duplicados.

A fronteira de identificadores é intencional:

```text
Document.document_id       = UUID
Chunker.chunk_page input   = UUID
Chunk.document_id          = str
```

O `Chunker` converte explicitamente o UUID para string ao materializar cada chunk.

## Classificação e entrada

`InputClassifier` reconhece exatamente:

| MIME | Tipo |
|---|---|
| `application/pdf` | PDF |
| `image/png` | imagem |
| `image/jpeg` | imagem |

Outros tipos geram `UnsupportedDocumentError`. A classificação não inspeciona extensão, assinatura binária ou conteúdo.

## PDF textual

`PDFProcessor` usa `pypdf` para extrair texto página a página. O resultado mantém a ordem física, numera páginas a partir de 1 e atribui `ExtractionMethod.NATIVE`.

Páginas sem texto extraível permanecem no `Document` com `text=""`; não são descartadas.

Falhas de leitura, parsing ou extração são convertidas em `PDFExtractionError`, preservando a causa original quando disponível.

## OCR

`OCRDocumentProcessor` implementa a fronteira `OCRProcessor` para imagens e PDFs. Ele utiliza:

- Pillow para abrir imagens e materializar rasterizações;
- PyMuPDF para rasterizar cada página de PDF;
- pytesseract como adaptador Python;
- Tesseract como engine local.

Imagens produzem uma página OCR. PDFs produzem uma página OCR para cada página rasterizada, preservando ordem e numeração. O OCR não cria chunks nem executa limpeza; essas responsabilidades pertencem ao pipeline.

Ausência de Pillow, PyMuPDF, pytesseract, Tesseract, dados de idioma, rasterização ou reconhecimento gera `OCRProcessingError`.

## Fallback de PDF

Para um PDF, o `DocumentIngestionPipeline` executa primeiro o `PDFProcessor`. Se nenhuma página contiver texto útil após a extração nativa, o `DocumentInput` original é enviado ao OCR:

```text
PDF → PDFProcessor
       ├── texto útil → Document nativo
       └── sem texto útil → OCRDocumentProcessor → Document OCR
```

O documento OCR substitui integralmente o documento nativo. Não há mistura entre os resultados.

PDFs parcialmente textuais seguem a política atual: se ao menos uma página possuir texto útil, o documento nativo completo é preservado. OCR seletivo por página não faz parte desta implementação.

## Limpeza

`TextCleaner` atua sobre `str` e executa normalização estrutural:

- CRLF e CR são convertidos para LF;
- espaços e tabs horizontais redundantes são normalizados;
- espaços nas extremidades são removidos;
- excesso de linhas vazias é reduzido.

A limpeza não reconstrói palavras hifenizadas e não aplica regras de negócio. Testes cobrem preservação de números, percentuais, datas, valores monetários, Unicode, pontuação e termos jurídicos.

## Chunking

`Chunker` divide cada página em fatias consecutivas de caracteres, com tamanho máximo configurável e padrão de 1000 caracteres.

Garantias:

- `chunk_index` começa em zero;
- não há overlap;
- nenhum caractere é perdido ou duplicado;
- páginas vazias produzem lista vazia;
- whitespace é preservado quando forma parte do texto;
- `"".join(chunk.text for chunk in page.chunks) == page.text` quando há chunks;
- IDs e páginas de origem são preservados.

## Proveniência

A rastreabilidade é mantida pela relação:

```text
Document.document_id
        ↓
Page.page_number
        ↓
Chunk.document_id
Chunk.page_number
Chunk.chunk_index
Chunk.text
```

Assim, cada trecho pode ser localizado no documento e na página original. O pipeline não interpreta semanticamente a apólice e não inventa valores ausentes.

## Exceções

A hierarquia pública é:

```text
DocumentIngestionError
├── UnsupportedDocumentError
├── InvalidDocumentError
└── DocumentProcessingError
    ├── PDFExtractionError
    └── OCRProcessingError
```

Entradas incompatíveis, parsing inválido, extração e OCR não são convertidos em sucesso silencioso.

## Tecnologias e dependências

O código atual utiliza Python, Pydantic, pypdf, Pillow, PyMuPDF, pytesseract, Tesseract, pytest e Streamlit para a tela inicial. Não há integração atual com LLM, banco de dados, comparação de apólices ou upload na interface.

O alias `fitz` utilizado pelo PyMuPDF emite uma advertência de depreciação em versões recentes, mas não apresentou impacto funcional durante a validação. A migração para `pymupdf` é uma manutenção futura separada.

## Limitações conhecidas

- a interface Streamlit ainda é informativa e não executa upload ou processamento;
- a extração estruturada, comparação e persistência serão responsabilidade de etapas posteriores;
- a homologação externa validou PDFs textuais reais, imagens reais derivadas de páginas reais e OCR rasterizado, mas não obteve um PDF público escaneado ou híbrido íntegro para validação empírica adicional;
- testes de integração geram fixtures pequenas em runtime e não versionam apólices reais.
