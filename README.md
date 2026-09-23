# InsurMinds — D&O Policy Analyzer

Projeto final: plataforma inteligente para análise e comparação de apólices D&O (Directors and Officers).

## Estado

Estrutura inicial, com página Streamlit informativa. O pipeline de análise, OCR, integração com LLM e persistência ainda será implementado. Não é um MVP funcional de análise nesta fase.

## Objetivo e arquitetura prevista

Receber documentos, extrair texto (OCR quando necessário), organizar informações num schema validado, armazenar os resultados e comparar apólices com referências às páginas e cláusulas de origem.

```text
PDF/imagem → ingestion → extraction → database → comparison → app
```

A comparação deverá começar por regras determinísticas sobre dados normalizados. A IA poderá explicar diferenças apoiada nas evidências. Informação ausente deve ser assinalada, nunca inventada; a interpretação exige validação da pessoa de seguros.

## Estrutura

| Pasta | Responsabilidade |
|---|---|
| `app/` | Interface Streamlit |
| `src/ingestion/` | Leitura de documentos, texto por página e OCR |
| `src/extraction/` | Schema e extração estruturada com LLM |
| `src/comparison/` | Comparação e explicações com evidências |
| `src/database/` | Persistência e consultas |
| `src/utils/` | Configuração e utilitários partilhados |
| `tests/` | Testes automatizados e casos de validação |
| `data/samples/` | Orientações para exemplos sintéticos |
| `docs/` | Arquitetura, responsabilidades e decisões |
| `Projeto_Final_Artefatos/` | Relatório, diagramas e apresentação |

## Preparação local

Recomendado: Python 3.11 ou 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m streamlit run app/main.py
```

No Windows, ativar com `.venv\Scripts\activate`. A página inicial não requer chave de API. O `.env.example` prepara variáveis para futura integração; a aplicação inicial ainda não as lê. As dependências são intervalos iniciais, ainda sem lockfile validado. OCR poderá exigir dependências adicionais quando a equipa escolher o motor.

## Equipa e próximos passos

Ver [responsabilidades](docs/responsabilidades.md) e [arquitetura](docs/arquitetura.md).

1. Validar os campos D&O e preparar dois documentos sintéticos.
2. Definir contratos de dados com evidências por página.
3. Implementar extração, persistência e comparação.
4. Integrar a interface e validar os resultados com a pessoa de seguros.
5. Documentar limitações, métricas e demonstração.

## Dados e credenciais

O repositório é público. Não incluir apólices reais, dados pessoais ou credenciais. Os ficheiros de dados locais e `.env` são ignorados por padrão. Antes de publicar exemplos, confirmar que são sintéticos ou devidamente anonimizados e autorizados.

## Validação

A pasta `tests/` contém o plano inicial. Ainda não existem testes funcionais. Após os implementar, executar `python -m pytest`.

## Licença

Código disponibilizado sob a licença [MIT](LICENSE).
