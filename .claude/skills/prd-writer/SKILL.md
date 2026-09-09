---
name: prd-writer
description: 'Cria e refina PRDs (Product Requirements Documents) de features, produtos digitais e iniciativas tecnológicas: problema, usuário-alvo, capability, requisitos com ID, métricas, trade-offs. TRIGGER: "PRD", "product requirements", "documento de requisitos de produto", "especificação de produto", "vamos documentar/especificar essa feature" e equivalentes. NÃO acionar para tech spec, design ou tasks, ADR, notas de reunião, documentação geral ou spec de API sem contexto de produto.'
---

# PRD Writer

Este arquivo é o roteador: quando usar, o workflow e onde vive cada regra. Regra detalhada vive em `references/`, em um único lugar; os demais lugares citam.

## Quando usar

Feature, produto digital ou iniciativa tecnológica com impacto funcional para um usuário. Iniciativa técnica com impacto funcional real ganha PRD focado no impacto, não na implementação.

| Não é PRD | Artefato certo |
|---|---|
| Dívida técnica, refactor, modernização sem impacto funcional novo | ADR, doc de dívida técnica, plano de refactor |
| Decisão arquitetural | ADR |
| Processo interno sem entrega de software | Runbook, doc de processo |
| Spec de implementação (contratos de API, módulos, plano de tarefas, design de componente) | Tech spec, design doc |

Pedido que é PRD mas chega enquadrado como implementação, tela ou CRUD: reenquadre pelo problema (intake.md, Escopo problemático).

## Princípios

- **Precedência.** Quando pedido, convenção e defaults discordam sobre layout, seções, idioma ou forma, vale nesta ordem: primeiro o que o usuário pediu nesta sessão; depois a convenção do repositório (CLAUDE.md, rules, docs existentes); depois as instruções pessoais do usuário (CLAUDE.md global); por último os defaults desta skill. A skill preenche só o que ninguém fixou e avisa quando substituiu um default.
- **Idioma.** O artefato segue a mesma precedência; quando ninguém fixou, é o idioma do input, e input ambíguo é português. Termo canônico em inglês com tradução de mesma força e reconhecimento se traduz: Given/When/Then → Dado/Quando/Então, Functional Requirements → Requisitos Funcionais, Non-functional Requirements → Requisitos Não Funcionais, Open Questions → Perguntas em Aberto. Sem tradução de mesma força fica em inglês: Factory Pattern, Entity Service Antipattern, Bounded Context, Domain Event, Ubiquitous Language, JTBD, MoSCoW, guardrail, leading/lagging, trade-off. Identificadores de domínio (`Offering`, `ReservationBook`), IDs e tags não se traduzem. Critério: traduz quando o leitor do idioma do input reconhece a tradução tão rápido quanto o original. O linter aceita o par PT/EN de cada heading como alias. O idioma da conversa não muda o do artefato.
- Falha é entregável: linter com HARD que você não consegue resolver, parser Mermaid indisponível ou fonte que falta se apresentam como relatório de falha com o que falta, nunca como PRD aprovável.
- Rascunho útil vale mais que certeza forjada: `[LACUNA]`, `[PREMISSA]` e Perguntas em Aberto dizem o que falta (writing.md, Tags). Não resolva incerteza artificialmente para entregar.
- O PRD vive no problem space. O capability test (writing.md, Lente DDD) é o critério de qualidade mais importante desta skill.
- Texto sem tag é fato; inferência é `[PREMISSA]`, informação que falta é `[LACUNA]` (writing.md, Tags).
- Uma regra, um lugar: cada regra de negócio existe em um FR e todo o resto cita o ID (writing.md, Uma regra, um lugar). A mesma regra vale para esta skill.
- Contribua conhecimento de domínio reconhecível (finance, saúde, e-commerce, logística, compliance) e pesquise as lacunas; não espere pelo usuário.

## Workflow

| Passo | O que fazer | Regras em |
|---|---|---|
| 1. Avalie o input | Encaixe, escopo, material de discovery, riqueza do contexto | [intake.md](references/intake.md); reverse PRD e plataforma/API em [modes.md](references/modes.md) |
| 2. Pesquise | Busca web para benchmarks, comportamento e regulação; cite fontes | [intake.md](references/intake.md), Pesquisa |
| 3. Redija | Capability test, lente DDD, IDs, PRD 0000, diagramas, seções e sua forma, redação | [writing.md](references/writing.md) |
| 4. Grave | Path via `seq.py next` e header | Gravar, abaixo |
| 5. Revise | Scripts (nenhum HARD no `lint_prd.py`, nenhum bloco Mermaid sem parse no `lint_mermaid.py`), passada "uma regra, um lugar", três passadas de julgamento | [review.md](references/review.md) |
| 6. Apresente e itere | Abaixo | — |

Leia a referência inteira antes de executar o passo; as regras dependem umas das outras.

**Apresente e itere.** Depois de apresentar, aponte o Ponto de Maior Fragilidade, as `[PREMISSA]` e `[LACUNA]` que bloqueiam decisão e as perguntas críticas, com especificidade. Quando a mudança afeta várias seções ou a narrativa, regenere o PRD inteiro, porque a consistência entre seções é o que se perde no ajuste pontual. Quando a mudança é localizada (um FR, um threshold, uma frase, uma `[LACUNA]`), faça o ajuste pontual. Em dúvida, regenere.

Antes de alterar ou remover um FR, liste quem cita os IDs tocados (writing.md, IDs).

## Gravar

- Path: `/docs/prd/NNNN-<domain-slug>-<feature-slug>.md`, kebab-case em inglês, sem prefixo `prd-`. `NNNN` é contador de 4 dígitos global na pasta, porque dá referência curta ("PRD 0007") e ordem de chegada; obtenha-o com `seq.py next`, nunca lendo o diretório. `0000-<slug>-overview.md` é o PRD 0000 (writing.md, PRD 0000). Contador colide em PR paralelo: renumere o branch que entra depois; `seq.py check` acusa a duplicata. Sem repositório, use o mesmo layout sob o diretório de saída que o ambiente indica.
- PRD se edita no lugar: o diff é a mudança; o `git log` é autor, data e histórico. Aprovação é o commit: árvore suja é trabalho em elaboração; arquivo commitado é a versão válida. Nenhum campo de status, autor, data, confiança ou aprovação; não há substituição por número novo.
- Header: primeira linha `# Título`; abaixo, tabela de duas colunas com um único campo, `Contexto Originário` (contexto primário; afetados vão a Dependências e Riscos; rótulo equivalente, módulo ou área, se DDD não se aplica); depois a linha de prefixo (writing.md, IDs), seguida da frase que aponta o PRD 0000 quando ele existe. O PRD 0000 usa `Escopo` no lugar de Contexto Originário, não tem linha de prefixo e carrega `<!-- prd: overview -->` na primeira linha, por ser o único que o linter trata diferente; nenhum outro comentário de máquina. O rótulo segue o idioma do PRD; o nome do contexto preserva o termo do domínio.

```
# Verificação Assíncrona de Documentos

| | |
|---|---|
| **Contexto Originário** | Customer Onboarding; afeta Account Activation |

Prefixo dos requisitos: `ONB`. Propósito da plataforma, mapa de contextos, catálogo de eventos e fluxos: [PRD 0000](0000-platform-overview.md).
```

## Scripts

Ficam em `scripts/` no diretório desta skill e são executados a partir dele, com `python` (ou `python3` onde `python` não existir); o parser Mermaid exige Node. `/docs/prd` nos exemplos é caminho relativo à raiz do repositório: passe o caminho real. Semântica de HARD e WARN em review.md, Passada mecânica.

| Comando | Quando |
|---|---|
| `python scripts/seq.py next /docs/prd --slug <domain-slug>-<feature-slug>` | Antes de criar o arquivo: imprime `NNNN-<slug>` com o próximo número; recusa sobre número duplicado |
| `python scripts/seq.py check /docs/prd` | Antes de apresentar: número duplicado |
| `python scripts/lint_prd.py <arquivo.md \| /docs/prd>` | Antes de apresentar: seções obrigatórias, prefixo, IDs entre PRDs, links locais que resolvem, PRD 0000 |
| `python scripts/lint_mermaid.py <arquivo.md \| dir>` | Antes de apresentar PRD com diagrama: parse de todo bloco Mermaid; `--self-test` prova extração e parser; `--setup` instala o parser (`npm ci`, único modo com rede, só com autorização); exit 3 = parser indisponível |

## Exemplo

PRD no formato-alvo em [references/example.md](references/example.md). Leia quando houver dúvida sobre a forma de uma seção; não é template a copiar.
