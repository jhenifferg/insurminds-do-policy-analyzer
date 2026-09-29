# Plano de testes

Os testes unitários do pipeline documental estão em `tests/ingestion/` e os testes de integração em `tests/integration/`. Eles cobrem os contratos, classificação MIME, PDF nativo, imagens PNG/JPEG, OCR, fallback de PDF sem texto útil, limpeza, chunking, proveniência e tratamento de erros.

Execute a suíte com:

```bash
python -m pytest -q
python -m pytest tests/ingestion -q
python -m pytest tests/integration -q
```

Os cenários de OCR que dependem do executável Tesseract são executados quando Tesseract e os dados de idioma estão disponíveis; o teste negativo de ausência do executável é ignorado nesse ambiente quando a dependência está presente. A extração estruturada, comparação, persistência e interface de análise permanecem fora do escopo atual.
