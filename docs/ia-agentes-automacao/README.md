# IA, agentes e comparação

Implementação inicial da Pessoa 2: extração validada de dados D&O, normalização conservadora de cláusulas e comparação determinística. O texto recebido continua vindo do pipeline de ingestão (`src/ingestion/`), que mantém documento, página e chunk de origem.

## Fluxo

```text
Document (páginas/chunks)
        ↓
ExtractionAgent + adaptador LLM
        ↓
PolicyExtraction (Pydantic + evidências verificadas)
        ↓
ComparisonEngine (regras determinísticas)
        ↓
ComparisonReport com evidências
        ↓
ExplanationAgent (explicação opcional, sem ranking)
```

## O que está implementado

- `src/extraction/models.py`: contrato JSON tipado para identificação, segurado, vigência, retroatividade, períodos complementares/suplementares, run-off, LMG, LMI/sublimites, franquias, coberturas, exclusões e extensões.
- `src/extraction/agent.py`: agente que recebe chunks identificados em lotes pequenos, solicita JSON e valida o resultado com Pydantic; conflitos entre lotes ficam marcados como ambíguos.
- Evidências obrigatórias nos campos encontrados e cláusulas: `document_id`, página, `chunk_id` e citação literal. As citações são conferidas contra o texto do chunk antes de aceitar a extração.
- `src/extraction/normalization.py`: códigos determinísticos para um conjunto inicial de nomes e sinónimos D&O em português. Termos fora dessa lista ficam sem código e preservam o nome original.
- `src/comparison/engine.py`: comparação de LMG, franquias, limites de coberturas, coberturas e exclusões. As linhas incluem os dados de origem das duas apólices.
- `src/comparison/models.py`: saída estruturada com diferenças, valores, explicação factual e evidências.
- `src/extraction/explainer.py`: fronteira opcional para explicar o relatório. O prompt limita a explicação aos factos comparados e proíbe declarar uma apólice como “melhor”.
- `src/llm/gemini_client.py`: adaptador REST Gemini GenerateContent nativo, sem SDK adicional.
- `src/llm/groq_client.py`: adaptador Groq Chat Completions, sem SDK adicional.
- `src/llm/openai_client.py`: adaptador OpenAI Chat Completions, sem SDK adicional.
- `src/database/repository.py`: histórico SQLite local opcional, com leitura e gravação de extrações/relatórios.

## Regra importante sobre ausência

`not_found`, `ambiguous` e `not_applicable` são estados explícitos do schema. Se uma cobertura/exclusão aparece numa apólice e não foi localizada na outra, o comparador marca `needs_review`; não conclui que a outra apólice não a cobre/exclui. Diferenças jurídicas de redação também permanecem para revisão especializada.

## Ligação de um fornecedor LLM

Os adaptadores implementam `complete_json(system_prompt=..., user_prompt=...)` e `complete_text(...)`. Gemini usa o endpoint REST nativo `generateContent`; Groq e OpenAI usam Chat Completions compatível. Gemini é o provider primário e Groq pode ser ativado como fallback. A chave, o provedor e o modelo são fornecidos pelo ambiente; a interface final exibe apenas o status do modelo. A interface exige confirmação antes de cada nova análise. Não envie apólices reais ou dados pessoais para um serviço externo sem autorização da equipa.

Exemplo de composição no código:

```python
from src.comparison import ComparisonEngine
from src.extraction import ExtractionAgent

policy_a = ExtractionAgent(llm_adapter).extract(document_a)
policy_b = ExtractionAgent(llm_adapter).extract(document_b)
report = ComparisonEngine().compare(policy_a, policy_b)
```

## Próxima validação com a equipa

1. Confirmar schema, estados de ausência e taxonomia com a pessoa de seguros.
2. Verificar se franquias percentuais/mistas precisam de campos de base de cálculo adicionais.
3. Definir critérios para Side A/B/C, EPL, investigações regulatórias, exclusões e gatilhos de fraude.
4. Confirmar modelo disponível e política de tratamento de documentos.
5. Criar exemplos sintéticos anotados e avaliação contra o golden dataset descrito em `data/do/referencias/`.
6. Reservar revisão humana para ambiguidades e diferenças de redação; avaliar precisão/recall/F1.
