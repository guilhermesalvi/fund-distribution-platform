---
name: sdd
description: 'SDD em cinco entradas (Specify, Design, Tasks, Execute, Verify): de requisitos técnicos testáveis (EARS, IDs rastreáveis, spec viva por capability) a design orientado a risco, tasks com teste co-locado e verificação com evidência. Começa onde o PRD termina. TRIGGER: "tech spec", "especificação técnica", "spec" de requisitos técnicos ou de comportamento do sistema, "SDD", "design da solução", "quebre em tasks", "implemente a spec", "verifique a implementação", "retome" uma mudança existente, "documente a spec do módulo X"; também ao implementar feature não trivial sem citar spec. NÃO acionar para PRD/discovery, ADR isolada, code review sem spec, refactor mecânico.'
---

# Spec-Driven Development

Esta skill é um método de escrita e de execução em cinco entradas, cada uma com um papel fixo:

- **Specify:** a spec diz *o quê* construir.
- **Design:** o design diz *como*.
- **Tasks:** as tasks dizem *em que ordem*.
- **Execute:** entrega uma task por vez.
- **Verify:** prova com evidência que a implementação atende à spec e ao design.

O PRD, em `/docs/prd` e com IDs no formato `<PREFIXO>-nn`, é a entrada do método e a fonte das regras de negócio. Esta skill começa onde o PRD termina.

O linter é feedback para o agente, não carimbo no artefato: o que ele acusa se corrige antes de apresentar, no ciclo e no teto descritos em Scripts. O artefato nunca carrega estado de validação.

## Abrir uma mudança

### Quanto artefato a mudança pede

Duas perguntas decidem quais artefatos a mudança pede, além da spec:

1. Há decisão arquitetural, padrão novo, interação entre três ou mais componentes a planejar ou risco nomeado (integração externa, estado e concorrência, dinheiro, dado regulado, contrato público, novo deployável)? Se sim, a mudança pede `design.md`.
2. Há mais de cinco passos, ou algum passo depende de outro que não é o imediatamente anterior? Se sim, a mudança pede `tasks.md`.

**Catraca.** A resposta só sobe. Complexidade descoberta no meio da mudança promove o nível de artefato: pare, diga o que descobriu e crie o artefato que faltou. Nada rebaixa o nível já decidido.

Specify e Execute nunca são pulados: sempre se sabe *o quê* antes de fazer. Quando não há `tasks.md`, o Execute começa por um plano inline (execute.md, Plano inline).

### Entradas e pré-requisitos

| Entrada | Pré-requisito | Referência |
|---|---|---|
| Specify | PRD, pedido rico (usuário, problema, comportamento observável) ou código a documentar | [specify.md](references/specify.md) |
| Design | spec commitada | [design.md](references/design.md) |
| Tasks | design commitado, ou spec quando o Design foi dispensado | [tasks.md](references/tasks.md) |
| Execute | tasks commitadas, ou plano inline aprovado | [execute.md](references/execute.md) |
| Verify | última task fechada | [verify.md](references/verify.md) |
| ADR | decisão que fixa convenção para features futuras | [adr.md](references/adr.md) |

Leia a referência inteira antes de agir em qualquer entrada. O layout de arquivos e os comentários de máquina estão definidos na referência de Specify (specify.md, Layout).

## Aprovação e autorizações

- **Aprovação é o commit.** Árvore suja é trabalho em elaboração; arquivo commitado é a versão válida.
- **Apresente e espere.** Apresente cada artefato e espere a aprovação antes de começar o seguinte. Aprovação dada no chat sem commit não abre a entrada seguinte: peça, uma vez, que o usuário commite o artefato ou autorize o commit; sem resposta, a mudança fica parada nessa entrada. O plano inline (execute.md, Plano inline) é a exceção: vive no chat, é aprovado no chat e o Execute começa em seguida.
- **Cada palavra autoriza uma coisa.** "Implementa" autoriza editar os arquivos da mudança. "Commita", dito uma vez por mudança, autoriza todos os commits locais dela: um por artefato e um por task. Push, deploy e qualquer efeito externo perguntam sempre.
- **Silêncio nunca é aprovação.**

## Tags e dúvidas

- **Tags.** `[PREMISSA]` marca inferência com default e racional; `[LACUNA]` marca informação insuficiente para decidir. Texto sem tag é fato, com origem no PRD, no usuário, no código ou na documentação. Aprovação não converte premissa em fato.
- **Fatos você procura; decisões você pergunta.** A cadeia de pesquisa para um fato, nesta ordem: base de código, docs do projeto, documentação oficial, web; se nada responder, sinalize a incerteza. Nunca fabrique API, padrão ou comportamento; "não encontrei" é resposta válida.
- **Toda dúvida cai em uma de três categorias:**
  1. Decisão dentro da autonomia concedida, isto é, delegada por escrito no pedido da sessão ou no CLAUDE.md do repositório: decida, registre e siga. Sem delegação escrita, escolha de solution space é a categoria 2 e escolha de negócio é a categoria 3; a exceção é o ponto em que uma entrada exige resposta do usuário por escrito, como critérios e abordagem no Design (design.md, Critérios antes das abordagens); ali a resposta é aguardada.
  2. `[PREMISSA]` com default e racional: avance; a premissa fica revisável.
  3. Decisão material do usuário (escopo, regra de negócio, trade-off, efeito externo): pergunte e bloqueie só o que depende dela. Sem resposta, o item fica bloqueado; nada é adotado por default.
- **Refine o contexto, não o erro.** Artefato downstream errado (teste que não deveria passar, código que contradiz o design, task impossível) não se remenda: corrija o artefato upstream que carregava a causa e re-derive o downstream. Regra de negócio errada volta ao PRD.
- **Precedência**, do que prevalece para o que cede:
  1. Pedido da sessão.
  2. Convenção do repositório.
  3. Defaults desta skill.

## Contrato de execução

Cinco regras, detalhadas em execute.md; este resumo não as reescreve:

1. **Testes derivam da spec, nunca da implementação** (execute.md, Ciclo por task).
2. **O gate decide, não a auto-avaliação**: task pronta é gate com exit 0 (execute.md, Ciclo por task).
3. **Um commit atômico por task**, quando autorizado (execute.md, Ciclo por task).
4. **Escopo de escrita de uma task** é só o dela; problema vizinho é reportado (execute.md, Ciclo por task).
5. **Segurança**: pacote novo e segredo (execute.md, Segurança).

## Scripts

Os scripts ficam em `scripts/`, no diretório desta skill, e rodam com `python3 <skill-dir>/scripts/<nome>.py`; rodar sem argumentos imprime a docstring completa.

- `HARD` exige correção e nova rodada. O ciclo é: grave o artefato, rode o linter, corrija todo `HARD`, rode de novo e apresente quando a saída for `0 HARD`. São no máximo duas rodadas de correção: se a segunda ainda terminar com `HARD`, apresente o artefato e liste no chat cada `HARD` remanescente com o motivo de ele ter sobrado. Linter que não roda por falha de ambiente não é rodada: diga isso no chat e apresente sem essa verificação.
- `WARN` é heurística: cada um termina de uma de duas formas, corrigido ou mantido com uma linha de razão no chat.
- HARD que decorre de convenção do repositório (Precedência) não se corrige nem conta como rodada: diga no chat qual HARD é e qual convenção o justifica.
- Linter verde é esqueleto conforme, não artefato bom.

| Antes de | Comando |
|---|---|
| criar a pasta de uma mudança ou uma ADR | `seq.py next <dir> --slug <slug>`: imprime `NNNN-<slug>` com o próximo número da pasta; recusa alocar sobre número duplicado |
| apresentar qualquer artefato numerado | `seq.py check <dir>`: acusa número duplicado na pasta |
| apresentar a spec | `lint_spec.py <spec.md>` |
| apresentar o design | `lint_design.py <design.md> --spec <spec.md>` |
| apresentar as tasks | `lint_tasks.py <tasks.md> --spec <spec.md>` |

## Idioma e redação

### Idioma

- O artefato fica no idioma do input; se o idioma for ambíguo, português.
- Termo canônico com tradução de mesma força se traduz: Requisitos, Fora de Escopo, Perguntas em Aberto, Dado/Quando/Então.
- Termo sem tradução de mesma força fica em inglês: domain event, outbox, idempotency key, retry, circuit breaker, aggregate, value object, port/adapter, trade-off, gate.
- Keywords EARS, IDs, código, paths, slugs e identificadores não se traduzem.
- Termo que o time usa em português (CLAUDE.md, glossário do PRD ou código) fica em português mesmo que esteja na lista acima: é a precedência de Tags e dúvidas.

### Redação

- Declarativo, sem hedging, sem meta-narração, sem placeholder. `lint_spec.py` acusa os três na spec, `lint_tasks.py` e `lint_design.py` acusam placeholder nas tasks e no design; na ADR, que não tem linter, a checagem é sua.
- Um conceito por parágrafo.
- Contexto de decisão (racional, mitigação) preservado: é sinal para humanos e para o próximo agente.

## Revisão por entrada

Faça esta revisão antes de apresentar cada artefato, além de rodar o linter. Vale para todas as entradas: nenhuma seção existe só para cumprir a forma.

A lista da entrada é fechada. Em Specify, Design e Tasks, percorra o artefato inteiro para cada item e dê ao item a nota 100 menos 20 por ocorrência encontrada (mínimo 0): item abaixo de 90 é reescrito, item com 90 ou mais fica como está. Reescreveu, dê nota de novo — são no máximo duas passadas por artefato. Item que continuar abaixo de 90 na segunda passada não segura o artefato: apresente e diga no chat qual item é, com a nota e o que falta. A revisão vem depois do ciclo do linter; se ela alterou o artefato, rode o linter uma vez mais, fora do teto: HARD nessa execução é corrigido uma vez e, se persistir, listado no chat. Em Execute e Verify os itens são binários, atendido ou não: item não atendido se corrige dentro dos tetos do próprio ciclo (execute.md, Ciclo por task; verify.md, Gaps e tasks de correção).

### Specify

- `SHALL` e ID único já são HARD de `lint_spec.py`, e padrão EARS é WARN dele; aqui: o padrão está correto, o valor de cada requisito é concreto e dá para escrever o teste que o afirma. Se não dá, reescreva o requisito.
- Cada cenário dos Critérios de Aceitação do PRD aparece na Rastreabilidade com os IDs EARS que o cobrem; o linter não confere cenários.
- Requisito que vem do PRD cita o ID e não reescreve a regra.
- Nenhuma regra de negócio foi decidida por premissa.
- Toda inferência está marcada.
- Se o Design vai precisar decidir comportamento, a spec ficou incompleta.

### Design

- Profundidade proporcional ao risco: seção com mais de dez linhas cujo assunto não aparece em Riscos e técnicas é inflação; risco sem técnica ou aceite é buraco.
- Critérios fixados e criticados antes das abordagens; a quarta pergunta (existe forma mais barata ou menos arriscada de fazer o mesmo?) respondida.
- Nenhum comportamento decidido aqui que devia estar na spec.
- Interfaces com tipos; a cobertura de todo `IF/THEN` da spec no tratamento de erros já é HARD de `lint_design.py`.
- ADRs conformadas ou supersedidas (adr.md, Conformar e superseder).

### Tasks

- Cobertura requisito para task e task para requisito já é HARD de `lint_tasks.py`; aqui: nenhuma task cita em `Requisito` um ID que ela não exercita.
- `Consome` e `Produz` consistentes entre as tasks e com o design.
- `Tests` coerente com a camada da task, com teste co-locado.
- `Pronto quando` com critério de comportamento que a spec define; a presença do comando de gate e do critério `lint_tasks.py` já exige, o conteúdo do critério é você quem confere.

### Execute

- Plano declarado antes do código.
- Testes da spec falhando antes da implementação.
- Implementação mínima.
- Gate verde.
- Tabela de evidência preenchida.
- Nenhuma lacuna resolvida em silêncio.
- Só os arquivos da task tocados.

### Verify

- Cobertura re-derivada com olhos frescos, com o grau de independência declarado no relatório.
- Toda linha de evidência com `file:line` e assertion.
- Lacuna de precisão reportada, nunca aprovada.
- Os dois eixos percorridos: conformidade à spec e aderência ao design.
- Gaps ordenados por severidade (verify.md, Relatório no chat) e convertidos em tasks de correção `TCn`.
