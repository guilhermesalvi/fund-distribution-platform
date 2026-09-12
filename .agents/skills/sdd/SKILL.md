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

1. Há decisão de deploy, de estilo arquitetural ou de biblioteca compartilhada (design.md, Unidade de deploy e reuso); arquivo novo numa camada com menos de três arquivos do mesmo tipo, contados antes de decidir com `git ls-files '<glob da camada>'` — sem três exemplares não há convenção a copiar (design.md, Base de código); interação entre três ou mais componentes a planejar; ou risco de integração, dinheiro, regulação, contrato público, migração ou preocupação encontrada na base (as fontes de design.md, Do risco à técnica, fora as dimensões implícitas, que já viraram requisito)? Se sim, a mudança pede `design.md`.
2. Há mais de cinco passos, ou algum passo depende de outro que não é o imediatamente anterior? Se sim, a mudança pede `tasks.md`.

**Catraca.** A resposta só sobe. Complexidade descoberta no meio da mudança promove o nível de artefato: pare, diga o que descobriu e crie o artefato que faltou. Nada rebaixa o nível já decidido.

Specify e Execute nunca são pulados: sempre se sabe *o quê* antes de fazer. Quando não há `tasks.md`, o Execute começa por um plano inline (execute.md, Plano inline).

### Entradas e pré-requisitos

| Entrada | Pré-requisito | Referência |
|---|---|---|
| Specify | PRD, pedido com usuário-alvo e problema (specify.md, Origem) ou código a documentar | [specify.md](references/specify.md) |
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
  1. Decisão dentro da autonomia concedida, isto é, delegada por escrito no pedido da sessão ou no AGENTS.md do repositório: decida, registre e siga. Sem delegação escrita, escolha de negócio é a categoria 3 e escolha de solution space é a categoria 2, com duas exceções em que se pergunta: no Clarify, quando a resposta muda arquitetura, modelo de dados, decomposição, desenho de teste ou aceitação (specify.md, Clarify); no Design, critérios e abordagem (design.md, Critérios antes das abordagens). Com delegação escrita para o solution space, essas duas exceções caem e só a apresentação de cada artefato espera.
  2. `[PREMISSA]` com default e racional: avance; a premissa fica revisável.
  3. Decisão material do usuário (escopo, regra de negócio, trade-off, efeito externo): pergunte e bloqueie só o que depende dela. Sem resposta, o item fica bloqueado; nada é adotado por default.
- **Refine o contexto, não o erro.** Artefato downstream errado (teste que não deveria passar, código que contradiz o design, task impossível) não se remenda: corrija o artefato upstream que carregava a causa e re-derive o downstream. Regra de negócio errada volta ao PRD.
- **Precedência**, do que prevalece para o que cede:
  1. Pedido da sessão.
  2. Convenção do repositório.
  3. Defaults desta skill.

  A lista fechada de seções de cada artefato é default desta skill, degrau 3: HARD que decorre de um dos dois primeiros degraus é mantido, não corrigido (Scripts).

## Contrato de execução

Cinco regras, detalhadas em execute.md; este resumo não as reescreve:

1. **Testes derivam da spec, nunca da implementação** (execute.md, Ciclo por task).
2. **O gate decide, não a auto-avaliação**: task pronta é gate com exit 0 (execute.md, Ciclo por task).
3. **Um commit atômico por task**, quando autorizado (execute.md, Ciclo por task).
4. **Escopo de escrita de uma task** é só o dela; problema vizinho é reportado (execute.md, Ciclo por task).
5. **Segurança**: pacote novo e segredo (execute.md, Segurança).

## Scripts

Os scripts ficam em `scripts/`, no diretório desta skill, e rodam com `python3 <skill-dir>/scripts/<nome>.py` (ou `python`, onde `python3` não existir); rodar sem argumentos imprime a docstring completa. O `lint_mermaid.py` exige Node além do Python.

- `HARD` exige correção e nova rodada. O ciclo é: grave o artefato, rode o linter, corrija todo `HARD`, rode de novo e apresente quando a saída for `0 HARD`. São no máximo duas rodadas de correção: se a segunda ainda terminar com `HARD`, apresente o artefato e liste no chat cada `HARD` remanescente com o motivo de ele ter sobrado. Linter que não roda por falha de ambiente (Python ou Node ausentes; exit 3 de `lint_mermaid.py` por parser ausente) não é rodada: é bloqueio de ambiente, dito no chat, e o artefato é apresentado sem essa verificação. No exit 3, a ordem é: peça a autorização de `--setup` uma vez, antes de apresentar; autorizada, rode `--setup` e o linter de novo e trate a saída como qualquer outra; recusada ou sem resposta, apresente sem essa verificação. Exit 2 é erro de uso (arquivo ausente, opção desconhecida ou codificação fora de UTF-8) e se corrige como HARD.
- `WARN` é heurística: cada um termina de uma de duas formas, corrigido ou mantido com uma linha de razão no chat. A exceção é o WARN de `prd-rev` desatualizado, que é sempre corrigido e nunca mantido com razão (specify.md, Comentário de máquina).
- HARD que decorre do pedido da sessão ou da convenção do repositório — os dois primeiros degraus da Precedência — não se corrige nem conta como rodada: diga no chat qual HARD é e qual dos dois o mantém, com as palavras "mantido por pedido" ou "mantido por convenção". Pedido é o da sessão que nomeia literalmente a seção, o campo ou a forma de onde o HARD sai ("inclua uma seção Plano de Rollout no design"). Convenção é forma presente em três ou mais artefatos commitados do mesmo tipo, ou escrita no AGENTS.md do repositório: conte os artefatos com `git ls-files '<glob do tipo>'` (por exemplo `git ls-files 'docs/adr/*.md'`) e diga o número no chat; arquivo não commitado não conta.
- Linter verde é esqueleto conforme, não artefato bom.

| Antes de | Comando |
|---|---|
| criar a pasta de uma mudança ou uma ADR | `seq.py next <dir> --slug <slug>`: imprime `NNNN-<slug>` com o próximo número da pasta; recusa alocar sobre número duplicado |
| apresentar qualquer artefato numerado | `seq.py check <dir>`: acusa número duplicado na pasta. Renumere o item cujo branch entra depois: mova-o para um nome sem o prefixo `NNNN-` (o `next` recusa alocar enquanto a duplicata existe), rode `seq.py next <dir> --slug <slug>`, mova-o para o nome devolvido e rode o check de novo |
| apresentar a spec | `lint_spec.py <spec.md>` |
| apresentar o design | `lint_design.py <design.md> --spec <spec.md>` |
| apresentar as tasks | `lint_tasks.py <tasks.md> --spec <spec.md>` |
| apresentar a ADR | `lint_adr.py <adr.md \| dir>` |
| apresentar qualquer artefato com diagrama Mermaid | `lint_mermaid.py <arquivo.md \| dir>`: faz o parse de todo bloco Mermaid. Bloco que não passou ou fence sem fechamento é HARD, porque diagrama não validado é diagrama não entregue. `--self-test` prova a extração e o parser; `--setup` instala o parser com `npm ci`, é o único modo com rede e só roda quando o usuário o autorizou na sessão |

## Idioma e redação

### Idioma

- **O artefato é escrito em português ou em inglês, nunca em outro idioma.** Os quatro linters casam os headings por igualdade com os aliases PT/EN da lista de seções do artefato, e cada lista traz os dois nomes: spec (specify.md, Seções), design (design.md, Seções), tasks (tasks.md, Seções do `tasks.md`) e ADR (adr.md, Template). Seção fora da lista é HARD em `lint_design.py`, `lint_tasks.py` e `lint_adr.py`; em `lint_spec.py` é WARN, porque spec real pode carregar seção herdada do PRD. Artefato em terceiro idioma sai com um achado por seção — HARD nos três, WARN na spec — e sem correção possível.
- Qual dos dois: o idioma do PRD; sem PRD, o do material recebido (com material em mais de um idioma, o do documento que o pedido cita primeiro ou, sem citação, o do primeiro anexo); sem os dois, o do pedido; se o pedido mistura idiomas, português.
- Quando o idioma que essa regra devolve não é português nem inglês, o artefato fica em inglês e a apresentação diz, em uma linha, qual era o idioma do material e que o artefato saiu em inglês por isso.
- Termo canônico com tradução de mesma força se traduz: Requisitos, Fora de Escopo, Perguntas em Aberto, Dado/Quando/Então.
- Termo sem tradução de mesma força fica em inglês: domain event, outbox, idempotency key, retry, circuit breaker, aggregate, value object, port/adapter, trade-off, gate.
- Keywords EARS, IDs, código, paths, slugs e identificadores não se traduzem.
- Termo que o time usa em português (AGENTS.md, glossário do PRD ou código) fica em português mesmo que esteja na lista acima: é a precedência de Tags e dúvidas.

### Redação

- Declarativo, sem hedging, sem meta-narração, sem placeholder: `lint_spec.py`, `lint_design.py`, `lint_tasks.py` e `lint_adr.py` acusam os três como WARN, cada um no seu artefato. Tag fora de `[PREMISSA]` e `[LACUNA]` é HARD nos quatro.
- Um conceito por parágrafo.
- Contexto de decisão (racional, mitigação) preservado: é sinal para humanos e para o próximo agente.

## Revisão por entrada

Faça esta revisão antes de apresentar cada artefato, além de rodar o linter. Vale para todas as entradas: nenhuma seção existe só para cumprir a forma.

A lista da entrada é fechada. Em Specify, Design, Tasks e ADR:

- percorra o artefato inteiro para cada item e dê ao item a nota 100 menos 20 por ocorrência encontrada (mínimo 0); uma ocorrência já derruba o item, e a nota existe para registrar quantas;
- item abaixo de 90 é reescrito; item com 90 ou mais fica como está;
- reescreveu, dê nota de novo: são no máximo duas passadas por artefato;
- item que continuar abaixo de 90 na segunda passada não segura o artefato: apresente e diga no chat qual item é, com a nota e o que falta;
- a revisão vem depois do ciclo do linter; se ela alterou o artefato, rode o linter uma vez mais, fora do teto: HARD nessa execução é corrigido uma vez e, se persistir, listado no chat.

Em Execute e Verify os itens são binários, atendido ou não: item não atendido se corrige dentro dos tetos do próprio ciclo (execute.md, Ciclo por task; verify.md, Gaps e tasks de correção).

### Specify

- `SHALL` e ID único já são HARD de `lint_spec.py`, e padrão EARS é WARN dele; aqui: o padrão está correto, o valor de cada requisito é concreto e dá para escrever o teste que o afirma. Se não dá, reescreva o requisito.
- Cada cenário dos Critérios de Aceitação do PRD aparece na Rastreabilidade com os IDs EARS que o cobrem: a presença é HARD de `lint_spec.py` quando o PRD os lista em tabela; aqui, os IDs listados de fato cobrem o cenário.
- Requisito que vem do PRD cita o ID e não reescreve a regra.
- Nenhuma regra de negócio foi decidida por premissa nova na spec; premissa herdada do PRD, com origem anotada, não conta.
- Toda inferência está marcada.
- Se o Design vai precisar decidir comportamento, a spec ficou incompleta.

### Design

- Profundidade proporcional ao risco: as linhas de cada seção não se contam a olho, `lint_design.py` acusa como WARN a seção acima de dez linhas de corpo; aqui você decide, para cada seção acusada, se o assunto dela aparece em Riscos e técnicas — se não aparece, é inflação e a seção encolhe. Risco sem técnica ou aceite é buraco.
- Critérios fixados e criticados antes das abordagens; a quarta pergunta (existe forma mais barata ou menos arriscada de fazer o mesmo?) respondida.
- Nenhum comportamento decidido aqui que devia estar na spec.
- Interfaces com tipos; a cobertura de todo `IF/THEN` da spec no tratamento de erros já é HARD de `lint_design.py`.
- ADRs conformadas ou supersedidas (adr.md, Conformar e superseder).

### Tasks

- Cobertura requisito para task e task para requisito já é HARD de `lint_tasks.py`; aqui: nenhuma task cita em `Requisito` um ID que ela não exercita.
- `Consome` e `Produz` consistentes entre as tasks e com o design.
- `Tests` coerente com a camada da task, com teste co-locado.
- `Pronto quando` com critério de comportamento que a spec define; `lint_tasks.py` já exige que o comando entre crases seja o do gate da task e que exista critério além dele, o conteúdo do critério é você quem confere.

### ADR

Quatro itens, os que `lint_adr.py` não alcança porque são conteúdo, não forma:

- A decisão fixa convenção, restrição ou padrão que features futuras seguem; decisão local à feature é ocorrência, e o destino dela é o design (adr.md, Quando a decisão é de projeto).
- Cada linha de Alternativas consideradas é uma alternativa realmente avaliada, derrubada contra os mesmos critérios que sustentam a decisão; alternativa escrita para encher a tabela é ocorrência.
- A linha `Negativas` nomeia o custo aceito desta decisão; risco genérico, que qualquer decisão teria, é ocorrência.
- Toda regra de projeto que a decisão cria ou altera está em Regras derivadas; o bullet e o path do arquivo já são HARD de `lint_adr.py` (adr.md, Conformar e superseder), aqui: cada regra listada é mesmo criada ou alterada por esta decisão, e ADR que não cria regra não tem a seção.

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
