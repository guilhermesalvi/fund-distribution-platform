# Fluxo SDD

## Escopo e conclusão

O pedido da sessão prevalece sobre as convenções do repositório, que prevalecem sobre os padrões desta skill, dentro das permissões do ambiente.

| Pedido | Entrega e limite |
|---|---|
| Análise, especificação, design ou tarefas | Entregue o artefato solicitado e os pré-requisitos indispensáveis; encerre nesse escopo |
| Implementação completa | Defina o comportamento, implemente, corrija e verifique até concluir o escopo autorizado |
| Verificação | Inspecione a versão indicada e relate evidências; correções dependem do escopo do pedido |
| Retomada | Recupere o que falta e preserve autorizações e decisões anteriores |

A apresentação intermediária informa progresso. Não impõe espera quando a execução já está autorizada. Aprovação de conteúdo e autorização de Git são distintas: um commit registra uma versão, não é requisito para usar ou verificar os arquivos atuais. Commit, push e publicação seguem a autorização da mudança; commits são agrupados pelo motivo, conforme `CLAUDE.md`.

## Decisões e bloqueios

| Situação | Ação |
|---|---|
| Fato verificável no projeto ou em fonte primária | Consulte a fonte pertinente |
| Escolha técnica dentro da autonomia da tarefa | Decida, registre justificativa e custo relevante e continue |
| Inferência ainda não confirmada | Use `[ASSUMPTION]`, com origem, padrão adotado e justificativa |
| Informação ausente | Use `[GAP]`, indicando o impacto |
| Decisão material de negócio ou efeito externo fora da autorização | Prepare o resultado revisável e interrompa apenas a parte dependente |

Pergunte somente quando faltar informação indispensável que o contexto não resolve. Se perguntas forem vedadas, registre a lacuna e conclua o trabalho independente; não adote uma decisão de negócio sem autorização. Silêncio não é aprovação.

Quando uma regra bloquear trabalho autorizado, confira sua aplicabilidade e a precedência antes de parar. Se o bloqueio persistir, cite o arquivo e a instrução exata, a ação impedida e a decisão ou recurso necessário.

Corrija a causa no artefato que a define: regra de negócio no PRD, comportamento técnico na spec, mecanismo no design. Atualize os dependentes afetados; não enfraqueça testes para acomodar um defeito.

## Artefatos proporcionais à mudança

A implementação SDD precisa de comportamento testável antes do código. Use a spec existente ou escreva a parte ausente.

Crie `design.md` quando houver escolha arquitetural, integração, contrato público, persistência, migração ou risco que exija uma decisão técnica explícita. Considere também interações cuja solução não seja evidente pelas convenções existentes.

Crie `tasks.md` quando dependências, execução por etapas ou transferência de contexto exigirem um plano persistente. Caso contrário, um plano na conversa basta.

Se surgir uma necessidade dessas durante a execução, produza o artefato necessário e continue dentro da autorização. Contar arquivos, passos ou exemplos não substitui avaliar a necessidade.

| Etapa | Pré-requisito |
|---|---|
| Specify | Pedido ou fontes suficientes para descrever comportamento ou expor suas lacunas |
| Design | Spec atual com o comportamento pertinente definido |
| Tasks | Spec e, quando necessário, design atuais |
| Execute | Implementação autorizada e plano concreto coerente com os requisitos |
| Verify | Versão a examinar identificada; pode conter alterações locais ou trabalho parcial explicitamente solicitado |
| ADR | Decisão que estabelece convenção para futuras mudanças |

## Leitura e idioma

Use `CLAUDE.md` e as regras de `.claude/rules` aplicáveis aos arquivos afetados. Leia os requisitos, contratos, decisões e testes relacionados à mudança; amplie apenas quando aparecer uma dependência. A ausência de muitos exemplos não invalida uma convenção escrita.

Prosa, títulos livres e explicações são em português. Identificadores, arquivos, comandos, código, tags e palavras-chave EARS permanecem no idioma técnico original.

Os contratos de artefato continuam em inglês: títulos `##` definidos nas referências de Specify, Design, Tasks e ADR; comentários `sdd:`; `Requirement prefix:`; campos das tarefas; `Retired:`, `Design criterion:`, `Outside this capability:`, `No real alternative:`, `Participants:`, `Supersedes:`, `Superseded by:`, `Positive:`, `Negative:` e `Base:`.

Aplique [prose.md](prose.md) à redação. Estes formatos organizam o trabalho; a verificação de forma não prova qualidade nem conclusão.
