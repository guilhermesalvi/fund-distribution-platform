---
name: spec-driven
description: 'SDD em cinco entradas (Specify, Design, Tasks, Execute, Verify): de requisitos técnicos testáveis (EARS, IDs rastreáveis, spec viva por capability) a design orientado a risco, tasks com teste co-locado e verificação com evidência. Começa onde o PRD termina. TRIGGER: "tech spec", "especificação técnica", "spec" de requisitos técnicos ou de comportamento do sistema, "SDD", "design da solução", "quebre em tasks", "implemente a spec", "verifique a implementação", "retome" uma mudança existente, "documente a spec do módulo X"; também ao implementar feature não trivial sem citar spec. NÃO acionar para PRD/discovery, ADR isolada, code review sem spec, refactor mecânico.'
---

# Spec-Driven Development

Método de escrita e execução: a spec diz o quê, o design diz como, as tasks dizem em que ordem, o Execute entrega uma task por vez e o Verify prova com evidência. O PRD (em `/docs/prd`, IDs `<PREFIXO>-nn`) é a entrada e a fonte das regras de negócio; esta skill começa onde ele termina. Linter é feedback para o agente: gravar → rodar → corrigir → rodar de novo → apresentar; o artefato nunca carrega estado de validação, e falha de ambiente é dita no chat.

## Abrir uma mudança

Duas perguntas decidem quanto artefato a mudança pede:

- `design.md` quando há decisão arquitetural, padrão novo, interação entre componentes a planejar ou risco nomeado (integração externa, estado e concorrência, dinheiro, dado regulado, contrato público, novo deployável).
- `tasks.md` quando há mais de cinco passos ou dependência não trivial.

Catraca: complexidade descoberta no meio promove (pare, diga, crie o artefato que faltou); nada rebaixa. Specify e Execute nunca são pulados: sempre se sabe o quê antes de fazer. Sem `tasks.md`, o Execute começa por um plano inline (execute.md).

| Entrada | Pré-requisito | Referência |
|---|---|---|
| Specify | PRD, pedido rico (usuário, problema, comportamento observável) ou código a documentar | [specify.md](references/specify.md) |
| Design | spec commitada | [design.md](references/design.md) |
| Tasks | design commitado, ou spec quando o Design foi dispensado | [tasks.md](references/tasks.md) |
| Execute | tasks commitadas, ou plano inline aprovado | [execute.md](references/execute.md) |
| Verify | última task fechada | [verify.md](references/verify.md) |
| ADR | decisão que fixa convenção para features futuras | [adr.md](references/adr.md) |

Leia a referência inteira antes de agir. Layout de arquivos e comentários de máquina em specify.md, Layout.

## Aprovação e autorizações

Aprovação é o commit: árvore suja é trabalho em elaboração; arquivo commitado é a versão válida. Apresente cada artefato e espere antes de começar o seguinte. "Implementa" autoriza editar os arquivos da mudança; "commita" autoriza commit local, uma vez por mudança; push, deploy e qualquer efeito externo perguntam sempre. Silêncio nunca é aprovação.

## Tags e dúvidas

- `[PREMISSA]` é inferência com default e racional; `[LACUNA]` é informação insuficiente para decidir. Sem tag é fato (PRD, usuário, código, documentação). Aprovação não converte premissa em fato.
- **Fatos você procura; decisões você pergunta.** Cadeia de pesquisa: base de código → docs do projeto → documentação oficial → web → sinalizar incerteza. Nunca fabrique API, padrão ou comportamento; "não encontrei" é resposta válida.
- Toda dúvida cai em uma de três categorias: decisão dentro da autonomia concedida (decida, registre, siga); `[PREMISSA]` com default e racional (avance, fica revisável); decisão material do usuário (escopo, regra de negócio, trade-off, efeito externo: pergunte e bloqueie só o que depende dela). Sem resposta, o item fica bloqueado; nada é adotado por default.
- **Refine o contexto, não o erro.** Artefato downstream errado (teste que não deveria passar, código que contradiz o design, task impossível) não se remenda: corrija o artefato upstream que carregava a causa e re-derive. Regra de negócio errada volta ao PRD.
- Precedência: pedido da sessão > convenção do repositório > defaults desta skill.

## Contrato de execução

1. Testes derivam da spec, nunca da implementação: cada teste afirma o resultado que a spec define.
2. O gate decide, não a auto-avaliação: task pronta é comando de gate com exit 0; gate que não roda é bloqueio com motivo.
3. Um commit atômico por task, quando autorizado, no formato que o repositório convenciona; se ele tem validação de mensagem, rode-a. Nunca enfraqueça, pule ou apague teste para passar.
4. Escopo de escrita de uma task: seus arquivos de implementação, teste, configuração indispensável e o `tasks.md`. Problema vizinho é reportado, não corrigido.
5. Pacote novo é sugestão até validar a procedência; segredo encontrado na base nunca entra no output.

## Scripts

Em `scripts/` no diretório desta skill: `python3 <skill-dir>/scripts/<nome>.py` (docstring completa ao rodar sem argumentos). `HARD` exige correção e nova rodada; `WARN` é heurística, julgue. Linter verde é esqueleto conforme, não artefato bom. Sem ferramenta de execução, faça as mesmas checagens lendo e diga que foi manual.

| Antes de apresentar | Comando |
|---|---|
| a spec | `lint_spec.py <spec.md>` |
| as tasks | `lint_tasks.py <tasks.md> --spec <spec.md>` |

## Idioma e redação

- Artefato no idioma do input (ambíguo: português). Termo canônico com tradução de mesma força se traduz (Requisitos, Fora de Escopo, Perguntas em Aberto, Dado/Quando/Então); sem tradução de mesma força fica em inglês (domain event, outbox, idempotency key, retry, circuit breaker, aggregate, value object, port/adapter, trade-off, gate); keywords EARS, IDs, código, paths, slugs e identificadores não se traduzem; termo que o time usa em português fica em português.
- Declarativo, sem hedging, sem meta-narração, sem placeholder; um conceito por parágrafo; contexto de decisão (racional, mitigação) preservado, porque é sinal para humanos e para o próximo agente.

## Revisão por entrada

Antes de apresentar, além do linter. Em todas: nenhuma seção existe só para cumprir a forma.

- **Specify:** cada requisito é um padrão EARS com `SHALL`, valor concreto e ID único (se não dá para escrever o teste, reescreva); requisito do PRD cita o ID e não reescreve a regra; nenhuma regra de negócio decidida por premissa; toda inferência marcada; se o Design vai precisar decidir comportamento, a spec ficou incompleta.
- **Design:** profundidade proporcional ao risco (seção longa sem risco é inflação; risco sem técnica ou aceite é buraco); critérios fixados e criticados antes das abordagens, quarta pergunta respondida; nenhum comportamento decidido aqui que devia estar na spec; interfaces com tipos e todo `IF/THEN` da spec no tratamento de erros; ADRs conformadas ou supersedidas.
- **Tasks:** todo requisito em escopo tem task; toda task tem requisito; `Consome`/`Produz` consistentes entre tasks e com o design; `Tests` coerente com a camada e co-locado; `Pronto quando` com critério de comportamento e gate.
- **Execute:** plano declarado, testes da spec falhando antes, implementação mínima, gate verde, tabela de evidência; nenhuma lacuna resolvida em silêncio; só os arquivos da task tocados.
- **Verify:** cobertura re-derivada com olhos frescos e independência declarada; toda linha de evidência com `file:line` e assertion; lacuna de precisão reportada, nunca aprovada; dois eixos; gaps ordenados e convertidos em `TCn`.
