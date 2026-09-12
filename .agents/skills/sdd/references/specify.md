# Specify

**Objetivo:** capturar *o quê* construir como requisitos testáveis e rastreáveis. A spec é o contrato que o Design refina, que as Tasks decompõem e que o Verify audita. A spec vive no solution space; a regra de negócio vive no PRD.

## Layout

```text
/docs/specs/<domain-slug>/<capability-slug>/
├── spec.md                      # spec viva, editada no lugar
└── NNNN-<change-slug>/          # só quando a mudança pede design ou tasks
    ├── design.md
    └── tasks.md
/docs/adr/NNNN-<slug>.md         # decisão de projeto (adr.md)
```

### Slugs e numeração

- **Slugs** em inglês e kebab-case, espelhando o nome que o código usa: `PartialReservation` vira `partial-reservation`. Capability é uma área funcional de um bounded context, como `reservation-book/reservation-lifecycle`.
- **`NNNN`** é um contador dentro da capability. Obtenha o número com `seq.py next <capability-dir> --slug <change-slug>`, nunca lendo a pasta; `seq.py check` acusa duplicata quando dois branches alocam o mesmo número (validation.md, Scripts). A pasta da mudança só existe quando há `design.md` ou `tasks.md`; nunca scaffolde artefato vazio.

### Versionamento

Git é o controle de versão: o diff é o delta e o log é o histórico; a aprovação é o commit (workflow.md, Aprovação e autorizações). Nenhum artefato carrega campo de status, autor, data ou aprovação.

### Comentário de máquina

A primeira linha de cada artefato, antes do `#`, é um comentário de máquina em ASCII minúsculo:

- spec: `<!-- sdd: spec | capability: offering/offer-lifecycle | prd: /docs/prd/0001-offering-offer-lifecycle.md | prd-rev: git:<hash> -->`
- design: `<!-- sdd: design | spec: ../spec.md -->`
- tasks: `<!-- sdd: tasks | spec: ../spec.md | design: ./design.md -->`

Campos condicionais:

- `design:` entra no comentário das tasks só quando o `design.md` existe.
- `scope: RSV-07, RSV-10` entra no comentário do design e das tasks quando a mudança toca só parte dos requisitos da spec; no design, limita a cobertura de `IF ... THEN` exigida em Tratamento de erros aos IDs listados.
- `prd:` e `prd-rev:` entram no comentário da spec só quando há PRD. `prd-rev` é o resultado de `git hash-object <prd.md>` sobre o arquivo em disco, com a árvore limpa para esse arquivo (é o que o linter recalcula); PRD modificado e não commitado pede o commit dele antes de gravar a spec. Se o PRD mudar depois, o linter avisa; esse WARN é sempre corrigido, nunca mantido com razão: re-derive os requisitos que citam os IDs tocados e atualize o hash.

### Linha de prefixo

Logo abaixo do `#` vem a linha ``Prefixo dos requisitos: `RSV`.`` e nada mais de cabeçalho.

## Origem

O sinal no pedido determina a origem da spec, o que conta como fato e o cuidado que a escrita exige.

| Sinal no pedido | Origem | O que é fato | Cuidado |
|---|---|---|---|
| Há PRD em `/docs/prd` | PRD | O texto sem tag do PRD. O que está marcado `[PREMISSA]` no PRD continua `[PREMISSA]` na spec, com a origem PRD anotada, e não conta como premissa de solution space | Siga as seis regras da subseção A partir do PRD |
| Não há PRD, mas usuário-alvo e problema estão no pedido | Ideia | O que o usuário afirmou | Registre usuário, problema e resultado no Contexto; comportamento observável ausente vira `[LACUNA]` no Contexto. Se faltar usuário ou problema, pare |
| Pedido solution-first, sem usuário nem problema ("CRUD para X", "tela de Y") | — | — | Responda "Isso precisa de PRD antes" e pare |
| Código existente sem spec ("documente a spec do módulo X") | Código | O que o código *faz*: comportamento, testes, docs | Intenção inferida é `[PREMISSA]`; comportamento sem justificativa de negócio é `[LACUNA]`; divergências vão na seção Divergências; a leitura da base segue design.md, Base de código |

### A partir do PRD

Quando a origem é o PRD, valem seis regras:

1. **Cite o ID, não reescreva a regra.** O requisito EARS cita o ID do PRD ao fim da linha (`[BOOK-04]`) e descreve o comportamento observável que realiza a regra (valor, status, evento, prazo), sem reescrevê-la. Regra escrita em dois lugares diverge. Estado, evento e enumeração usam o identificador que o PRD fixa.
2. **Regra de negócio se corrige no PRD.** Lacuna ou inconsistência de regra de negócio se corrige no PRD e nunca vira premissa na spec. Premissa nova na spec é só de solution space: formato de erro, prazo técnico, ordem de processamento; premissa herdada do PRD mantém a tag com a origem anotada (Origem).
3. **Prefixo distinto.** O prefixo da spec é distinto de todo prefixo de PRD e não compartilha com nenhum deles as duas primeiras letras: `OFR` ao lado de `OFF` convida a erro; prefira sigla de outra raiz. O linter acusa colisão lendo `/docs/prd`.
4. **PRD 0000.** Quando existe, o PRD 0000 fornece o mapa de contextos, o catálogo de eventos e as decisões delegadas a ADR. Evento que a capability produz ou consome vira requisito citando o ID que o governa; decisão delegada a ADR entra em Perguntas em Aberto com dono "Design/ADR".
5. **NFR.** NFR com resultado observável por teste (prazo, atomicidade, registro de auditoria) vira requisito EARS citando o `X-NFR-nn`. NFR que é atributo de qualidade sem teste direto vira critério de design (design.md, Critérios) e aparece na Rastreabilidade numa linha cuja segunda coluna começa com `Critério de design:` (forma que o linter reconhece).
6. **Cenários de aceitação.** Os cenários dos Critérios de Aceitação do PRD são a suíte mínima que o Execute reproduz (execute.md, Ciclo por task). A Rastreabilidade os lista pelo nome do caso quando o PRD os traz em tabela (primeira coluna; o linter exige os que citam FR em escopo) e pelo FR que exercitam quando o PRD os traz em bullets, com os IDs EARS que os cobrem. FR ou cenário de outra capability entra numa linha cuja segunda coluna começa com `Fora desta capability:` e o nome da capability dona (forma que o linter reconhece). Aceitar a entrada válida e rejeitar a inválida são cenários distintos e requisitos distintos.

### Leitura prévia

Em qualquer origem, leia antes de escrever: a `spec.md` viva da capability, se existir, e as ADRs ativas em `/docs/adr`, que restringem o que a spec pode pedir.

## Clarify

- **Varra a base antes de perguntar:** o módulo que a capability toca, os padrões que ele usa e ao menos uma feature irmã já implementada. Use o que encontrar para ancorar as perguntas, não para limitar a spec ao que já existe.
- **Você é par técnico, não entrevistador.** Desafie vagueza ("rápido" é quanto? "usuários" são quem?) e torne o abstrato concreto ("me conduz por um uso disso").
- **Pergunte só quando a resposta muda** arquitetura, modelo de dados, decomposição, desenho de teste ou aceitação (é a exceção de workflow.md, Tags e dúvidas; com delegação escrita para o solution space, não se pergunta). O que o código ou o PRD já responde não se pergunta; preferência estilística não se pergunta.
- **Uma pergunta por vez:** interrogativa completa, uma linha de "por que importa" e duas ou três opções concretas, com a recomendada primeiro. Ofereça "você decide" quando a escolha é de solution space e todas as opções atendem aos requisitos já escritos; a delegação vira decisão registrada. Teto: cinco perguntas por spec; da sexta em diante, a decisão vai direto para Perguntas em Aberto, com dono e o que bloqueia.
- **Codifique cada resposta na spec imediatamente,** como requisito, premissa ou fora de escopo. Decisão material sem resposta fica em Perguntas em Aberto, bloqueia só o que depende dela e nunca vira default.
- **A fronteira da mudança é fixa:** clarify esclarece *como* algo se comporta, nunca *se* uma capability nova entra.

## Dimensões implícitas

Percorra as dez dimensões abaixo, uma a uma, ao fechar o entendimento. Só o que gera requisito é escrito, e é escrito como requisito; o resto não deixa rastro.

- Validação de entrada e limites
- Falha e falha parcial: timeout, gravação parcial, compensação
- Idempotência, retry e duplicata
- Autorização e rate limit
- Concorrência e ordenação
- Ciclo de vida dos dados: retenção, exclusão
- Observabilidade
- Falha de dependência externa
- Integridade de transição de estado
- Consistência entre contextos: evento publicado, contrato consumido, eventual vs forte

## Requisitos em EARS

| Padrão | Template |
|---|---|
| Ubiquitous | The [system] SHALL [response] |
| Event-driven | WHEN [trigger] THEN the [system] SHALL [response] |
| State-driven | WHILE [state] the [system] SHALL [response] |
| Optional-feature | WHERE [feature is present] the [system] SHALL [response] |
| Unwanted-behavior | IF [undesired condition] THEN the [system] SHALL [response] |
| Complex | WHILE [state], WHEN [trigger] the [system] SHALL [response] |

- **Um padrão por requisito.** Todo requisito contém `SHALL` e um valor concreto (status code, mensagem, limite, prazo). "Rapidamente" e "apropriado" não são requisitos.
- **Um requisito é uma unidade verificável.** Obrigações que falham separadamente vão em requisitos separados; condição conjunta com efeito indivisível (gravar e publicar na mesma transação) fica num requisito só. O teste da unidade: dá para escrever um teste que afirme exatamente este resultado?
- **Keywords em inglês, corpo no idioma da spec:** `WHEN o investidor confirma a reserva THEN the system SHALL registrar a reserva com status Pendente em até 2s [BOOK-01]`.
- **Domain event relevante a outro contexto é requisito,** não detalhe de implementação. Edge case é requisito Unwanted-behavior, com ID como os outros.
- **IDs `<PREFIXO>-nn` desde o rascunho,** com dois ou mais dígitos e nunca reciclados. ID removido morre.

### Forma de escrita

Escreva a condição e a resposta em ordem direta, mantendo o padrão EARS aplicável. Nomeie o resultado definido pela fonte. Preserve IDs, referências ao PRD, keywords, valores e nomes de erro. Um requisito precisa de resultado observável; uma medida ausente exige a resolução prevista para lacunas, não um número escolhido para completar a frase. Uma edição de estilo não autoriza transformar registro de violação em rejeição de operação, nem acrescentar HTTP status, persistência ou evento.

## Spec viva

A spec é editada no lugar; a mudança é o diff.

- **Remover requisito:** apague a linha e acrescente o ID à linha `Aposentados: RSV-05, RSV-09` ao fim da spec; crie a linha na primeira aposentadoria. O linter recusa ID reutilizado e avisa número pulado que não consta dos aposentados.
- **Mudar significado:** edite o texto e mantenha o ID.
- **Substituir conceito:** aposente o ID e crie um novo.
- **Refactor sem mudança de comportamento** não toca a spec: o design ou as tasks citam os IDs que o refactor preserva, e os testes existentes são a evidência.

## Seções

Cada seção existe quando há o que dizer; o linter exige só Contexto e Requisitos e, quando há `prd:`, Rastreabilidade. A lista é fechada: `lint_spec.py` acusa como WARN — e não como HARD, porque spec real pode carregar seção herdada do PRD — a seção `##` fora dela. A coluna Seção (en) traz o heading da spec escrita em inglês (workflow.md, Idioma); nome separado por vírgula é forma alternativa aceita no mesmo idioma.

| Seção | Seção (en) | Conteúdo |
|---|---|---|
| Contexto | Context | 3–5 linhas: a origem (o PRD e o que foi corrigido nele; a ideia; ou o código e por que está sendo especificado), a base lida, e o que a capability produz e consome |
| Escopo e Fora de Escopo, Escopo | Scope / Out of Scope, Scope | O que entra; tabela item / razão para o que fica fora |
| Premissas | Assumptions | Tabela premissa / default / racional, cada linha marcada `[PREMISSA]` |
| Perguntas em Aberto | Open Questions | Pergunta, dono e o que ela bloqueia; a que bloqueia mais requisitos primeiro, em negrito |
| Requisitos | Requirements | Lista EARS com IDs; subtítulos `###` por tema a partir de 8 requisitos |
| Domain Events | Domain Events | Evento, produtor, consumidores, payload semântico, gatilho |
| Glossário | Glossary | Só termos de solution space; termo de domínio aponta para o glossário do PRD |
| Rastreabilidade | Traceability | Presente quando há PRD: de cada FR em escopo (ID do PRD citado por ao menos um requisito EARS) para os IDs EARS que o cobrem, e de cada cenário herdado para os IDs EARS que o cobrem; o linter confere FR e IDs EARS nas duas direções e a presença de cada cenário da tabela do PRD |
| Divergências | Divergences | Presente na origem código: o que o código faz e parece não dever, o que deveria fazer e não faz, dead code; cada item com `file:line` |

Exemplo didático completo de formato; dados, contratos e decisões abaixo não afirmam adoção pelo projeto.

## Template

```markdown
<!-- sdd: spec | capability: reservation-book/reservation-lifecycle | prd: /docs/prd/0002-reservation-book-reservation-lifecycle.md | prd-rev: git:3f9c2a1b7d0e4c5a9b8d7e6f0a1b2c3d4e5f6a7b -->
# Livro de Reservas

Prefixo dos requisitos: `RSV`.

## Contexto

Origem: [PRD 0002](../../../prd/0002-reservation-book-reservation-lifecycle.md).
A capability consome `OfferPublished` e `OfferClosed` e fornece o livro fechado ao Allocation por consulta (BOOK-16).
Base lida: `src/ReservationBook` tem só a composição do serviço.

## Escopo e Fora de Escopo

**Em escopo:** registro, alteração e cancelamento contra oferta `Open`; congelamento no fechamento.

| Fora de escopo | Razão |
|---|---|
| Rateio e condicionamento | Capability `allocation/book-processing` |

## Premissas

| Premissa | Default | Racional |
|---|---|---|
| [PREMISSA] Forma da rejeição | ProblemDetails 422 com `violations[]` | `AddApiDefaults()` já usa ProblemDetails; BOOK-09 exige todas as violações |

## Perguntas em Aberto

- **A prática da corretora permite ajustar a reserva até o fechamento?** Dono: autor do PRD. Bloqueia os requisitos de alteração de reserva, que só entram com a resposta.

## Requisitos

- **RSV-01** — WHEN o operador registra uma reserva sem violação de RSV-02 e RSV-03 THEN the system SHALL registrá-la em `Active` com instante e ordem de registro [BOOK-01]
- **RSV-02** — IF a oferta não está `Open` THEN the system SHALL registrar a violação `OFFER_NOT_ACCEPTING_RESERVATIONS` com regra BOOK-01 [BOOK-01]
- **RSV-03** — IF a posição do investidor com a nova reserva excede o investimento máximo THEN the system SHALL registrar a violação `POSITION_ABOVE_MAXIMUM` [BOOK-04]
- **RSV-04** — IF o mesmo registro chega duas vezes com o mesmo `idempotencyKey` THEN the system SHALL devolver a reserva original sem duplicar
- **RSV-05** — WHEN a reserva é aceita THEN the system SHALL atribuir ordem de registro estritamente crescente no livro da oferta [BOOK-14]

## Rastreabilidade

| ID do PRD | IDs EARS |
|---|---|
| BOOK-01 | RSV-01, RSV-02 |
| BOOK-04 | RSV-03 |
| BOOK-14 | RSV-05 |

| Cenário do PRD | IDs EARS |
|---|---|
| Segunda reserva dentro do máximo aceita | RSV-01 |
| Terceira reserva acima do máximo rejeitada | RSV-03 |
```

Depois de gravar a spec, rode `lint_spec.py <spec.md>` e siga o ciclo de correção de validation.md, Scripts.

### Exemplo didático parcial de reescrita

Fragmento de escrita; não é um artefato completo nem evidência de uma execução real.

```text
Antes: IF a posição do investidor com a nova reserva excede o investimento
máximo THEN the system SHALL proceder ao registro da violação
POSITION_ABOVE_MAXIMUM [BOOK-04]

Depois: IF a posição do investidor com a nova reserva excede o investimento
máximo THEN the system SHALL registrar a violação POSITION_ABOVE_MAXIMUM
[BOOK-04]

Preservado: condição, resposta, identificador e referência ao PRD.
```
