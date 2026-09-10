---
name: prd
description: 'Cria e refina PRDs (Product Requirements Documents) de features, produtos digitais e iniciativas tecnológicas: problema, usuário-alvo, capability, requisitos com ID, métricas, trade-offs. TRIGGER: "PRD", "product requirements", "documento de requisitos de produto", "especificação de produto", "vamos documentar/especificar essa feature" e equivalentes. NÃO acionar para tech spec, design ou tasks, ADR, notas de reunião, documentação geral ou spec de API sem contexto de produto.'
---

# PRD Writer

## Princípios

- **Método de escrita.** O PRD diz que problema existe, para quem, e que comportamento de negócio o resolve. Como o software é construído é downstream.
- **Linter é feedback para o agente.** O ciclo é: grave o arquivo, rode os scripts, corrija, rode de novo e só então apresente. O PRD nunca carrega resultado de lint, nota de confiança ou marca de validação. Falha de ambiente (parser Mermaid indisponível, fonte que falta) é dita no chat.
- **Aprovação é o commit.** Árvore suja é trabalho em elaboração; arquivo commitado é a versão válida.
- **Precedência.** Para layout, seções, idioma e forma, vale nesta ordem: primeiro o pedido da sessão, depois a convenção do repositório, por último os defaults desta skill.

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

## Workflow

1. **Entender.** Avalie o escopo, a riqueza do contexto, o material de discovery e a necessidade de pesquisa conforme intake.md. Contexto vago pede no máximo três perguntas. Se o usuário recusa discovery, gere o PRD com `[LACUNA]` e siga.
2. **Escrever.** Aplique o que está em writing.md: capability test, lente DDD, uma regra, um lugar, IDs, PRD 0000, diagramas, seções e redação. Grave o arquivo conforme a seção Gravar, abaixo.
3. **Checar.** Rode os scripts da tabela em Scripts. Corrija todo HARD, rode de novo e apresente quando a saída for 0 HARD. São no máximo duas rodadas de correção: se a segunda ainda terminar com HARD, apresente o PRD e liste no chat cada HARD remanescente com o motivo de ele ter sobrado. WARN é você quem julga; se ignorar um de propósito, diga em uma linha no chat. Depois, faça a revisão de cinco itens de Revisão antes de apresentar.

## Gravar

### Caminho e numeração

- O path é `/docs/prd/NNNN-<domain-slug>-<feature-slug>.md`, com slug em kebab-case em inglês e sem prefixo `prd-`.
- `NNNN` é um contador de 4 dígitos, global na pasta, porque dá referência curta ("PRD 0007") e registra a ordem de chegada. Obtenha o número com `seq.py next`, nunca lendo o diretório.
- `0000-<slug>-overview.md` é o PRD 0000 (writing.md, PRD 0000).
- O contador colide quando dois PRs paralelos alocam o mesmo número: renumere o branch que entra depois. `seq.py check` acusa a duplicata.
- Sem repositório, use o mesmo layout sob o diretório de saída que o ambiente indica.

### Edição no lugar

- O PRD se edita no lugar: o diff é a mudança, e o `git log` é autor, data e histórico.
- O PRD não tem campo de status, autor, data, confiança ou aprovação, e não é substituído por um arquivo com número novo.

### Header

O header tem estes elementos, nesta ordem:

1. A primeira linha é `# Título`.
2. Abaixo, uma tabela de duas colunas com um único campo, `Contexto Originário`. O valor é o contexto primário; os contextos afetados vão a Dependências e Riscos. Se DDD não se aplica, use o rótulo equivalente do time (módulo ou área).
3. Depois, a linha de prefixo dos requisitos (writing.md, IDs).
4. Na mesma linha do prefixo, a frase que aponta o PRD 0000, quando ele existe.

O PRD 0000 difere em três pontos: usa `Escopo` no lugar de `Contexto Originário`, não tem linha de prefixo e carrega `<!-- prd: overview -->` na primeira linha, por ser o único PRD que o linter trata de forma diferente. Nenhum outro comentário de máquina entra em PRD algum.

O rótulo do campo segue o idioma do PRD; o nome do contexto preserva o termo do domínio.

```markdown
# Verificação Assíncrona de Documentos

| | |
|---|---|
| **Contexto Originário** | Customer Onboarding; afeta Account Activation |

Prefixo dos requisitos: `ONB`. Propósito da plataforma, mapa de contextos, catálogo de eventos e fluxos: [PRD 0000](0000-platform-overview.md).
```

## Tags, idioma e IDs

### Tags

- Texto sem tag é fato. `[PREMISSA]` marca inferência a validar. `[LACUNA]` marca informação insuficiente.
- Premissa que, se falsa, derruba o PRD é a primeira linha de Perguntas em Aberto, em negrito, com a cláusula "se falsa, …" e como validar.
- Nunca preencha lacuna com especulação sem tag. Rascunho que diz o que falta é entregável; rascunho que esconde o que falta não é (writing.md, Tags).

### Idioma

- O idioma do artefato segue a precedência. Quando ninguém o fixou, é o idioma do input; input ambíguo é português.
- Termo canônico em inglês se traduz quando existe tradução de mesma força e reconhecimento:

| Inglês | Português |
|---|---|
| Given/When/Then | Dado/Quando/Então |
| Functional Requirements | Requisitos Funcionais |
| Non-functional Requirements | Requisitos Não Funcionais |
| Open Questions | Perguntas em Aberto |

- Sem tradução de mesma força, o termo fica em inglês: Factory Pattern, Entity Service Antipattern, Bounded Context, Domain Event, Ubiquitous Language, JTBD, MoSCoW, guardrail, leading/lagging, trade-off.
- Identificadores de domínio (`Offering`, `ReservationBook`), IDs e tags não se traduzem.
- Fora da tabela, o critério é a fonte: traduza quando a tradução do termo aparece na fonte primária do domínio (norma, prospecto, documentação oficial) no idioma do input; se a busca não a encontrar, mantenha o original em inglês.
- O linter aceita o par PT/EN de cada heading como alias.
- O idioma da conversa não muda o do artefato.

### IDs

- FR usa `<PREFIXO>-nn`, com MoSCoW; NFR usa `<PREFIXO>-NFR-nn`. A definição tem a forma `- **OFF-01 (Must)** condição.`; todo o resto do PRD cita o ID. ID nunca é reciclado (writing.md, IDs).
- Uma regra, um lugar: cada regra de negócio existe em um único FR e todo o resto cita o ID (writing.md, Uma regra, um lugar).
- O mesmo princípio de uma regra, um lugar vale para esta skill.

## Revisão antes de apresentar

Depois do linter, dê a cada um dos cinco itens abaixo uma nota de 0 a 100: item abaixo de 90 é corrigido, item com 90 ou mais fica como está. Corrigido o item, repontue só ele: são no máximo duas passadas. Item ainda abaixo de 90 na segunda passada não segura o PRD: apresente e diga em uma linha no chat qual item é, com a nota e o que falta.

1. **Capability test.** A Solução Proposta e cada FR descrevem comportamento observável, não mecanismo (writing.md, Capability test).
2. **Uma regra, um lugar.** Cada regra existe em um único FR e o resto cita o ID. Paráfrase que diverge do FR é a informação, não o ruído (writing.md, Uma regra, um lugar).
3. **Tags.** Toda inferência está marcada `[PREMISSA]` ou `[LACUNA]`; discovery sintetizado tem a origem marcada (intake.md, Material de discovery).
4. **Forma.** Nenhuma seção existe só para cumprir forma (writing.md, Seções):
   - não há "Nenhuma.", bullet inserido para completar contagem nem seção vazia;
   - métrica só entra com guardrail;
   - trade-off tem custo e razão;
   - Ponto de Maior Fragilidade só entra quando há decisão de julgamento sobre fatos conhecidos — corte de escopo, threshold, priorização ou usuário-alvo — e então não é cosmético.
5. **Idioma e headings.** Seguem a precedência; há um conceito por parágrafo (writing.md, Redação).

## Apresentar e iterar

- Ao apresentar, aponte o que existe no PRD: o Ponto de Maior Fragilidade, as `[PREMISSA]` e `[LACUNA]` que bloqueiam decisão e as perguntas críticas.
- Mudança que toca duas ou mais seções ou altera a narrativa regenera o PRD inteiro, porque a consistência entre seções é o que se perde no ajuste pontual. Mudança localizada (um FR, um threshold, uma frase, uma `[LACUNA]`) é ajuste pontual.
- Antes de alterar ou remover um FR, liste quem cita os IDs tocados (writing.md, IDs).

## Scripts

- Os scripts ficam em `scripts/`, no diretório desta skill, e são executados a partir dele com `python` (ou `python3`, onde `python` não existir). O parser Mermaid exige Node.
- `/docs/prd` nos exemplos é caminho relativo à raiz do repositório; passe o caminho real.
- A docstring completa de cada script sai ao rodá-lo sem argumentos.
- `HARD` bloqueia apresentar. `WARN` é heurística com risco de falso-positivo.
- Linter verde é esqueleto conforme, não PRD bom.

| Comando | Quando | O que faz |
|---|---|---|
| `python scripts/seq.py next /docs/prd --slug <domain-slug>-<feature-slug>` | Antes de criar o arquivo | Imprime `NNNN-<slug>` com o próximo número; recusa alocar quando há número duplicado |
| `python scripts/seq.py check /docs/prd` | Antes de apresentar | Acusa número duplicado |
| `python scripts/lint_prd.py <arquivo.md \| /docs/prd>` | Antes de apresentar | Verifica seções obrigatórias, prefixo, IDs entre PRDs, links locais que resolvem e o PRD 0000 |
| `python scripts/lint_mermaid.py <arquivo.md \| dir>` | Antes de apresentar PRD com diagrama | Faz o parse de todo bloco Mermaid. Bloco que não passou, fence sem fechamento ou parser indisponível (exit 3) é HARD, porque diagrama não validado é diagrama não entregue. `--self-test` prova a extração e o parser; `--setup` instala o parser com `npm ci`, é o único modo com rede e só roda com autorização |

## Exemplo

PRD no formato-alvo em [references/example.md](references/example.md). Leia a seção correspondente quando a coluna Forma da tabela (writing.md, Seções) não bastar para instanciá-la; não é template a copiar.
