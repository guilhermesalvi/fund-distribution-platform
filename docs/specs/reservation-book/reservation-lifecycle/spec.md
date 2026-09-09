<!-- sdd: spec | capability: reservation-book/reservation-lifecycle | prd: /docs/prd/0002-reservation-book-reservation-lifecycle.md | prd-rev: git:af9ac063d126cb0334c58f22d314c9f0b3354fff -->
# Livro de Reservas

Prefixo dos requisitos: `RSV`.

## Contexto

Origem: [PRD 0002](../../../prd/0002-reservation-book-reservation-lifecycle.md). Mapa de contextos e catálogo de eventos: [PRD 0000](../../../prd/0000-platform-overview.md). A capability consome `OfferPublished`, `OfferClosed`, `OfferRevoked` e `BookProcessed`, não produz evento na v1, e fornece o livro fechado ao Allocation por consulta (BOOK-16).

Base lida: `src/ReservationBook` contém só a composição do serviço, sem domínio; testes são o esqueleto do xUnit. Convenções respeitadas: `.claude/rules/program-composition.md` e `.claude/rules/tracing.md`. Identificadores de categoria e de vínculo foram acrescentados ao glossário do PRD 0002 durante esta spec, porque a spec não inventa nome de enumeração.

## Escopo e Fora de Escopo

**Em escopo:** registro, alteração e cancelamento de reservas contra oferta `Open`; congelamento no fechamento; leitura do livro fechado pelo Allocation; aplicação do resultado por reserva; efeito da revogação; consultas do operador.

| Fora de escopo | Razão |
|---|---|
| Vedação a vinculadas, formação, condicionamento e rateio | Capability `allocation/book-processing` |
| Cadastro, identidade e autorização de investidor; verificação das declarações | Não-objetivos do PRD 0002; investidores vêm de seed |
| Efeito da categoria do investidor em regra | BOOK-05: na v1 a categoria não altera regra alguma |
| Forma da leitura do livro fechado pelo Allocation | Decisão delegada a ADR pelo PRD 0000, exigência BOOK-NFR-02; entra no Design |

## Premissas

| Premissa | Default | Racional |
|---|---|---|
| [PREMISSA] Forma da rejeição | ProblemDetails 422 com `violations[]` (`attribute`, `rule` = `BOOK-nn`); 409 para operação fora de oferta `Open` ou fora do período | Mesma forma da capability `offering/offer-lifecycle`; BOOK-09 exige todas as violações |
| [PREMISSA] Seed de investidores | Carregado pelo worker `DataMigration`; o contexto só consulta id e nome | PRD 0002: investidor tem apenas id e nome, por seed |
| [PREMISSA] Instante do registro | Relógio do serviço em UTC (`TimeProvider`), atribuído no aceite; a ordem de registro é um contador por oferta | BOOK-14 exige ordem total mesmo com instantes iguais |
| [PREMISSA] Resultado por reserva com itens inválidos | Itens válidos do `BookProcessed` são aplicados; cada item inválido é rejeitado e registrado individualmente | BOOK-19 fala do item, não do evento inteiro; rejeitar o evento inteiro deixaria o livro sem status por um item |
| [PREMISSA] Reentrega de evento | Evento com identificador já processado é registrado como duplicata e ignorado | Consumo assíncrono admite reentrega; BOOK-19 já protege as reservas terminais |

## Perguntas em Aberto

- **[PREMISSA] `BookProcessed` carrega o resultado de todas as reservas do livro fechado em uma única mensagem (ALLOC-26).** Se falsa, RSV-22 e RSV-23 deixam de ser atômicos por livro e o congelamento precisa de versão por lote. Validar no Design contra a spec de `allocation/book-processing` antes de Execute.
- A prática da corretora permite ajustar a reserva até o fechamento do livro interno (`[PREMISSA]` em Trade-offs do PRD 0002, Perguntas em Aberto do PRD)? Dono: autor do PRD. Se a resposta for não, RSV-13 a RSV-16 caem e entra um instante de confirmação. Bloqueia Design.
- Janela entre o fechamento antecipado no Offering (OFF-07) e a chegada de `OfferClosed` aqui: reserva aceita nessa janela tem instante posterior ao fechamento e viola BOOK-NFR-02. Dono: Design/ADR de transporte (OFF-NFR-03) e de leitura do livro (BOOK-NFR-02); se a ADR escolher entrega eventual, o PRD 0002 precisa dizer o destino dessa reserva. Fora do caminho da spec; ver Ponto de Maior Fragilidade.

## Requisitos

### Registro

- **RSV-01** — WHEN o operador registra uma reserva sem violação de RSV-02 a RSV-10 THEN the system SHALL registrá-la em `Active` com instante do registro e ordem de registro atribuídos [BOOK-01]
- **RSV-02** — IF a oferta não está `Open` ou o instante do registro está fora do período de reserva (intervalo fechado) THEN the system SHALL registrar a violação `OFFER_NOT_ACCEPTING_RESERVATIONS` com regra BOOK-01 [BOOK-01]
- **RSV-03** — IF o investidor informado não existe THEN the system SHALL registrar a violação `INVESTOR_NOT_FOUND` com regra BOOK-02 [BOOK-02]
- **RSV-04** — IF a quantidade reservada não é inteira ou é menor que o investimento mínimo por investidor THEN the system SHALL registrar a violação `QUANTITY_BELOW_MINIMUM` com regra BOOK-03 [BOOK-03]
- **RSV-05** — IF a posição do investidor, somando as reservas `Active` e a que está sendo registrada ou alterada, é maior que o investimento máximo THEN the system SHALL registrar a violação `POSITION_ABOVE_MAXIMUM` com a posição resultante e regra BOOK-04 [BOOK-04]
- **RSV-06** — IF a categoria está ausente ou fora de `Retail`, `Qualified`, `Professional` THEN the system SHALL registrar a violação `INVESTOR_CATEGORY_REQUIRED` com regra BOOK-05 [BOOK-05]
- **RSV-07** — IF a declaração `IsRelatedParty` está ausente THEN the system SHALL registrar a violação `RELATED_PARTY_DECLARATION_REQUIRED` com regra BOOK-06 [BOOK-06]
- **RSV-08** — IF categoria ou `IsRelatedParty` difere das declarações vigentes do investidor na oferta THEN the system SHALL registrar a violação `DECLARATION_MISMATCH` com regra BOOK-07 [BOOK-07]
- **RSV-09** — IF a oferta tem distribuição parcial e a opção está ausente ou fora de `acceptedConditioningOptions` THEN the system SHALL registrar a violação `CONDITIONING_OPTION_INVALID` com regra BOOK-08 [BOOK-08]
- **RSV-10** — IF a oferta não tem distribuição parcial e a reserva informa opção THEN the system SHALL registrar a violação `CONDITIONING_OPTION_NOT_APPLICABLE` com regra BOOK-08 [BOOK-08]
- **RSV-11** — IF o registro ou a alteração encontra violações THEN the system SHALL rejeitar sem alterar o livro e responder com a lista completa, cada uma com atributo e ID da regra [BOOK-09]
- **RSV-12** — WHEN uma reserva é aceita THEN the system SHALL atribuir ordem de registro estritamente crescente no livro da oferta, distinta mesmo entre reservas aceitas no mesmo instante [BOOK-14]

### Alteração e cancelamento

- **RSV-13** — WHILE a oferta está `Open` e o instante corrente está dentro do período, WHEN o operador altera quantidade, declarações ou opção de uma reserva `Active` THEN the system SHALL aplicar a alteração depois de validar RSV-03 a RSV-10, mantendo instante e ordem de registro [BOOK-10]
- **RSV-14** — WHEN uma alteração muda categoria ou `IsRelatedParty` THEN the system SHALL aplicar o novo valor a todas as reservas `Active` do investidor na oferta, com uma entrada de histórico em cada uma [BOOK-10]
- **RSV-15** — WHILE a oferta está `Open` e o instante corrente está dentro do período, WHEN o operador cancela uma reserva `Active` THEN the system SHALL passá-la a `Withdrawn` sem alterar as demais reservas do investidor [BOOK-11]
- **RSV-16** — IF alteração ou cancelamento é solicitado com a oferta fora de `Open` ou fora do período THEN the system SHALL rejeitar com `RESERVATION_IRREVOCABLE`, sem alterar a reserva [BOOK-12]
- **RSV-17** — WHEN uma alteração ou cancelamento é aplicado THEN the system SHALL registrar no histórico da reserva quem, o instante e cada campo com valor anterior e novo [BOOK-13]
- **RSV-18** — The system SHALL manter instante e ordem de registro inalterados em qualquer operação posterior ao aceite [BOOK-14]

### Fechamento e resultado

- **RSV-19** — WHEN `OfferPublished` é recebido THEN the system SHALL passar a aceitar reservas para a oferta com os limites, o período e `acceptedConditioningOptions` publicados [BOOK-01]
- **RSV-20** — WHEN `OfferClosed` é recebido THEN the system SHALL congelar o livro: as reservas `Active` no instante do fechamento formam o livro fechado e nenhuma entra, muda ou sai depois [BOOK-15]
- **RSV-21** — WHEN o Allocation consulta o livro fechado THEN the system SHALL responder com todas as reservas do livro fechado, cada uma com investidor, quantidade, categoria, `IsRelatedParty`, opção, instante e ordem de registro [BOOK-16]
- **RSV-22** — IF o livro fechado é consultado antes do congelamento THEN the system SHALL responder `BOOK_NOT_CLOSED` [BOOK-15]
- **RSV-23** — WHEN `BookProcessed` é recebido com desfecho formada THEN the system SHALL aplicar a cada reserva do livro fechado a quantidade alocada e o status derivado do motivo: `Filled` → `Filled`; `PartiallyFilledByCondition` ou `ScaledBack` → `PartiallyFilled`; `CancelledByCondition` → `CancelledByCondition`; `ExcludedRelatedParty` → `ExcludedRelatedParty` [BOOK-17]
- **RSV-24** — WHEN `BookProcessed` é recebido com desfecho não formada THEN the system SHALL passar toda reserva do livro fechado a `Void` com quantidade alocada 0 [BOOK-17]
- **RSV-25** — WHEN um resultado é aplicado THEN the system SHALL manter quantidade reservada, declarações e opção exatamente como estavam [BOOK-17]
- **RSV-26** — WHEN `OfferRevoked` é recebido THEN the system SHALL passar a `Void` toda reserva da oferta que não esteja `Withdrawn`, com quantidade alocada vigente 0 e o resultado anterior preservado no histórico; reserva já `Void` permanece [BOOK-18]
- **RSV-27** — IF um item de resultado aponta para reserva inexistente, `Withdrawn` ou em status terminal THEN the system SHALL rejeitar o item, registrá-lo com motivo e não alterar a reserva [BOOK-19]

### Consulta

- **RSV-28** — WHEN o operador consulta o livro de uma oferta THEN the system SHALL responder com a demanda acumulada e a lista de reservas com status e, quando houver, quantidade alocada [BOOK-20]
- **RSV-29** — WHEN o operador consulta as reservas de um investidor THEN the system SHALL responder com cada reserva, seu status e, após o processamento, a quantidade alocada [BOOK-21]

### Consistência e auditoria

- **RSV-30** — WHEN registro, alteração ou cancelamento é executado THEN the system SHALL validar contra a definição vigente da oferta e as demais reservas `Active` do investidor na mesma operação atômica [BOOK-NFR-01]
- **RSV-31** — IF duas operações concorrentes tocam reservas do mesmo investidor na mesma oferta THEN the system SHALL aplicá-las uma por vez, reavaliando a posição antes de aceitar a segunda [BOOK-NFR-01]
- **RSV-32** — IF um registro, alteração ou cancelamento é processado depois do congelamento THEN the system SHALL rejeitá-lo, mesmo que a requisição tenha começado antes [BOOK-NFR-02]
- **RSV-33** — WHEN qualquer mudança de reserva ou status é aplicada THEN the system SHALL registrar a origem (operador ou evento consumido) e o instante [BOOK-NFR-03]
- **RSV-34** — The system SHALL manter nome e demais dados do investidor fora de trace e log, usando as tags `app.reservation.id` e `app.offer.id` [BOOK-NFR-04]

## Rastreabilidade

| ID do PRD | IDs EARS |
|---|---|
| BOOK-01 | RSV-01, RSV-02, RSV-19 |
| BOOK-02 | RSV-03 |
| BOOK-03 | RSV-04 |
| BOOK-04 | RSV-05 |
| BOOK-05 | RSV-06 |
| BOOK-06 | RSV-07 |
| BOOK-07 | RSV-08 |
| BOOK-08 | RSV-09, RSV-10 |
| BOOK-09 | RSV-11 |
| BOOK-10 | RSV-13, RSV-14 |
| BOOK-11 | RSV-15 |
| BOOK-12 | RSV-16 |
| BOOK-13 | RSV-17 |
| BOOK-14 | RSV-12, RSV-18 |
| BOOK-15 | RSV-20, RSV-22 |
| BOOK-16 | RSV-21 |
| BOOK-17 | RSV-23, RSV-24, RSV-25 |
| BOOK-18 | RSV-26 |
| BOOK-19 | RSV-27 |
| BOOK-20 | RSV-28 |
| BOOK-21 | RSV-29 |
| BOOK-NFR-01 | RSV-30, RSV-31 |
| BOOK-NFR-02 | RSV-32; identidade livro lido = congelado é critério de design (ADR de leitura) |
| BOOK-NFR-03 | RSV-33 |
| BOOK-NFR-04 | RSV-34 |

Cenários herdados dos Critérios de Aceitação do PRD 0002, pelo FR que exercitam:

| Cenário do PRD | IDs EARS |
|---|---|
| 50 + 400 aceitas (posição 450), 60 rejeitada por BOOK-04, vinculado rejeitado por BOOK-07 | RSV-01, RSV-05, RSV-08 |
| Alterar vínculo cascateia para as duas reservas (BOOK-10) | RSV-14, RSV-17 |
| Reserva de 5 com opção 4 sem vínculo: três violações (BOOK-09) | RSV-04, RSV-07, RSV-09, RSV-11 |
| Oferta sem distribuição parcial com opção informada (BOOK-08) | RSV-10 |
| Oferta Draft, Fechada, Revogada ou fora do período (BOOK-01) | RSV-02 |
| 50 → 80 às 11h mantém instante e ordem (BOOK-13, BOOK-14) | RSV-13, RSV-17, RSV-18 |
| Cancelar após Fechada rejeitado (BOOK-12) | RSV-16 |
| Livro fechado só com Ativas; ordens distintas no mesmo instante (BOOK-16, BOOK-14) | RSV-12, RSV-21 |
| Resultado: 50 → 40 `PartiallyFilled`; 1 → 0 `PartiallyFilled`; excluída → 0; não formada → todas `Void` (BOOK-17) | RSV-23, RSV-24, RSV-25 |
| Revogada em Aberta e em Formada: `Void`, alocada 0, histórico preservado, `Withdrawn` intacta (BOOK-18) | RSV-26 |
| Resultado para `Withdrawn` rejeitado e registrado (BOOK-19) | RSV-27 |
| Demanda acumulada 480 com três Ativas (BOOK-20) | RSV-28 |

## Ponto de Maior Fragilidade

A decisão de **congelar o livro na chegada de `OfferClosed` (RSV-20), tomando o instante carregado pelo evento como corte, e rejeitar operações posteriores (RSV-32)**.

*Vetor de ataque:* o fechamento antecipado acontece no Offering em `t`; até o evento chegar aqui, uma reserva aceita em `t + δ` passa por RSV-02 (a oferta ainda parece `Open`) e entra num livro que o Offering considera fechado, violando BOOK-NFR-02. Rejeitar retroativamente não tem status no PRD; deixar entrar corrompe a entrada do Allocation. A spec empurra o problema para o Design (OFF-NFR-03: estado igual para todos os consumidores em qualquer instante), e se a ADR de transporte escolher entrega eventual, a spec fica sem regra para essa reserva.

*Desafie antes de aprovar:* o registro deve consultar o estado da oferta no Offering de forma síncrona a cada aceite, pagando latência e acoplamento, ou o transporte garante que `OfferClosed` chega antes de qualquer aceite posterior ao fechamento? A resposta fixa a ADR e decide se o PRD 0002 precisa de um destino para a reserva aceita na janela.
