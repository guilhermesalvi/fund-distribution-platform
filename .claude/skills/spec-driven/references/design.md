# Design

**Objetivo:** definir *como* construir (estrutura, componentes, interfaces, o que reusar) com profundidade proporcional ao **risco**, não ao tamanho. Design não decide comportamento: se precisar, volte à spec.

Pré-requisito: spec commitada. Grave em `<capability>/NNNN-<change-slug>/design.md` (layout em specify.md, Layout).

## Carregar contexto

1. `spec.md` da capability: é o contrato; o design não a reinterpreta.
2. ADRs ativas em `/docs/adr`: cada uma é restrição de projeto. Conflito entre uma decisão anterior e o melhor para esta feature exige escolha explícita: conformar ou superseder (adr.md). Ignorar em silêncio cria inconsistência invisível entre features.
3. PRD, quando existe: Trade-offs Declarados e Dependências e Riscos são restrições e fonte de riscos; NFRs são a origem primeira dos critérios de avaliação. PRD 0000: o mapa de contextos fixa quem é upstream e a direção de mudança de contrato; o catálogo de eventos fixa produtor e consumidores; as decisões delegadas a ADR são decisões deste design ou de ADR própria.

## Base de código

Não leia tudo; a spec é o guia de foco.

1. Identifique módulos e arquivos ligados ao escopo; leia a estrutura de diretórios antes de abrir arquivos.
2. Ordem: interfaces e contratos → entidades de domínio → serviços e casos de uso → infraestrutura. Implementação completa só quando assinatura e nome não bastam.
3. Declare o que foi lido e o que foi ignorado: "Analisei X, Y, Z. A e B ficaram fora e podem conter restrições não consideradas."
4. O que a base impõe é fato; o que você inferiu de padrão é `[PREMISSA]`. Padrão visto em dois arquivos não é convenção do projeto.
5. Preocupação encontrada (acoplamento, dívida, segredo exposto, N+1, lacuna de teste no caminho) vira linha em Riscos, com mitigação ou aceite. Preocupação vira `[PREMISSA]` até achar a decisão que a explica (ADR, commit, PR): um desenho que parece errado hoje pode ter sido o melhor sob as restrições da época.
6. Reuso: cada componente novo referencia o existente que segue; componente sem reuso justifica por quê.

## Risco → técnica

Antes de preencher seções, liste o que pode falhar caro nesta mudança (dimensões da spec, preocupações da base, integrações, dinheiro, regulação, contrato público, migração). Para cada risco, escolha a técnica que o reduz e só faça aquele trabalho. Risco sem técnica é aceite registrado ("aceito porque").

| Risco típico | Técnica proporcional |
|---|---|
| Consistência entre contextos, evento perdido | Contrato de domain event explícito; eventual vs forte decidido; outbox ou equivalente |
| Concorrência, duplicata, retry | Modelo de idempotência; chave; lock otimista; tabela de transições |
| Integração externa instável | Anti-corruption layer; timeout, retry e circuit breaker declarados; fallback |
| Dinheiro, cálculo financeiro | Tipos de valor; regras isoladas e testáveis; precisão decimal declarada |
| Migração, compatibilidade | Estratégia de migração; dupla escrita; rollback |
| Performance | Orçamento (p95, throughput) e onde é gasto; índice; paginação |
| Segurança, dado regulado | Fronteira de autorização; retenção; mascaramento; auditoria |

Não imponha estilo arquitetural: o design fala a língua da base (ports e adapters, aggregates, ou o que houver). Introduzir estilo novo é decisão de projeto (adr.md). Cerimônia sem risco que a justifique é peso morto.

## Critérios antes das abordagens

Quem propõe e julga é o mesmo agente; critério escrito depois da proposta vira racionalização.

1. **Critérios**, cada um com origem (NFR do PRD, dimensão da spec, ADR, custo ou prazo). Critério é atributo de qualidade ou restrição, nunca mecanismo: "sem ponto único de falha", não "usar Bloom filter".
2. **Crítica dos critérios.** Que critério falta para este tipo de problema (falso positivo em segurança, frescor do dado, custo de operação)? Que trade-off decide a escolha e não está fixado? Critério de negócio ausente volta ao PRD como pergunta; critério de solution space o usuário fixa aqui. Apresente e espere antes de propor abordagem.
3. **Abordagens**, só quando há alternativa real: 2–3 materialmente viáveis, mesmo escopo, avaliadas contra os critérios (colunas da tabela) e as quatro perguntas abaixo; recomendada primeiro, com racional; confirmada antes de detalhar componentes. Sem alternativa real, uma linha dizendo isso e a seção não existe.

As quatro perguntas de uma decisão arquitetural: atende aos objetivos de negócio? Respeita os atributos de qualidade? Respeita as restrições (ADRs, base, regulação, time)? **Existe forma mais barata ou menos arriscada de fazer o mesmo?** A quarta é sempre respondida: complexidade (componentes × interconexões) é custo, e complexidade não justificada é custo desnecessário.

## Componentes, contratos e dados

- **Componentes.** Propósito em uma frase (sem "e"), path real, interfaces com tipos, dependências, o que reusa. Interfaces vêm antes da implementação: são o que as tasks consomem.
- **Domain events.** Por evento: produtor, consumidores conhecidos, payload semântico, chave de partição ou ordenação, garantia de entrega (at-least-once é o normal; idempotência do consumidor torna a reentrega segura), versionamento. Evento mal documentado é acoplamento implícito entre contextos.
- **Modelo de dados** quando a feature toca persistência: entidades, relacionamentos, invariantes, migração.
- **Tratamento de erro.** Cenário (ID), tratamento, impacto. Todo `IF … THEN` da spec aparece aqui com o mecanismo escolhido.

## Unidade de deploy e reuso

Três conceitos distintos: **módulo** (fronteira de código: assembly, pacote, namespace com interface pública), **pacote de release** (o que é versionado e publicado) e **unidade de deploy** (o que sobe e cai junto). Diga de qual está falando.

Ordem de preferência: mudança no deployável existente → módulo novo no deployável existente → deployável novo. O que justifica deployável novo é demanda de **deploy independente** (time com ritmo próprio, stack diferente, estrangulamento de legado); escalabilidade, resiliência e "separação de responsabilidades" não justificam sozinhos, porque réplica e módulo entregam. Deployável novo carrega contrato de interface, versionamento, compatibilidade retroativa e um dono nomeado.

Biblioteca compartilhada só com dono, estabilidade (o custo de release contra o custo de divergência) e ausência de pacote público equivalente; sem regra de negócio em biblioteca de plataforma; `Utils`/`Shared` como destino é o cheiro da regra não aplicada. Sem ciclo entre módulos com fronteira própria; módulo é consumido só pela sua interface pública.

Desvio da ordem de preferência registra o porquê na tabela de Decisões técnicas, não em seção própria.

## Decisões técnicas

Só as não óbvias: decisão, escolha, racional, tipo. O tipo distingue **contrato público** (API, evento, formato persistido ou exposto a terceiros: muda com versionamento e aviso) de **decisão interna** (muda sem aviso). Decisão que fixa convenção, restrição ou padrão para features futuras vira ADR (adr.md); local à feature fica só na tabela.

## Seções

Cada seção existe quando há o que dizer; nenhuma seção vazia.

Contexto de design (restrições da spec, do PRD e das ADRs; base lida vs ignorada) · Critérios de avaliação · Riscos e técnicas · Abordagens (quando há alternativa) · Visão da arquitetura · Unidade de deploy (uma linha quando fica no existente) · Componentes · Domain Events · Modelo de dados · Tratamento de erros · Decisões técnicas · Arquivos a criar ou modificar (insumo direto do tasks.md).

## Template

```markdown
<!-- sdd: design | spec: ../spec.md -->
# Reserva Parcial — Design

## Contexto de design

Spec: RSV-07 a RSV-12. ADR 0001 (outbox) restringe a publicação de eventos. Base lida: `src/ReservationBook/Reservations/*`; ignorado: `src/ReservationBook/Reports/*`.

## Critérios de avaliação

| # | Critério | Origem |
|---|---|---|
| C1 | O livro lido pelo Allocation é idêntico ao congelado | BOOK-NFR-02 |
| C2 | Resultado visível em até 5s após `BookProcessed` | usuário, nesta sessão |

## Riscos e técnicas

| Risco | Fonte | Técnica | Onde |
|---|---|---|---|
| Duplicata por retry do canal | RSV-10 | Idempotency key persistida; unicidade (investorId, offerId) | `ReservationService` |

## Visão da arquitetura

[Parágrafo; diagrama quando a estrutura é um grafo.]

## Unidade de deploy

Fica em `src/ReservationBook`.

## Componentes

### ReservationService
- **Propósito:** aceitar e alterar reservas contra a oferta publicada.
- **Localização:** `src/ReservationBook/Reservations/ReservationService.cs`
- **Interfaces:** `Place(PlaceReservation cmd, CancellationToken ct): Task<Result<Reservation, ReservationError>>`
- **Dependências:** `IOfferReader`, `IReservationStore`
- **Reusa:** `src/ServiceDefaults/TraceAsync.cs`

## Tratamento de erros

| Cenário (ID) | Tratamento | Impacto |
|---|---|---|
| Posição acima do máximo (RSV-11) | `Result.Failure(POSITION_ABOVE_MAXIMUM)`; 422 no endpoint | Operador vê a posição resultante |

## Decisões técnicas

| Decisão | Escolha | Racional | Tipo |
|---|---|---|---|
| Ordem de registro | Contador por oferta, não instante | BOOK-14 exige ordem total com instantes iguais | interna |

## Arquivos a criar ou modificar

- `src/ReservationBook/Reservations/ReservationService.cs` — novo
- `tests/UnitTests/Reservations/ReservationServiceTests.cs` — novo
```

Apresente e espere antes de Tasks.
