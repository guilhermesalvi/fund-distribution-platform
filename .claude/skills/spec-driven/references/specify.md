# Specify

**Objetivo:** capturar *o quê* construir como requisitos testáveis e rastreáveis: o contrato que o Design refina, as Tasks decompõem e o Verify audita. A spec vive no solution space; a regra de negócio vive no PRD.

## Layout

```
/docs/specs/<domain-slug>/<capability-slug>/
├── spec.md                      # spec viva, editada no lugar
└── NNNN-<change-slug>/          # só quando a mudança pede design ou tasks
    ├── design.md
    └── tasks.md
/docs/adr/NNNN-<slug>.md         # decisão de projeto (adr.md)
```

- Slugs em inglês, kebab-case, espelhando o nome que o código usa (`PartialReservation` vira `partial-reservation`). Capability é uma área funcional de um bounded context (`reservation-book/reservation-lifecycle`).
- `NNNN` é contador dentro da capability: leia a pasta e use max+1. A pasta da mudança só existe quando há `design.md` ou `tasks.md`; nunca scaffolde artefato vazio.
- Git é o controle de versão: o diff é o delta, o log é o histórico. Árvore suja é trabalho em elaboração; arquivo commitado é a versão válida. Nenhum campo de status, autor, data ou aprovação.
- Comentário de máquina na primeira linha, antes do `#`, em ASCII minúsculo:
  - `<!-- sdd: spec | capability: offering/offer-lifecycle | prd: /docs/prd/0001-offering-offer-lifecycle.md | prd-rev: git:<hash> -->`
  - `<!-- sdd: design | spec: ../spec.md -->`
  - `<!-- sdd: tasks | spec: ../spec.md | design: ./design.md -->` (`design:` só quando existe; `scope: RSV-07, RSV-10` quando a mudança toca só parte dos requisitos)
  - `prd:` e `prd-rev:` só quando há PRD; `prd-rev` é `git hash-object <prd.md>` do PRD commitado. Se o PRD mudar depois, o linter avisa: re-derive os requisitos que citam os IDs tocados e atualize o hash.
- Logo abaixo do `#`, a linha `Prefixo dos requisitos: \`RSV\`.` Nada mais de cabeçalho.

## Origem

| Sinal no pedido | Origem | O que é fato | Cuidado |
|---|---|---|---|
| PRD em `/docs/prd` | PRD | O texto sem tag do PRD; `[PREMISSA]` do PRD continua `[PREMISSA]` aqui | Seis regras abaixo |
| Sem PRD, mas usuário-alvo, problema e comportamento observável estão no pedido | Ideia | O que o usuário afirmou | Registre usuário, problema e resultado no Contexto; se faltar usuário ou problema, pare |
| Solution-first sem usuário nem problema ("CRUD para X", "tela de Y") | — | — | "Isso precisa de PRD antes" e pare |
| Código existente sem spec ("documente a spec do módulo X") | Código | O que o código *faz* (comportamento, testes, docs) | Intenção inferida é `[PREMISSA]`; comportamento sem justificativa de negócio é `[LACUNA]`; divergências em seção própria; leitura da base em design.md, Base de código |

**A partir do PRD, seis regras:**

1. O requisito EARS cita o ID do PRD ao fim da linha (`[BOOK-04]`) e não reescreve a regra: descreve o comportamento observável que a realiza (valor, status, evento, prazo). Regra em dois lugares diverge. Estado, evento e enumeração usam o identificador que o PRD fixa.
2. Lacuna ou inconsistência de regra de negócio se corrige no PRD, nunca vira premissa na spec. `[PREMISSA]` na spec é só de solution space (formato de erro, prazo técnico, ordem de processamento).
3. O prefixo da spec é distinto de todo prefixo de PRD e não confundível com ele (`OFR` ao lado de `OFF` convida a erro; prefira sigla de outra raiz). O linter acusa colisão lendo `/docs/prd`.
4. PRD 0000, quando existe, fornece o mapa de contextos, o catálogo de eventos e as decisões delegadas a ADR: evento que a capability produz ou consome vira requisito citando o ID que o governa; decisão delegada entra em Perguntas em Aberto com dono "Design/ADR".
5. NFR com resultado observável por teste (prazo, atomicidade, registro de auditoria) vira requisito EARS citando o `X-NFR-nn`. NFR que é atributo de qualidade sem teste direto vira critério de design (design.md, Critérios) e aparece na Rastreabilidade como tal.
6. Os cenários dos Critérios de Aceitação do PRD são a suíte mínima que o Execute reproduz: a Rastreabilidade os lista pelo nome do caso (primeira coluna da tabela do PRD) ou pelo FR que exercitam, com os IDs EARS que os cobrem. Aceitar a entrada válida e rejeitar a inválida são cenários e requisitos distintos.

Em qualquer origem, leia antes de escrever: a `spec.md` viva da capability, se existir, e as ADRs ativas em `/docs/adr` (restringem o que a spec pode pedir).

## Clarify

- Varra a base antes de perguntar: código vizinho, padrões, features irmãs. Use o que encontrar para ancorar as perguntas, não para limitar a spec ao que existe.
- Você é par técnico, não entrevistador. Desafie vagueza ("rápido" é quanto? "usuários" são quem?); torne o abstrato concreto ("me conduz por um uso disso").
- Pergunte só quando a resposta muda arquitetura, modelo de dados, decomposição, desenho de teste ou aceitação. O que o código ou o PRD responde não se pergunta; preferência estilística não se pergunta.
- Uma pergunta por vez: interrogativa completa, uma linha de "por que importa", opções concretas com a recomendada primeiro. Ofereça "você decide" quando razoável; a delegação vira decisão registrada.
- Codifique cada resposta na spec imediatamente (requisito, premissa ou fora de escopo). Decisão material sem resposta fica em Perguntas em Aberto, bloqueia só o que depende dela e nunca vira default.
- A fronteira da mudança é fixa: clarify esclarece *como* algo se comporta, nunca *se* uma capability nova entra.

## Dimensões implícitas

Percorra a lista ao fechar o entendimento. Só o que gera requisito é escrito, e é escrito como requisito; o resto não deixa rastro.

Validação de entrada e limites · falha e falha parcial (timeout, gravação parcial, compensação) · idempotência, retry e duplicata · autorização e rate limit · concorrência e ordenação · ciclo de vida dos dados (retenção, exclusão) · observabilidade · falha de dependência externa · integridade de transição de estado · consistência entre contextos (evento publicado, contrato consumido, eventual vs forte).

## Requisitos em EARS

| Padrão | Template |
|---|---|
| Ubiquitous | The [system] SHALL [response] |
| Event-driven | WHEN [trigger] THEN the [system] SHALL [response] |
| State-driven | WHILE [state] the [system] SHALL [response] |
| Optional-feature | WHERE [feature is present] the [system] SHALL [response] |
| Unwanted-behavior | IF [undesired condition] THEN the [system] SHALL [response] |
| Complex | WHILE [state], WHEN [trigger] the [system] SHALL [response] |

- Um padrão por requisito; todo requisito contém `SHALL` e valor concreto (status code, mensagem, limite, prazo). "Rapidamente" e "apropriado" não são requisitos.
- Um requisito = uma unidade verificável: obrigações que falham separadamente vão em requisitos separados; condição conjunta e efeito indivisível (gravar e publicar na mesma transação) ficam juntos. Teste: dá para escrever um teste que afirme exatamente este resultado?
- Keywords em inglês, corpo no idioma da spec: `WHEN o investidor confirma a reserva THEN the system SHALL registrar a reserva com status Pendente em até 2s [BOOK-01]`.
- Domain event relevante a outro contexto é requisito, não detalhe de implementação. Edge case é requisito Unwanted-behavior com ID como os outros.
- IDs `<PREFIXO>-nn` desde o rascunho, dois ou mais dígitos, nunca reciclados. ID removido morre.

## Spec viva

A spec é editada no lugar; a mudança é o diff.

- Remover requisito: apague a linha e acrescente o ID à linha `Aposentados: RSV-05, RSV-09` ao fim da spec (crie a linha na primeira aposentadoria). O linter recusa ID reutilizado e avisa número pulado sem aposentadoria.
- Mudar significado: edite o texto e mantenha o ID.
- Substituir conceito: aposente o ID e crie um novo.
- Refactor sem mudança de comportamento não toca a spec: o design ou as tasks citam os IDs que o refactor preserva e os testes existentes são a evidência.

## Seções

Cada seção existe quando há o que dizer; o linter exige só Contexto e Requisitos.

| Seção | Conteúdo |
|---|---|
| Contexto | 3–5 linhas: origem (PRD e o que foi corrigido nele, ideia, ou código e por que está sendo especificado), base lida, o que a capability produz e consome |
| Escopo e Fora de Escopo | O que entra; tabela item / razão do que fica fora |
| Premissas | Tabela premissa / default / racional, cada linha `[PREMISSA]` |
| Perguntas em Aberto | Pergunta, dono, o que bloqueia; a mais pesada primeiro, em negrito |
| Requisitos | Lista EARS com IDs; subtítulos `###` por tema quando ajudam a leitura |
| Domain Events | Evento, produtor, consumidores, payload semântico, gatilho |
| Glossário | Só termos de solution space; termo de domínio aponta o glossário do PRD |
| Rastreabilidade | PRD → EARS (cada FR em escopo) e cenários herdados → EARS; presente quando há PRD |
| Divergências | Origem código: o que o código faz e parece não dever, o que deveria e não faz, dead code; cada item com `file:line` |

## Template

```markdown
<!-- sdd: spec | capability: reservation-book/reservation-lifecycle | prd: /docs/prd/0002-reservation-book-reservation-lifecycle.md | prd-rev: git:3f9c2a1b7d0e4c5a9b8d7e6f0a1b2c3d4e5f6a7b -->
# Livro de Reservas

Prefixo dos requisitos: `RSV`.

## Contexto

Origem: [PRD 0002](../../../prd/0002-reservation-book-reservation-lifecycle.md). A capability consome `OfferPublished` e `OfferClosed` e fornece o livro fechado ao Allocation por consulta (BOOK-16). Base lida: `src/ReservationBook` tem só a composição do serviço.

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

- **A prática da corretora permite ajustar a reserva até o fechamento?** Dono: autor do PRD. Bloqueia RSV-13 a RSV-16.

## Requisitos

### Registro

- **RSV-01** — WHEN o operador registra uma reserva sem violação de RSV-02 a RSV-05 THEN the system SHALL registrá-la em `Active` com instante e ordem de registro [BOOK-01]
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

Depois: `lint_spec.py <spec.md>`; corrija, rode de novo, apresente.
