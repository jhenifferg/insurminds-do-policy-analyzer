# Roteiro do vídeo de demonstração

**Duração prevista:** 4 min 40 s. **Ficheiro final:** `InsurMinds_Projeto_Final.mp4`.

O roteiro evita afirmar métricas ainda não avaliadas. Grave a demonstração depois de configurar um modelo Gemini ou OpenAI habilitado e verificar que os dois documentos escolhidos podem ser enviados para processamento externo.

| Tempo | Ecrã e fala |
|---|---|
| 0:00-0:30 | **Problema.** “A leitura e comparação de apólices D&O exige localizar limites, franquias, coberturas, exclusões e condições temporais em documentos extensos. O InsurMinds organiza essa análise e mantém as fontes visíveis.” |
| 0:30-1:05 | **Arquitetura.** Mostrar o deck. Explicar ingestão PDF/OCR local, extração estruturada por LLM, validação Pydantic e citações por página/chunk, comparação determinística e explicação opcional. |
| 1:05-1:30 | **Preparação.** Mostrar a interface sem expor a chave. Selecionar duas apólices públicas/sintéticas autorizadas. Confirmar que o envio do texto ao provedor de IA selecionado foi autorizado e iniciar a análise. |
| 1:30-2:40 | **Extração.** Mostrar os campos estruturados de cada apólice. Abrir evidências de seguradora, vigência, LMG, franquia e uma cobertura. Explicar que citações não encontradas no chunk são rejeitadas e valores ambíguos ficam marcados. |
| 2:40-3:40 | **Comparação.** Mostrar a tabela com valores das apólices A/B e diferenças. Abrir “Evidências por diferença”. Destacar um valor maior e uma cláusula pendente de revisão, sem declarar uma apólice como melhor. |
| 3:40-4:10 | **Explicação e histórico.** Gerar a explicação opcional baseada no relatório. Mostrar que o histórico SQLite é opcional e local, com salvamento desligado por padrão. |
| 4:10-4:40 | **Limitações e próximos passos.** Informar que a taxonomia é inicial, a comparação de cláusulas exige validação especializada e o golden dataset/métricas ainda precisam ser avaliados. Encerrar com a arquitetura e os entregáveis do projeto. |

## Antes da gravação

- Configurar `OPENAI_API_KEY` e `OPENAI_MODEL` e executar a análise de ponta a ponta.
- Confirmar autorização para enviar os documentos selecionados ao provedor selecionado.
- Usar apólices públicas ou sintéticas sem dados pessoais não autorizados.
- Ocultar a chave e outros segredos da gravação.
- Não apresentar resultados ou métricas que não tenham sido verificados.
- Confirmar nomes dos integrantes e completar o slide de equipa antes da entrega.
