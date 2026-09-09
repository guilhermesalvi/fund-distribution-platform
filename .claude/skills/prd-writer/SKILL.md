---
name: prd-writer
description: 'Cria e refina PRDs (Product Requirements Documents) de features, produtos digitais e iniciativas tecnológicas: problema, usuário-alvo, capability, requisitos com ID, métricas, trade-offs. TRIGGER: "PRD", "product requirements", "documento de requisitos de produto", "especificação de produto", "vamos documentar/especificar essa feature" e equivalentes. NÃO acionar para tech spec, design ou tasks, ADR, notas de reunião, documentação geral ou spec de API sem contexto de produto.'
---

# PRD Writer

Método de escrita: o PRD diz que problema existe, para quem, e que comportamento de negócio o resolve; como o software é construído é downstream. Linter é feedback para o agente: gravar → rodar → corrigir → rodar de novo → apresentar; o PRD nunca carrega resultado de lint, nota de confiança ou marca de validação, e falha de ambiente (parser Mermaid indisponível, fonte que falta) é dita no chat. Aprovação é o commit: árvore suja é trabalho em elaboração; arquivo commitado é a versão válida. Precedência: pedido da sessão > convenção do repositório > defaults desta skill, para layout, seções, idioma e forma.

## Quando é PRD

Feature, produto digital ou iniciativa tecnológica com impacto funcional para um usuário. Iniciativa técnica com impacto funcional real ganha PRD focado no impacto, não na implementação.

| Não é PRD | Artefato certo |
|---|---|
| Dívida técnica, refactor, modernização sem impacto funcional novo | ADR, doc de dívida técnica, plano de refactor |
| Decisão arquitetural | ADR |
| Processo interno sem entrega de software | Runbook, doc de processo |
| Contratos de API, módulos, plano de tarefas, design de componente | Tech spec, design doc |

Pedido que é PRD mas chega enquadrado como implementação, tela ou CRUD: reenquadre pelo problema (intake.md, Escopo problemático). "PRD do que já existe" e plataforma, infra, SDK ou API como produto: modes.md.

## Workflow

1. **Entender.** Escopo, riqueza do contexto, material de discovery e pesquisa: intake.md. Contexto vago pede no máximo três perguntas; recusa de discovery gera PRD com `[LACUNA]` e segue.
2. **Escrever.** Capability test, lente DDD, uma regra um lugar, IDs, PRD 0000, diagramas, seções e redação: writing.md. Grave conforme Gravar, abaixo.
3. **Checar.** Rode os scripts da tabela Scripts; corrija todo HARD e rode de novo; WARN você julga, e se ignorar de propósito diz em uma linha no chat. Depois, a revisão de cinco itens.

## Gravar

- Path: `/docs/prd/NNNN-<domain-slug>-<feature-slug>.md`, kebab-case em inglês, sem prefixo `prd-`. `NNNN` é contador de 4 dígitos global na pasta, porque dá referência curta ("PRD 0007") e ordem de chegada; obtenha-o com `seq.py next`, nunca lendo o diretório. `0000-<slug>-overview.md` é o PRD 0000 (writing.md, PRD 0000). Contador colide em PR paralelo: renumere o branch que entra depois; `seq.py check` acusa a duplicata. Sem repositório, use o mesmo layout sob o diretório de saída que o ambiente indica.
- PRD se edita no lugar: o diff é a mudança; o `git log` é autor, data e histórico. Nenhum campo de status, autor, data, confiança ou aprovação; não há substituição por número novo.
- Header: primeira linha `# Título`; abaixo, tabela de duas colunas com um único campo, `Contexto Originário` (contexto primário; afetados vão a Dependências e Riscos; rótulo equivalente, módulo ou área, se DDD não se aplica); depois a linha de prefixo (writing.md, IDs), seguida da frase que aponta o PRD 0000 quando ele existe. O PRD 0000 usa `Escopo` no lugar de Contexto Originário, não tem linha de prefixo e carrega `<!-- prd: overview -->` na primeira linha, por ser o único que o linter trata diferente; nenhum outro comentário de máquina. O rótulo segue o idioma do PRD; o nome do contexto preserva o termo do domínio.

```
# Verificação Assíncrona de Documentos

| | |
|---|---|
| **Contexto Originário** | Customer Onboarding; afeta Account Activation |

Prefixo dos requisitos: `ONB`. Propósito da plataforma, mapa de contextos, catálogo de eventos e fluxos: [PRD 0000](0000-platform-overview.md).
```

## Tags, idioma e IDs

- **Tags.** Texto sem tag é fato; `[PREMISSA]` é inferência a validar; `[LACUNA]` é informação insuficiente. Premissa que, se falsa, derruba o PRD é a primeira linha de Perguntas em Aberto, em negrito, com "se falsa, …" e como validar. Nunca preencha lacuna com especulação sem tag; rascunho que diz o que falta é entregável, rascunho que esconde não é (writing.md, Tags).
- **Idioma.** O artefato segue a precedência; quando ninguém fixou, é o idioma do input, e input ambíguo é português. Termo canônico em inglês com tradução de mesma força e reconhecimento se traduz: Given/When/Then → Dado/Quando/Então, Functional Requirements → Requisitos Funcionais, Non-functional Requirements → Requisitos Não Funcionais, Open Questions → Perguntas em Aberto. Sem tradução de mesma força fica em inglês: Factory Pattern, Entity Service Antipattern, Bounded Context, Domain Event, Ubiquitous Language, JTBD, MoSCoW, guardrail, leading/lagging, trade-off. Identificadores de domínio (`Offering`, `ReservationBook`), IDs e tags não se traduzem. Critério: traduz quando o leitor do idioma do input reconhece a tradução tão rápido quanto o original. O linter aceita o par PT/EN de cada heading como alias. O idioma da conversa não muda o do artefato.
- **IDs.** `<PREFIXO>-nn` para FR, com MoSCoW, e `<PREFIXO>-NFR-nn` para NFR; definidos como `- **OFF-01 (Must)** condição.` e citados pelo ID em todo o resto; nunca reciclados (writing.md, IDs). Uma regra, um lugar: cada regra de negócio existe em um FR e todo o resto cita o ID (writing.md, Uma regra, um lugar). A mesma regra vale para esta skill.

## Revisão antes de apresentar

Depois do linter, cinco itens; falha em qualquer um exige ajuste antes de apresentar.

1. Capability test na Solução Proposta e em cada FR: comportamento observável, não mecanismo (writing.md, Capability test).
2. Cada regra existe em um único FR e o resto cita o ID; paráfrase que diverge do FR é a informação, não o ruído (writing.md, Uma regra, um lugar).
3. Toda inferência marcada `[PREMISSA]` ou `[LACUNA]`; discovery sintetizado com origem marcada (intake.md, Material de discovery).
4. Nenhuma seção existe só para cumprir forma: sem "Nenhuma.", sem bullet de contagem, sem seção vazia; métrica só com guardrail; trade-off com custo e razão; Ponto de Maior Fragilidade só quando há decisão que um revisor cético atacaria, e então não cosmético (writing.md, Seções).
5. Idioma e headings conforme a precedência; um conceito por parágrafo (writing.md, Redação).

## Apresentar e iterar

Ao apresentar, aponte o que existe: o Ponto de Maior Fragilidade, as `[PREMISSA]` e `[LACUNA]` que bloqueiam decisão, as perguntas críticas. Mudança que cruza seções ou a narrativa regenera o PRD inteiro, porque a consistência entre seções é o que se perde no ajuste pontual; mudança localizada (um FR, um threshold, uma frase, uma `[LACUNA]`) é ajuste pontual; em dúvida, regenere. Antes de alterar ou remover um FR, liste quem cita os IDs tocados (writing.md, IDs).

## Scripts

Ficam em `scripts/` no diretório desta skill e são executados a partir dele, com `python` (ou `python3` onde `python` não existir); o parser Mermaid exige Node. `/docs/prd` nos exemplos é caminho relativo à raiz do repositório: passe o caminho real. A docstring completa de cada script sai ao rodá-lo sem argumentos. `HARD` bloqueia apresentar; `WARN` é heurística com risco de falso-positivo. Linter verde é esqueleto conforme, não PRD bom.

| Comando | Quando |
|---|---|
| `python scripts/seq.py next /docs/prd --slug <domain-slug>-<feature-slug>` | Antes de criar o arquivo: imprime `NNNN-<slug>` com o próximo número; recusa sobre número duplicado |
| `python scripts/seq.py check /docs/prd` | Antes de apresentar: número duplicado |
| `python scripts/lint_prd.py <arquivo.md \| /docs/prd>` | Antes de apresentar: seções obrigatórias, prefixo, IDs entre PRDs, links locais que resolvem, PRD 0000 |
| `python scripts/lint_mermaid.py <arquivo.md \| dir>` | Antes de apresentar PRD com diagrama: parse de todo bloco Mermaid; bloco que não passou, fence sem fechamento ou parser indisponível (exit 3) é HARD, porque diagrama não validado é diagrama não entregue; `--self-test` prova extração e parser; `--setup` instala o parser (`npm ci`, único modo com rede, só com autorização) |

## Exemplo

PRD no formato-alvo em [references/example.md](references/example.md). Leia quando houver dúvida sobre a forma de uma seção; não é template a copiar.
