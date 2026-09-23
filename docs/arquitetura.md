# Arquitetura prevista

## Contratos a definir antes da implementação

- Ingestion: documento com identificador e lista de páginas contendo número, texto e origem (texto nativo ou OCR).
- Extraction: schema validado com seguradora, segurado, vigência, limites, franquias, coberturas, exclusões, extensões, territorialidade e retroatividade. A pessoa de seguros valida a lista final.
- Evidências: associar cada informação à página, trecho original e documento; distinguir valor ausente, ambíguo e confirmado.
- Comparison: diferenças por campo com valores, unidades, moeda e evidências de cada apólice. Não assumir que ausência no texto significa ausência de cobertura.
- Database: guardar metadados, versão do schema e resultados; evitar duplicação pelo hash do documento.

## Decisões iniciais

Python, Streamlit, Pydantic e SQLite são a base proposta. O fornecedor LLM e motor OCR serão validados pela equipa. O módulo de extração deve isolar a integração com o fornecedor.

## Critérios de aceitação do futuro MVP

1. Processar duas apólices de teste, preservando referência às páginas.
2. Produzir dados válidos no schema e marcar campos não encontrados.
3. Exibir diferenças rastreáveis e permitir revisão humana.
4. Medir correção da extração por campo contra exemplos anotados pela pessoa de seguros.
5. Documentar falhas de OCR, ambiguidades, custo e tempo de processamento.
