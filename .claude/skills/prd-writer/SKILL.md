---
name: prd-writer
description: 'Cria e refina PRDs (Product Requirements Documents) de features, produtos digitais e iniciativas tecnológicas: problema, usuário-alvo, capability, requisitos com ID, métricas, trade-offs. TRIGGER: "PRD", "product requirements", "documento de requisitos de produto", "especificação de produto", "vamos documentar/especificar essa feature" e equivalentes. NÃO acionar para tech spec, design ou tasks (skill spec-driven), ADR, notas de reunião, documentação geral ou spec de API sem contexto de produto.'
---

# PRD Writer

Este arquivo é o roteador: quando usar, o workflow e onde vive cada regra. Regra detalhada vive em `references/`, em um único lugar; os demais lugares citam.

## Quando usar

Feature, produto digital ou iniciativa tecnológica com impacto funcional para um usuário. Iniciativa técnica com impacto funcional real → PRD focado no impacto, não na implementação.

| Não é PRD | Artefato certo |
|---|---|
| Dívida técnica, refactor, modernização sem impacto funcional novo | ADR, doc de dívida técnica, plano de refactor |
| Decisão arquitetural | ADR |
| Processo interno sem entrega de software | Runbook, doc de processo |
| Spec de implementação (contratos de API, módulos, plano de tarefas, design de componente) | Tech spec, design doc (skill `spec-driven`) |

Pedido que é PRD mas chega enquadrado como implementação, tela ou CRUD: reenquadre pelo problema (intake.md, Escopo problemático).

## Princípios

- Precedência: pedido do usuário na sessão > convenção do repositório (CLAUDE.md, rules, docs existentes) > instruções pessoais do usuário (CLAUDE.md global) > defaults desta skill, para layout, seções, idioma e forma. A skill preenche o que ninguém fixou e diz quando um default foi substituído; seção default dispensada por convenção do projeto é declarada no comentário de tier (`omit:`, output.md, Header), e o linter só silencia WARN, nunca HARD.
- Idioma do artefato pela mesma precedência; sem nada fixado, o do input, português quando ambíguo. Identificadores de domínio, IDs de requisito e tags de máquina não se traduzem. O idioma da conversa não muda o do artefato.
- Falha é entregável: linter com HARD que você não consegue resolver, parser Mermaid indisponível ou fonte que falta se apresentam como relatório de falha com o que falta, nunca como PRD aprovável.
- Rascunho útil vale mais que certeza forjada: Status, Confiança, `[LACUNA]`, `[PREMISSA-CRÍTICA]` e Perguntas em Aberto dizem juntos o que falta (output.md, Header; writing.md, Convenção de confiança). Não resolva incerteza artificialmente para entregar.
- O PRD vive no problem space. O capability test (writing.md, Lente DDD) é o critério de qualidade mais importante desta skill.
- Toda afirmação carrega a origem pela convenção de confiança (writing.md).
- Uma regra, um lugar: cada regra de negócio existe em um FR e todo o resto cita o ID (writing.md, Uma regra, um lugar). A mesma regra vale para esta skill.
- Contribua conhecimento de domínio reconhecível (finance, saúde, e-commerce, logística, compliance) e pesquise as lacunas; não espere pelo usuário.

## Workflow

| Passo | O que fazer | Regras em |
|---|---|---|
| 1. Avalie o input | Encaixe, escopo, material de discovery, ontologia a partir de transcrições, riqueza do contexto; modos reverse PRD e plataforma/infra | [intake.md](references/intake.md) |
| 2. Pesquise | Busca web para benchmarks, comportamento e regulação; cite fontes | [intake.md](references/intake.md), Pesquisa |
| 3. Declare o tier | Simples, média ou complexa; na dúvida, o maior | [writing.md](references/writing.md), Tier |
| 4. Redija | Lente DDD, IDs, PRD 0000, diagramas, seções e sua forma, Ponto de Maior Fragilidade, redação | [writing.md](references/writing.md) |
| 5. Grave | Path via `seq.py next`, PRD plano ou em pasta, header, comentário de tier, `.docx` | [output.md](references/output.md) |
| 6. Revise | Scripts (nenhum HARD, nenhum bloco Mermaid sem parse), passada "uma regra, um lugar", três passadas de julgamento | [review.md](references/review.md) |
| 7. Apresente e itere | Abaixo | — |

Leia a referência inteira antes de executar o passo; as regras dependem umas das outras.

**Apresente e itere.** Depois de apresentar, aponte o Ponto de Maior Fragilidade, as `[PREMISSA-CRÍTICA]` a validar, as `[PREMISSA]` e `[LACUNA]` que bloqueiam decisão e as perguntas críticas, com especificidade. Mudança que afeta várias seções ou a narrativa → regenere o PRD inteiro, porque a consistência entre seções é o que se perde no ajuste pontual. Mudança localizada (um FR, um threshold, uma frase, uma `[LACUNA]`) → ajuste pontual. Em dúvida, regenere.

O Status só passa a Aprovado por decisão do usuário (output.md, Header); é o estado que a skill `spec-driven` consome para abrir uma spec. PRD que já tem spec derivada em `/docs/specs`: antes de alterar ou remover um FR, liste as specs que citam os IDs tocados (writing.md, IDs).

## Scripts

Ficam em `scripts/` no diretório desta skill; rode-os a partir dele (`python`, ou `python3` onde `python` não existir; o parser Mermaid exige Node). `/docs/prd` nos exemplos é caminho relativo à raiz do repositório: passe o caminho real. Semântica de HARD e WARN em review.md, Passada mecânica.

| Comando | Quando |
|---|---|
| `python scripts/seq.py next /docs/prd --domain <domain-slug> --slug <feature-slug>` | Antes de criar o arquivo: valida a sequência e imprime o path no layout do repositório; `--overview` aloca o PRD 0000 |
| `python scripts/seq.py check /docs/prd` | Antes de apresentar: sequência, slugs, substituições recíprocas |
| `python scripts/lint_prd.py <arquivo.md \| /docs/prd>` | Antes de apresentar: esqueleto, header (Status, Autor, Data), IDs entre PRDs, fatos duplicados, substituição, parse dos blocos Mermaid |
| `python scripts/lint_mermaid.py <arquivo.md \| dir>` | Isolado, quando só um diagrama mudou; `--self-test` prova extração e parser; `--setup` instala o parser (`npm ci`, único modo com rede, só com autorização); exit 3 = parser indisponível |

## Exemplo

PRD tier complexa no formato-alvo em [references/example.md](references/example.md). Leia quando houver dúvida sobre a forma de uma seção; não é template a copiar.
