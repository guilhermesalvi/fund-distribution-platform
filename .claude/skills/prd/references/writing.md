# Conteúdo do PRD

O PRD define o comportamento de negócio. Destino, cabeçalho e idioma estão em [conventions.md](conventions.md); revisão em [workflow.md](workflow.md).

## Fatos, hipóteses e lacunas

Texto sem tag é fato sustentado pelo usuário, política formalizada, decisão registrada ou fonte primária. Use:

- `[ASSUMPTION]`: inferência que exige validação, com origem e justificativa.
- `[GAP]`: informação insuficiente para definir o conteúdo.

A hipótese que, se falsa, invalida a abordagem inteira aparece uma única vez: primeiro item de `Open Questions`, em negrito, com a expressão fixa `if false`, o impacto e como validá-la. Nos demais trechos, faça referência a ela.

## Teste de capacidade

Em `Proposed Solution`, na frase de solução de `Executive Summary` e nos FRs, descreva o resultado observável. Tela, serviço, banco, fila, cache, fornecedor e padrão de implementação geralmente pertencem à solução técnica.

Quando uma experiência ou interface pública for a própria capacidade solicitada, ela pode ser nomeada. Isso não autoriza inventar componentes ou protocolos.

| Formulação por mecanismo | Formulação por capacidade |
|---|---|
| Modal antes da exclusão | Excluir um registro ativo exige confirmação do usuário |
| Fila de auditoria a cada alteração | Cada mudança de estado registra autor e instante para auditoria |
| Assistente de envio com três telas | Envio de documentos com visibilidade do andamento |

No PRD de produto existente, aplique esse teste em todas as seções, conforme [modes.md](modes.md).

## Domínio e fronteiras

Use DDD quando houver vocabulário explícito, contextos ou catálogo de eventos; caso contrário, use módulo, área e integração.

O contexto de origem é dono da decisão. Contextos afetados entram no cabeçalho e em `Dependencies and Risks`. Uma fronteira exige evidência de diferenças nas regras e nos motivos de mudança; diferenças de palavras são sinais a investigar.

O glossário registra conceitos e relações. Sinônimos concorrentes dentro do contexto exigem reconciliação; entre contextos, podem ser termos legítimos para visões diferentes. Uma origem desconhecida recebe `[GAP]`, conforme a política de perguntas de [intake.md](intake.md).

Para subdomínio core, dê atenção aos critérios que preservam seu diferencial. Em capacidade genérica, avalie compra ou reuso quando pertinente. Não declare a classificação sem fonte.

Eventos reconhecem operações que mudaram estado e interessam a outro contexto. Identifique cenário, autor da mudança e consumidor. O catálogo compartilhado vive no PRD 0000; o PRD da capacidade declara o que produz e consome.

## Uma regra, uma fonte

O FR é a fonte normativa. Outras seções citam seu ID; o glossário pode definir o conceito em uma linha e citar o requisito. Cenários podem concretizar valores e resultados para testar a regra, sem criar outra definição.

Obrigações que podem falhar separadamente recebem FRs distintos. Uma condição conjunta com efeito indivisível fica no mesmo requisito. Atributos condicionais precisam de regra para seu fornecimento fora da condição: rejeitar ou ignorar é decisão de negócio.

Se uma paráfrase divergir do FR e a fonte não resolver, registre `[GAP]` em `Open Questions`; não escolha silenciosamente uma interpretação. Fatos compartilhados, mapa de contextos e catálogo de eventos ficam no PRD 0000.

## IDs

Use `<PREFIX>-nn` para FRs e `<PREFIX>-NFR-nn` para NFRs. Cada prefixo é único na pasta; neste repositório há um por PRD, inclusive quando o contexto possui várias capacidades.

```markdown
- **ONB-01 (Must)** Cada caso começa em `AwaitingDocuments`.
- **ONB-NFR-01** Uma submissão completa aparece em `UnderReview` em até um minuto.
```

FRs recebem `Must`, `Should`, `Could` ou `Won't`; NFRs não recebem MoSCoW. Toda citação deve resolver. IDs removidos não são reutilizados. Antes de alterar ou remover um ID, procure seus consumidores com `rg -n` na raiz.

Estados, motivos de resultado e enumerações que chegarão ao código têm coluna `Identifier` com o nome canônico, junto à tabela que os define.

## PRD 0000

Com dois ou mais prefixos na pasta, mantenha a visão geral em `0000-<slug>-overview.md`. Cada PRD regular aponta para ela na linha do prefixo. Ela cita regras por ID e não define requisitos.

Os títulos `##` são fixos, nesta ordem:

| Título | Conteúdo |
|---|---|
| Purpose | Propósito do projeto |
| Contexts | Contexto, responsabilidade, PRD, prefixo, posição e regras de integração |
| Event Catalog | Evento, produtor, consumidores, gatilho e IDs; evento sem consumidor confirmado fica como candidato |
| Flows Between Contexts | Fluxos pertinentes com IDs e, quando útil, Mermaid |
| Terms per Context | Correspondência de termos quando contextos usam nomes diferentes |
| Decisions Delegated to ADR | Decisão e requisito que ela deve satisfazer |

## Diagramas

Use Mermaid quando estados, decisões ou trocas entre contextos forem mais claros em grafo. Prefira `stateDiagram-v2`, `flowchart` e `sequenceDiagram`, os tipos reconhecidos pelo verificador.

Rótulos de transições e mensagens citam IDs. Ao lado de `stateDiagram-v2`, inclua a tabela de estados com `Identifier`. Evite aliases reservados como `end` e `off`; prefira nomes completos. Confira delimitadores e sintaxe, e renderize quando necessário para validar o desenho. O script cobre apenas parte da sintaxe.

## Seções

Use `#` para o título, `##` para as seções abaixo e `###` para temas que facilitem a leitura. Os títulos `##` são contratos em inglês e seguem a ordem da tabela. Seções opcionais só entram quando acrescentam conteúdo; não use seções vazias ou texto inventado.

| Título | Quando entra e conteúdo |
|---|---|
| Executive Summary | Obrigatória: problema, capacidade e métrica conhecida; explicite lacuna relevante |
| Strategic Alignment | Objetivo de negócio, OKR ou meta identificado na fonte |
| Context and Problem | Obrigatória: situação, impacto e evidências; separar hipóteses |
| Target User / JTBD | Obrigatória: um item por ator e resultado desejado |
| Opportunity / Hypothesis | Problema ainda em validação; hipótese e forma de verificá-la |
| Proposed Solution | Obrigatória: capacidade, relações, IDs e decisões técnicas posteriores |
| Domain Glossary | Termos sem definição suficiente ou com sinônimos concorrentes |
| Functional Requirements | Obrigatória em PRD regular: FRs com IDs e prioridades |
| Domain Events | Eventos produzidos e consumidos, citando IDs e o catálogo do PRD 0000 |
| Non-functional Requirements | Qualidades ou restrições para avaliar o design, com IDs; mecanismo pertence ao design |
| Regulatory Considerations | Norma identificada e lida; fonte, data e correspondência com requisitos |
| Non-goals | Exclusões adjacentes explicitadas no pedido ou material |
| Declared Trade-offs | Decisão tomada, custo concreto e justificativa |
| Success Metrics | Métrica ou meta sustentada pelo material, com proteção contra degradação |
| Acceptance Criteria | Cenários numéricos ou com ramificação que acrescentam poder de verificação |
| Dependencies and Risks | Dependência externa ao contexto, risco ou contexto afetado no cabeçalho |
| Open Questions | Lacuna ou hipótese material, divergência de regra ou intenção ainda sem decisão |
| Weakest Point | Decisão contestável que pode invalidar a solução ou a métrica principal |
| References | Fontes usadas, links e datas de consulta |

Em rascunho sem comportamento definido, registre a lacuna em `Functional Requirements` em vez de inventar requisito. A visão geral usa sua própria tabela de seções.

### Formatos específicos

- **Regulação:** cada artigo começa com norma e artigo e aponta por `→` aos IDs que o modelam. Uma nota após o ID tem até 20 palavras, limite preservado do verificador. Artigo não conferido recebe `[ASSUMPTION]`; norma ainda não identificada recebe `[GAP]`, sem ID.
- **Decisões:** `- **Decisão.** *Cost:* custo aceito. *Reason:* justificativa.` Não confunda decisão tomada com exclusão de escopo ou pergunta aberta.
- **Métricas:** diferencie indicadores antecipados e resultados quando existirem. Inclua uma linha `Guardrail` com o que não pode piorar. Sem proteção definida, use `Guardrail: [GAP]` e descreva a informação necessária; não invente indicador ou meta.
- **Aceitação:** a primeira coluna nomeia o caso, para permitir correspondência com testes. Use entrada, valores intermediários, ramo e resultado quando pertinentes. Cenários fora de tabela usam `**Given**`, `**when**`, `**then**` e citam o ID.
- **Dependências:** cada contexto de `; affects` possui uma linha. Acoplamento compartilhado aponta para PRD 0000.
- **Perguntas abertas:** registre assunto, impacto, responsável e critério de resolução quando conhecidos. Decisão já tomada vai para o requisito ou para os custos; decisão de arquitetura delegada aponta para Design/ADR.
- **Ponto fraco:** descreva a decisão contestável, como ela pode falhar e a evidência necessária para julgá-la. Distinga erro factual, informação ausente e julgamento sobre fatos. Não invente fragilidade para demonstrar rigor. Quando existir, é a última seção de conteúdo, seguida somente por `References`.

Formas explicitamente exigidas pelo pedido ou por convenção prevalecem sobre esta tabela, com a divergência do verificador relatada conforme [workflow.md](workflow.md). Aplique [prose.md](prose.md) preservando significado, IDs e modalidades.
