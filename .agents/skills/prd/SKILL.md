---
name: prd
description: 'Cria e refina PRDs (Product Requirements Documents) de features, produtos digitais e iniciativas tecnológicas: problema, usuário-alvo, capability, requisitos com ID, métricas, trade-offs. TRIGGER: "PRD", "product requirements", "documento de requisitos de produto", "especificação de produto", "vamos documentar/especificar essa feature" e equivalentes. NÃO acionar para tech spec, design ou tasks, ADR, notas de reunião, documentação geral ou spec de API sem contexto de produto.'
---

# PRD Writer

## Princípios

- **Método de escrita.** O PRD diz que problema existe, para quem, e que comportamento de negócio o resolve. Como o software é construído é downstream.
- **Linter é feedback para o agente.** HARD se corrige antes de apresentar e o que sobrar após o teto é listado no chat, tudo conforme o passo Checar (Workflow). O PRD nunca carrega resultado de lint, nota de confiança ou marca de validação.
- **Aprovação é o commit.** Árvore suja é trabalho em elaboração; arquivo commitado é a versão válida.
- **Precedência.** Para layout, seções, idioma e forma, vale nesta ordem: primeiro o pedido da sessão, depois a convenção do repositório, por último os defaults desta skill. HARD que decorre de um dos dois primeiros degraus é mantido, não corrigido, conforme o passo Checar (Workflow).

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

1. **Entender.** Avalie o escopo, a riqueza do contexto, o material de discovery e a necessidade de pesquisa conforme intake.md; é lá que estão o teto de perguntas e o que fazer quando o usuário recusa discovery.
2. **Escrever.** Aplique o que está em writing.md: capability test, lente DDD, uma regra, um lugar, IDs, PRD 0000, diagramas, seções e redação. Grave o arquivo conforme a seção Gravar, abaixo.
3. **Checar.** Rode os scripts da tabela em Scripts e siga este ciclo:
   - corrija todo HARD, rode de novo e apresente quando a saída for 0 HARD;
   - são no máximo duas rodadas de correção: se a segunda ainda terminar com HARD, apresente o PRD e liste no chat cada HARD remanescente com o motivo de ele ter sobrado;
   - HARD que decorre do pedido da sessão ou da convenção do repositório — os dois primeiros degraus da Precedência — não se corrige nem conta como rodada: diga no chat qual HARD é e qual dos dois o mantém, com as palavras "mantido por pedido" ou "mantido por convenção". Pedido é o da sessão que nomeia literalmente a seção, o campo ou a forma de onde o HARD sai ("inclua uma seção Plano de Rollout"); convenção é forma presente em três ou mais PRDs commitados da pasta — os commitados são os que `git ls-files` lista, e a forma se confere neles — ou escrita no AGENTS.md do repositório;
   - script que não roda por falha de ambiente (Python ou Node ausentes; exit 3 de `lint_mermaid.py` por parser ausente) não é rodada de correção: é bloqueio de ambiente, dito no chat, e o PRD é apresentado sem essa verificação. No exit 3, a ordem é: peça a autorização de `--setup` uma vez, antes de apresentar; autorizada, rode `--setup` e o linter de novo e trate a saída como qualquer outra; recusada ou sem resposta, apresente sem essa verificação. Exit 2 é erro de uso (caminho, opção ou nome de arquivo fora do padrão) e se corrige como HARD; exit 1 de `seq.py` (slug inválido ou número duplicado) também é HARD;
   - cada WARN termina de uma de duas formas: corrigido, ou mantido com uma linha de razão no chat;
   - depois, faça a revisão de cinco itens de Revisão antes de apresentar; se ela alterou o PRD, rode os scripts uma vez mais, fora do teto: HARD nessa execução é corrigido uma vez e, se persistir, listado no chat como os demais.

## Gravar

### Caminho e numeração

- O path é `/docs/prd/NNNN-<domain-slug>-<feature-slug>.md`, com slug em kebab-case em inglês e sem prefixo `prd-`.
- `NNNN` é um contador de 4 dígitos, global na pasta, porque dá referência curta ("PRD 0007") e registra a ordem de chegada. Obtenha o número com `seq.py next`, nunca lendo o diretório; a exceção é o PRD 0000, cujo número é fixo e não passa pelo contador.
- `0000-<slug>-overview.md` é o PRD 0000 (writing.md, PRD 0000); `lint_prd.py` acusa como HARD a visão geral gravada em qualquer outro número.
- O contador colide quando dois PRs paralelos alocam o mesmo número; `seq.py check` acusa a duplicata. Renumere o PRD do branch cujo merge acontece depois: mova o arquivo para um nome sem o prefixo `NNNN-` (o `next` recusa alocar enquanto a duplicata existe), rode `seq.py next /docs/prd --slug <domain-slug>-<feature-slug>`, mova o arquivo para o nome devolvido e rode `seq.py check` de novo.
- Sem repositório, use o mesmo layout sob o diretório de trabalho atual e diga no chat o caminho gravado.

### Edição no lugar

- O PRD se edita no lugar: o diff é a mudança, e o `git log` é autor, data e histórico.
- O PRD não tem campo de status, autor, data, confiança ou aprovação, e não é substituído por um arquivo com número novo.

### Header

O header tem estes elementos, nesta ordem:

1. A primeira linha é `# Título`.
2. Abaixo, uma tabela de duas colunas com um único campo, `Contexto Originário` (`Originating Context` em PRD em inglês). O valor é o contexto primário, seguido de `; afeta <contextos>` quando houver; o impacto em cada contexto afetado vai a Dependências e Riscos. Se DDD não se aplica, o rótulo é `Módulo` (`Module`) ou `Área` (`Area`); o linter aceita só esses três, e no PRD 0000 só `Escopo` (`Scope`).
3. Depois, a linha de prefixo dos requisitos (writing.md, IDs). O rótulo é `Prefixo dos requisitos:` em PRD em português e `Requirement prefix:` em PRD em inglês — são essas duas formas que se escrevem, e o linter as reconhece (docstring de `lint_prd.py`).
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

- As tags, suas definições e as regras de uso, inclusive o lugar fixo da premissa que derruba o PRD, estão em writing.md, Tags.

### Idioma

- **O PRD é escrito em português ou em inglês.** São os dois idiomas que o ferramental cobre: `--lang` aceita `pt` ou `en`, e a tabela de seções dá o nome de cada seção nos dois, o em português e, entre parênteses, o em inglês (writing.md, Seções). A precedência escolhe entre esses dois e não abre um terceiro.
- Entre os dois, o idioma do artefato segue a precedência. Quando ninguém o fixou, é o idioma do material recebido (com material em mais de um idioma, o do documento que o pedido cita primeiro ou, sem citação, o do primeiro anexo); sem material, o idioma do pedido. Uma vez fixado, pedido explícito de idioma na sessão é precedência e o muda; mensagem em outro idioma sem esse pedido não muda.
- Material, pedido ou pedido explícito de idioma fora desses dois: o PRD sai em inglês, e a apresentação abre com uma linha dizendo que ele está em inglês porque a skill escreve em português ou inglês. O termo de domínio continua no original nos dois casos (writing.md, Ubiquitous Language).
- Termo canônico em inglês se traduz quando existe tradução de mesma força e reconhecimento:

| Inglês | Português |
|---|---|
| Given/When/Then | Dado/Quando/Então |
| Functional Requirements | Requisitos Funcionais |
| Non-functional Requirements | Requisitos Não Funcionais |
| Open Questions | Perguntas em Aberto |

- Sem tradução de mesma força, o termo fica em inglês: Factory Pattern, Entity Service Antipattern, Bounded Context, Domain Event, Ubiquitous Language, JTBD, MoSCoW, guardrail, leading/lagging, trade-off.
- Identificadores de domínio (`Offering`, `ReservationBook`), IDs e tags não se traduzem.
- Fora das duas listas, traduza o termo só quando a tradução já aparece no material recebido ou no PRD 0000; caso contrário, mantenha o original em inglês.
- O linter reconhece o par PT/EN de cada heading como alias; qual dos dois vale neste PRD é o `--lang` da tabela de Scripts, que acusa o heading do outro idioma como WARN.

### IDs

- Formato, definição, remoção e enumerações dos IDs estão em writing.md, IDs; cada regra de negócio existe em um único FR e todo o resto cita o ID (writing.md, Uma regra, um lugar).
- O mesmo princípio vale para esta skill: cada regra vive em uma referência e este arquivo a cita.

## Revisão antes de apresentar

Depois do linter, para cada um dos cinco itens abaixo:

- percorra todas as seções do PRD e dê ao item a nota 100 menos 20 por ocorrência encontrada (mínimo 0); uma ocorrência já derruba o item, e a nota existe para registrar quantas;
- item abaixo de 90 é corrigido; item com 90 ou mais fica como está;
- corrigido o item, repontue só ele: são no máximo duas passadas;
- item ainda abaixo de 90 na segunda passada não segura o PRD: apresente e diga em uma linha no chat qual item é, com a nota e o que falta.

1. **Capability test.** A Solução Proposta, a frase de solução do Resumo Executivo e cada FR descrevem comportamento observável, não mecanismo (writing.md, Capability test); em reverse PRD o alcance é outro, e quem o fixa é uma fonte só (modes.md, Modo reverse PRD). Os termos de mecanismo da lista do script não se contam a olho: `lint_prd.py`, na forma da tabela de Scripts, acusa cada um como WARN em Solução Proposta e Requisitos Funcionais, e no alcance alargado quando roda com `--reverse`; termo cujo WARN você manteve com uma linha de razão no passo Checar (Workflow) não é ocorrência aqui. A leitura cobre o que a lista do script não tem e a frase de solução do Resumo Executivo.
2. **Uma regra, um lugar.** Cada regra existe em um único FR e o resto cita o ID. Paráfrase que diverge do FR não se resolve aqui: vira `[LACUNA]` em Perguntas em Aberto (writing.md, Uma regra, um lugar).
3. **Tags.** Toda inferência está marcada `[PREMISSA]` ou `[LACUNA]`; discovery sintetizado tem a origem marcada (intake.md, Material de discovery).
4. **Forma.** Nenhuma seção existe só para cumprir forma (writing.md, Seções). O que é forma verificável já é HARD ou WARN de `lint_prd.py` (docstring) — inclusive a seção `##` fora da tabela, que é HARD, então o conjunto de headings também não se confere a olho; aqui sobram os dois que só a leitura pega:
   - bullet inserido para completar contagem, isto é, bullet cuja remoção não tira informação nenhuma do PRD; bullet que uma regra de writing.md exige, como o guardrail de Métricas de Sucesso marcado `[PREMISSA]` (writing.md, Seções), nunca é ocorrência;
   - Ponto de Maior Fragilidade sem decisão de julgamento sobre fatos conhecidos (corte de escopo, threshold, priorização ou usuário-alvo), isto é, cosmético.
5. **Idioma e headings.** Seguem a precedência; há um conceito por parágrafo (writing.md, Redação). Ocorrência: heading fora do par PT/EN do idioma fixado, parágrafo com dois assuntos, ou dois parágrafos adjacentes sobre o mesmo ponto. Os headings não se contam a olho: `lint_prd.py --lang`, na forma da tabela de Scripts, acusa cada um como WARN; heading cujo WARN você manteve com uma linha de razão no passo Checar (Workflow) não é ocorrência aqui, porque a razão já o fechou. A leitura cobre só os dois casos de parágrafo.

## Apresentar e iterar

- Ao apresentar, aponte o que existe no PRD: o Ponto de Maior Fragilidade e cada linha de Perguntas em Aberto — o conjunto é o que a coluna "Entra quando" da tabela de Seções fez entrar na seção (writing.md, Seções), e não há segundo recorte. O recorte rege o que se aponta do PRD e nada além dele: os três acréscimos que intake.md manda dizer neste mesmo momento — quem é o usuário-alvo e a lista do que falta preencher (intake.md, Casos de borda), e a busca que ficou pendente (intake.md, Pesquisa) — não saem do PRD, então o recorte não os alcança e cada um entra quando a sua condição se cumpre.
- Mudança pedida pelo usuário que toca duas ou mais seções, ou que altera Contexto e Problema ou Solução Proposta, regenera o PRD inteiro, porque a consistência entre seções é o que se perde no ajuste pontual. Mudança localizada (um FR, um threshold, uma frase, uma `[LACUNA]`) é ajuste pontual. Regeneração ou ajuste pedido pelo usuário reinicia o passo Checar com os tetos zerados.
- Antes de alterar ou remover um FR, liste quem cita os IDs tocados (writing.md, IDs).

## Scripts

- Os scripts ficam na pasta `scripts/` do diretório desta skill e são chamados pelo caminho completo, `python <skill-dir>/scripts/<nome>.py` (ou `python3`, onde `python` não existir), de qualquer diretório de trabalho. `<skill-dir>` é o diretório que contém este SKILL.md. O parser Mermaid exige Node.
- `/docs/prd` nos exemplos é caminho relativo à raiz do repositório; passe o caminho real.
- A docstring completa de cada script sai ao rodá-lo sem argumentos.
- O ciclo de correção, o teto e as exceções estão no passo Checar (Workflow). `WARN` é heurística com risco de falso-positivo.
- Linter verde é esqueleto conforme, não PRD bom.

| Comando | Quando | O que faz |
|---|---|---|
| `python <skill-dir>/scripts/seq.py next /docs/prd --slug <domain-slug>-<feature-slug>` | Antes de criar o arquivo | Imprime `NNNN-<slug>` com o próximo número; recusa alocar quando há número duplicado |
| `python <skill-dir>/scripts/seq.py check /docs/prd` | Antes de apresentar | Acusa número duplicado; a rota de renumeração está em uma fonte só (SKILL.md, Caminho e numeração) |
| `python <skill-dir>/scripts/lint_prd.py <arquivo.md \| /docs/prd> --lang <pt\|en> [--source <material>] [--reverse]` | Antes de apresentar | Forma das seções e do header, IDs, links, PRD 0000 e heurísticas de redação; a lista completa de HARD e WARN é a docstring do script (rode-o sem argumentos) e não é repetida aqui. `--lang` é sempre o idioma fixado do PRD, `pt` ou `en` (Idioma). `--source` entra uma vez por arquivo de material de discovery em texto no disco, e acusa reformatação (intake.md, Material de discovery). `--reverse` é a opção do modo reverse PRD: quando ela entra e o que ela estende estão em uma fonte só (modes.md, Modo reverse PRD) |
| `python <skill-dir>/scripts/lint_mermaid.py <arquivo.md \| dir>` | Antes de apresentar PRD com diagrama | Faz o parse de todo bloco Mermaid. Bloco que não passou ou fence sem fechamento é HARD, porque diagrama não validado é diagrama não entregue; parser indisponível (exit 3) é bloqueio de ambiente e segue o passo Checar (Workflow). `--self-test` prova a extração e o parser; `--setup` instala o parser com `npm ci`, é o único modo com rede e só roda quando o usuário o autorizou na sessão, na ordem fixada em Checar |

## Exemplo

PRD no formato-alvo em [references/example.md](references/example.md). Leia a seção correspondente na primeira vez, nesta sessão, em que escrever uma seção da tabela (writing.md, Seções); não é template a copiar.
