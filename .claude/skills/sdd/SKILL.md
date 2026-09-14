---
name: sdd
description: Especifica, planeja, implementa e verifica mudanças de comportamento técnico com requisitos rastreáveis. Use para specs e execução de capacidades com regras ou contratos; exclui PRDs, documentação geral e ajustes mecânicos.
---

# Desenvolvimento orientado por especificação

A especificação define o comportamento técnico; o design escolhe a solução; as tarefas organizam a execução; a verificação reúne evidências. Regras de negócio pertencem ao PRD.

## Escopo

Siga o pedido, o `CLAUDE.md` e as regras aplicáveis de `.claude/rules`. As autorizações e decisões delegadas na sessão prevalecem sobre os padrões desta skill. Caminhos iniciados por `/docs/` são relativos à raiz do repositório.

Pedido de análise, spec, design ou plano termina na entrega solicitada. Implementação autorizada inclui correções e verificação dentro do escopo, sem aprovação ou commit obrigatório entre etapas. Consulte [workflow.md](references/workflow.md) para decisões, requisitos de entrada e limites.

## Escolha da etapa

| Pedido | Leia | Entrega |
|---|---|---|
| Definir comportamento técnico ou documentar módulo existente | [specify.md](references/specify.md) | `spec.md` |
| Projetar a solução | [design.md](references/design.md) | `design.md` |
| Decompor uma mudança técnica | [tasks.md](references/tasks.md) | `tasks.md` |
| Implementar uma capacidade ou spec | [execute.md](references/execute.md) | Alterações verificadas |
| Verificar implementação contra spec | [verify.md](references/verify.md) | Evidências e pendências |
| Retomar uma mudança SDD | [execute.md](references/execute.md), seção Retomada | Continuidade do escopo autorizado |
| Registrar decisão de projeto identificada no design | [adr.md](references/adr.md) | ADR |

“Continuar” ou “planejar” isoladamente não ativa SDD: determine a natureza do trabalho pelo contexto. Revisão geral de código, ADR avulso e correção editorial não exigem abrir este fluxo.

Leia a referência da etapa atual e apenas as dependências que a tarefa usar. Formato e rastreabilidade são conferidos em [validation.md](references/validation.md); redação em [prose.md](references/prose.md). Exemplos são didáticos e não definem contratos reais do repositório.
