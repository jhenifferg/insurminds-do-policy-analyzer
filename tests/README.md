# Plano de testes

Os testes unitários do pipeline documental estão em `tests/ingestion/`; os testes de integração em `tests/integration/`; e os testes das etapas de IA, comparação e persistência em `tests/extraction/`, `tests/comparison/` e `tests/database/`. Eles usam adaptadores locais/falsos e não fazem chamadas de API pagas.

Execute a suíte com:

```bash
python -m pytest -q
python -m pytest tests/ingestion -q
python -m pytest tests/integration -q
```

Os cenários de OCR que dependem do executável Tesseract são executados quando Tesseract e os dados de idioma estão disponíveis; o teste negativo de ausência do executável é ignorado nesse ambiente quando a dependência está presente. A integração com API real não deve ser executada na suíte automática: use testes isolados com cliente falso para evitar custos, rede e envio de documentos.
