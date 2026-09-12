---
name: sdd
description: 'Especifica, projeta, planeja, implementa e verifica mudanças com requisitos técnicos rastreáveis. Use para SDD, tech spec, retomada de mudança ou implementação não trivial; não para PRD, discovery, ADR isolada, code review sem spec ou refactor mecânico.'
---

# Spec-Driven Development

Esta skill transforma requisitos técnicos em uma mudança verificável: Specify define o quê, Design define como, Tasks define a ordem, Execute implementa uma task por vez e Verify prova a conformidade à spec e ao design. O PRD em `/docs/prd`, com IDs `<PREFIXO>-nn`, fornece as regras de negócio; este método começa onde ele termina.

Use para especificação técnica ou de comportamento do sistema, design da solução, decomposição em tasks, implementação não trivial, verificação e retomada de uma mudança, incluindo “documente a spec do módulo X”. PRD/discovery, ADR isolada, code review sem spec e refactor mecânico ficam fora deste fluxo. Uma decisão de projeto identificada no Design usa a entrada ADR.

| Pedido | Entrada | Ler | Resultado desta entrada |
|---|---|---|---|
| Definir comportamento técnico; tech spec; documentar módulo existente | Specify | [specify.md](references/specify.md) | Spec |
| Projetar solução; design da solução | Design | [design.md](references/design.md) | Design |
| Decompor trabalho; quebrar em tasks | Tasks | [tasks.md](references/tasks.md) | Tasks |
| Implementar; implementar a spec; feature não trivial | Execute | [execute.md](references/execute.md) | Tasks executadas e Verify ao fim da implementação autorizada |
| Verificar a implementação | Verify | [verify.md](references/verify.md) | Relatório de evidência |
| Retomar mudança | Roteamento de retomada | [execute.md — Retomar](references/execute.md#retomar) | Próxima entrada válida, determinada pelos pré-requisitos |
| Registrar decisão de projeto descoberta no Design | ADR | [adr.md](references/adr.md) | ADR |

Execute somente a entrada solicitada e os pré-requisitos necessários para ela. Um pedido de spec, design ou tasks não autoriza implementar código. Numa implementação autorizada, Specify precede Execute; terminar a implementação exige Verify. A aprovação exigida entre entradas continua valendo.

Antes de atuar, leia os pré-requisitos e autorizações pertinentes em [workflow.md](references/workflow.md). Autorização de commit é permissão da operação; cada artefato ainda exige aprovação de conteúdo (workflow.md, Aprovação e autorizações). Regras de negócio são resolvidas no PRD; dúvidas seguem (workflow.md, Tags e dúvidas). Teste ou validação não executados nunca contam como aprovação.

Para entrada nova, leia sua referência inteira e as dependências normativas. Para correção localizada, leia o trecho afetado, seus pré-requisitos, exceções e citadores; amplie a leitura quando surgir dependência. Retomada também lê o plano e os requisitos da mudança. Layout e comentários de máquina estão em (specify.md, Layout); o contrato de execução está em (execute.md, Ciclo por task) e (execute.md, Segurança).

Redação: [Convenções de escrita](references/prose.md#convenções-de-escrita), uma vez por versão do arquivo na sessão de escrita. Leia exemplos somente do artefato produzido ou para esclarecer um defeito editorial observado. Antes de apresentar artefato completo ou revisado, cumpra [validation.md](references/validation.md): leitura seletiva não dispensa checagem de forma nem revisão. Checagem de forma limpa comprova forma; a revisão confere conteúdo e não grava estado de validação no artefato.
