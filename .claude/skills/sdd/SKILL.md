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

O linter é feedback para o agente, não carimbo no artefato. O ciclo é: grave o artefato, rode o linter, corrija o que ele apontou, rode de novo e só então apresente. O artefato nunca carrega estado de validação. Se o linter não rodar por falha de ambiente, diga isso no chat.

## Abrir uma mudança

### Quanto artefato a mudança pede

Duas perguntas decidem quais artefatos a mudança pede, além da spec:

1. Há decisão arquitetural, padrão novo, interação entre componentes a planejar ou risco nomeado (integração externa, estado e concorrência, dinheiro, dado regulado, contrato público, novo deployável)? Se sim, a mudança pede `design.md`.
2. Há mais de cinco passos ou dependência não trivial? Se sim, a mudança pede `tasks.md`.

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
- **Apresente e espere.** Apresente cada artefato e espere a aprovação antes de começar o seguinte.
- **Cada palavra autoriza uma coisa.** "Implementa" autoriza editar os arquivos da mudança. "Commita" autoriza commit local, uma vez por mudança. Push, deploy e qualquer efeito externo perguntam sempre.
- **Silêncio nunca é aprovação.**

## Tags e dúvidas

- **Tags.** `[PREMISSA]` marca inferência com default e racional; `[LACUNA]` marca informação insuficiente para decidir. Texto sem tag é fato, com origem no PRD, no usuário, no código ou na documentação. Aprovação não converte premissa em fato.
- **Fatos você procura; decisões você pergunta.** A cadeia de pesquisa para um fato, nesta ordem: base de código, docs do projeto, documentação oficial, web; se nada responder, sinalize a incerteza. Nunca fabrique API, padrão ou comportamento; "não encontrei" é resposta válida.
- **Toda dúvida cai em uma de três categorias:**
  1. Decisão dentro da autonomia concedida: decida, registre e siga.
  2. `[PREMISSA]` com default e racional: avance; a premissa fica revisável.
  3. Decisão material do usuário (escopo, regra de negócio, trade-off, efeito externo): pergunte e bloqueie só o que depende dela. Sem resposta, o item fica bloqueado; nada é adotado por default.
- **Refine o contexto, não o erro.** Artefato downstream errado (teste que não deveria passar, código que contradiz o design, task impossível) não se remenda: corrija o artefato upstream que carregava a causa e re-derive o downstream. Regra de negócio errada volta ao PRD.
- **Precedência**, do que prevalece para o que cede:
  1. Pedido da sessão.
  2. Convenção do repositório.
  3. Defaults desta skill.

## Contrato de execução

1. **Testes derivam da spec, nunca da implementação.** Cada teste afirma o resultado que a spec define.
2. **O gate decide, não a auto-avaliação.** Task pronta é comando de gate com exit 0. Gate que não roda é bloqueio com motivo.
3. **Um commit atômico por task**, quando autorizado, no formato que o repositório convenciona; se o repositório tem validação de mensagem, rode-a. Nunca enfraqueça, pule ou apague teste para passar.
4. **Escopo de escrita de uma task:** seus arquivos de implementação, teste, configuração indispensável e o `tasks.md`. Problema vizinho é reportado, não corrigido.
5. **Segurança.** Pacote novo é sugestão até validar a procedência. Segredo encontrado na base nunca entra no output.

## Scripts

Os scripts ficam em `scripts/`, no diretório desta skill, e rodam com `python3 <skill-dir>/scripts/<nome>.py`; rodar sem argumentos imprime a docstring completa.

- `HARD` exige correção e nova rodada.
- `WARN` é heurística: julgue.
- Linter verde é esqueleto conforme, não artefato bom.
- Sem ferramenta de execução, faça as mesmas checagens lendo o artefato e diga que a verificação foi manual.

| Antes de apresentar | Comando |
|---|---|
| a spec | `lint_spec.py <spec.md>` |
| as tasks | `lint_tasks.py <tasks.md> --spec <spec.md>` |

## Idioma e redação

### Idioma

- O artefato fica no idioma do input; se o idioma for ambíguo, português.
- Termo canônico com tradução de mesma força se traduz: Requisitos, Fora de Escopo, Perguntas em Aberto, Dado/Quando/Então.
- Termo sem tradução de mesma força fica em inglês: domain event, outbox, idempotency key, retry, circuit breaker, aggregate, value object, port/adapter, trade-off, gate.
- Keywords EARS, IDs, código, paths, slugs e identificadores não se traduzem.
- Termo que o time usa em português fica em português.

### Redação

- Declarativo, sem hedging, sem meta-narração, sem placeholder.
- Um conceito por parágrafo.
- Contexto de decisão (racional, mitigação) preservado: é sinal para humanos e para o próximo agente.

## Revisão por entrada

Faça esta revisão antes de apresentar cada artefato, além de rodar o linter. Vale para todas as entradas: nenhuma seção existe só para cumprir a forma.

### Specify

- Cada requisito é um padrão EARS com `SHALL`, valor concreto e ID único. Se não dá para escrever o teste, reescreva o requisito.
- Requisito que vem do PRD cita o ID e não reescreve a regra.
- Nenhuma regra de negócio foi decidida por premissa.
- Toda inferência está marcada.
- Se o Design vai precisar decidir comportamento, a spec ficou incompleta.

### Design

- Profundidade proporcional ao risco: seção longa sem risco é inflação; risco sem técnica ou aceite é buraco.
- Critérios fixados e criticados antes das abordagens; a quarta pergunta (existe forma mais barata ou menos arriscada de fazer o mesmo?) respondida.
- Nenhum comportamento decidido aqui que devia estar na spec.
- Interfaces com tipos, e todo `IF/THEN` da spec aparece no tratamento de erros.
- ADRs conformadas ou supersedidas (adr.md, Conformar e superseder).

### Tasks

- Todo requisito em escopo tem task; toda task tem requisito.
- `Consome` e `Produz` consistentes entre as tasks e com o design.
- `Tests` coerente com a camada da task, com teste co-locado.
- `Pronto quando` com critério de comportamento e comando de gate.

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
- Gaps ordenados por severidade e convertidos em tasks de correção `TCn`.
