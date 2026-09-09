# Revisão

Passo 5 do workflow. Revisão é parte da entrega: nenhum PRD sai sem ela. São uma passada mecânica, uma passada "uma regra, um lugar" e três passadas de julgamento. Falha em qualquer uma exige ajuste antes de apresentar.

## Passada mecânica

Rode os scripts da tabela do SKILL.md depois de gravar o arquivo. Eles checam o que a auto-revisão da LLM faz mal: conformidade que sofre drift ao longo do documento (seções, prefixo, IDs, links, tags, placeholders, léxico). O que cada um checa está no docstring do script, impresso quando o script roda sem argumentos (`python scripts/<nome>.py`).

- `HARD`: violação mecânica. Corrija e rode de novo; nunca apresente PRD com HARD pendente. `HARD INCOMPLETO` é validação que não pôde ser feita (parser Mermaid indisponível): não é violação do documento, mas também nunca é sucesso; `lint_mermaid.py` sozinho sai com exit 3 nesse caso.
- `WARN`: heurística com risco de falso-positivo. Julgue, não obedeça cego.
- Todo bloco ```` ```mermaid ```` passa por parse (`lint_mermaid.py`, rodado à parte: o `lint_prd.py` não o chama). Bloco que não passou, fence sem fechamento ou parser indisponível é HARD: diagrama não validado é diagrama não entregue, porque o leitor só descobre o erro ao renderizar. Parser indisponível não se resolve sozinho: o linter nunca instala nada; `python scripts/lint_mermaid.py --setup` instala com autorização do usuário, e sem ela o PRD é apresentado como falha de validação (SKILL.md, Princípios). O parse garante que o diagrama renderiza, não que a estrutura do PRD está conforme; isso é o `lint_prd.py`.
- Linter verde significa esqueleto conforme, não PRD bom. As passadas seguintes cobrem o que nenhum check determinístico alcança e não são opcionais.

## Passada "uma regra, um lugar"

Aplica writing.md, Uma regra, um lugar, depois do linter. Para cada FR, em ordem:

1. Procure a mesma regra dita com outras palavras em Solução Proposta, Glossário, Considerações Regulatórias, Critérios de Aceitação, Métricas, Dependências, Perguntas em Aberto e no PRD 0000.
2. Substitua cada paráfrase pela citação do ID. Prosa que sobra sem a regra é prosa que sai.
3. Se a paráfrase e o FR divergem, decida qual está certo antes de apagar a paráfrase; a divergência é a informação, não o ruído.
4. Fato repetido em mais de um PRD vai para o 0000 e os PRDs citam.
5. Evento no catálogo do 0000 com consumidor que o PRD consumidor não declara: remova o consumidor ou declare o consumo no PRD dono.

## Passadas de julgamento

**Passada rápida.** Confira três itens: toda inferência está marcada (não a grafia da tag, que é do linter, mas se uma frase sem tag deveria ser `[PREMISSA]` ou `[LACUNA]`); há um conceito por parágrafo; o idioma segue a precedência (SKILL.md, Princípios). Drift de geração é real: itens que exigem disciplina ao longo do documento inteiro degradam.

**Passada detalhada.** Critérios de qualidade abaixo.

**Passada adversarial.** Ataque o próprio rascunho e, se houver decisão que um revisor cético atacaria, nomeie-a no Ponto de Maior Fragilidade (writing.md, Seções). Não é busca de regra violada, que é o trabalho das passadas anteriores; é a pergunta "se este PRD falhar, qual decisão terá sido a causa?". A LLM se autoavalia com generosidade: resista.

## Critérios de qualidade

Itens com alto risco de escape. Cada um cita a regra; não a repete.

- Capability test na Solução Proposta e nos FRs (writing.md, Lente DDD).
- Um FR, uma condição; nenhuma regra dita duas vezes (writing.md, Uma regra, um lugar).
- IDs com prefixo, todos resolvendo (writing.md, IDs).
- Toda métrica primária com guardrail (writing.md, Seções, Métricas de Sucesso).
- Trade-offs separados de Não-objetivos e de Perguntas em Aberto (writing.md, Seções).
- Premissa que derruba o PRD como primeira linha de Perguntas em Aberto, com "se falsa" e plano de validação (writing.md, Tags).
- Nenhuma seção existe só para cumprir forma: sem "Nenhuma.", sem bullet de contagem, sem seção vazia (writing.md, Seções).
- Critérios de Aceitação verificáveis e só os que acrescentam valores (writing.md, Seções).
- Discovery sintetizado, com origem marcada (intake.md, Material de discovery).
- Ponto de Maior Fragilidade, quando existe, não cosmético (writing.md, Seções).
