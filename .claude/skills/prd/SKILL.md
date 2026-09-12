---
name: prd
description: 'Cria e refina PRDs de produto ou feature: problema, usuário, comportamento de negócio, requisitos com ID, métricas e trade-offs. Use para "PRD", "product requirements", "especificação de produto", "vamos documentar/especificar essa feature", inclusive PRD do que já existe e pedido enquadrado como tela ou CRUD; não para tech spec, design, tasks, ADR, notas de reunião, documentação geral ou spec de API sem contexto de produto.'
---

# PRD Writer

Descreva o problema, o usuário afetado e o comportamento de negócio esperado. As decisões de implementação pertencem ao trabalho técnico posterior.

## Quando é PRD

É PRD a feature, o produto digital ou a iniciativa tecnológica com impacto funcional para um usuário: depois dela o usuário observa um resultado novo, um dado novo ou um prazo novo. Iniciativa técnica que produz um desses três ganha PRD focado no impacto, não na implementação.

| Não é PRD | Artefato certo |
|---|---|
| Dívida técnica, refactor, modernização sem impacto funcional novo | ADR, doc de dívida técnica, plano de refactor |
| Decisão arquitetural | ADR |
| Processo interno sem entrega de software | Runbook, doc de processo |
| Contratos de API, módulos, plano de tarefas, design de componente | Tech spec, design doc |

Dois enquadramentos têm tratamento próprio:

- Pedido que é PRD mas chega enquadrado como implementação, tela ou CRUD: reenquadre pelo problema (intake.md, Escopo problemático).
- "PRD do que já existe" (reverse PRD) e plataforma, infra, SDK ou API como produto: siga modes.md; ele diz o que muda em cada um desses modos.

## Escolher a entrada

| Pedido | Entrada | Ler | Resultado desta entrada |
|---|---|---|---|
| Criar PRD; product requirements; especificar produto ou feature | Criação | [intake.md](references/intake.md); [writing.md](references/writing.md); [conventions.md](references/conventions.md); [workflow.md](references/workflow.md) | PRD e apresentação das pendências pertinentes |
| Atualizar PRD | Edição | PRD atual; [IDs e regras afetadas](references/writing.md#ids); [Edição no lugar](references/conventions.md#edição-no-lugar); [workflow.md](references/workflow.md) | O mesmo arquivo revisado e checado |
| Documentar o produto existente | Reverse PRD | Referências de criação e [Modo reverse PRD](references/modes.md#modo-reverse-prd) | Reverse PRD com intenção inferida marcada |
| Plataforma, infra, SDK ou API como produto | Produto consumido por outro time ou sistema | Referências de criação e [modo correspondente](references/modes.md#modo-plataforma-infra-sdk-ou-api-como-produto) | PRD com consumidor e métricas adequados ao produto |

Redação: [Convenções de escrita](references/prose.md#convenções-de-escrita). Leia a política uma vez por versão do arquivo na sessão de escrita. Leia o exemplo por seção conforme a referência abaixo.

## Limites

- **Aprovação é o commit.** Árvore suja é trabalho em elaboração; arquivo commitado é a versão válida.
- **Precedência.** Para layout, seções, idioma e forma, vale primeiro o pedido da sessão, depois a convenção do repositório e por último os defaults desta skill. Achado de forma decorrente dos dois primeiros é mantido e relatado (workflow.md, Checar).
- Tags, IDs e fonte única das regras são definidos em (writing.md, Tags), (writing.md, IDs) e (writing.md, Uma regra, um lugar).
- Resultados de checagem, notas de confiança e marcas de validação ficam fora do PRD. Relate a verificação não executada e os achados remanescentes conforme (workflow.md, Checar); não declare aprovação sem evidência.

## Leitura por etapa

Para uma entrada nova, leia suas referências e dependências normativas. Para uma correção localizada, leia o trecho afetado, os pré-requisitos, as exceções e os citadores; amplie a leitura quando surgir dependência. A distinção entre regeneração e ajuste localizado é definida em (workflow.md, Apresentar e iterar). Leitura seletiva não dispensa a validação e a revisão do artefato completo ou revisado (workflow.md, Revisão antes de apresentar).

## Exemplo

PRD no formato-alvo em [references/example.md](references/example.md). Leia a seção correspondente na primeira vez, nesta sessão, em que escrever uma seção da tabela (writing.md, Seções); não é template a copiar. Exemplos adicionais são lidos somente para a seção produzida ou para esclarecer um defeito editorial observado.
