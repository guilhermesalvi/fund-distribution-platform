---
name: prd
description: Cria e revisa PRDs com requisitos de negócio rastreáveis. Use para requisitos de produto ou documentação do comportamento de um produto existente; exclui especificações técnicas e documentação geral.
---

# Requisitos de produto

Descreva o problema, o usuário e o comportamento esperado no negócio. Decisões de implementação pertencem ao trabalho técnico posterior.

## Escopo e autorização

Siga o pedido da sessão e as convenções aplicáveis de `CLAUDE.md` e das regras em `.claude/rules` antes dos padrões desta skill. Preserve decisões delegadas e autorizações existentes. Um pedido de PRD termina com o documento e sua revisão; commit não é condição para entregar ou usar o arquivo atual. Operações Git seguem a autorização da mudança e a convenção do repositório.

Caminhos iniciados por `/docs/` partem da raiz do repositório. A prosa desta skill e dos artefatos é em português; os contratos de formato estão em [conventions.md](references/conventions.md).

## Escolha da entrada

| Pedido | Referências necessárias | Entrega |
|---|---|---|
| Criar um PRD | [intake.md](references/intake.md), [writing.md](references/writing.md), [conventions.md](references/conventions.md) | PRD com fatos, hipóteses e lacunas distinguíveis |
| Revisar um PRD | Documento atual, regras das seções afetadas em [writing.md](references/writing.md) e formato em [conventions.md](references/conventions.md) | Mesmo arquivo revisado |
| Documentar um produto existente | Referências de criação e [modes.md](references/modes.md) | Comportamento observado e intenção inferida identificados |
| Documentar plataforma, SDK ou API como produto | Referências de criação e [modes.md](references/modes.md) | PRD voltado ao consumidor |

Aplique a revisão de [workflow.md](references/workflow.md) à entrega. Consulte [prose.md](references/prose.md) ao escrever ou revisar prosa e [example.md](references/example.md) quando um exemplo resolver dúvida de formato. Leia apenas as seções pertinentes e amplie a leitura quando encontrar dependências.

Dívida técnica sem impacto funcional, processo interno e decisão de arquitetura pedem outro artefato. Um pedido apresentado como tela ou CRUD pode ser um PRD: investigue a capacidade de negócio pelo material disponível, conforme [intake.md](references/intake.md).
