# Design

**Objetivo:** definir *como* construir — estrutura, componentes, interfaces e o que reusar — com profundidade proporcional ao **risco** da mudança, não ao seu tamanho. O design não decide comportamento: se uma decisão de comportamento for necessária, volte à spec e resolva lá.

Pré-requisito: a spec está commitada. Grave o design em `<capability>/NNNN-<change-slug>/design.md`; o layout de pastas e o comentário de máquina estão descritos em specify.md (specify.md, Layout).

## Carregar contexto

Leia, nesta ordem, antes de projetar:

1. **A `spec.md` da capability.** É o contrato; o design não a reinterpreta.
2. **As ADRs ativas em `/docs/adr`.** Cada uma é uma restrição de projeto. Quando uma decisão anterior conflita com o que seria melhor para esta feature, a escolha é explícita: conformar-se à ADR ou supersedê-la, pelo procedimento descrito em adr.md. Ignorar a ADR em silêncio cria inconsistência invisível entre features.
3. **O PRD, quando existe.**
   - As seções Trade-offs Declarados e Dependências e Riscos são restrições do design e fonte de riscos.
   - Os NFRs são a origem primeira dos critérios de avaliação.
   - No PRD 0000: o mapa de contextos fixa quem é upstream e a direção de mudança de contrato; o catálogo de eventos fixa o produtor e os consumidores de cada evento; as decisões delegadas a ADR são decisões deste design ou de uma ADR própria.

## Base de código

Não leia a base inteira; a spec é o guia de foco.

1. Identifique os módulos e arquivos ligados ao escopo. Leia a estrutura de diretórios antes de abrir qualquer arquivo.
2. Leia nesta ordem: interfaces e contratos; entidades de domínio; serviços e casos de uso; infraestrutura. Abra a implementação completa só quando assinatura e nome não bastam.
3. Declare o que foi lido e o que foi ignorado, na forma: "Analisei X, Y, Z. A e B ficaram fora e podem conter restrições não consideradas."
4. Separe fato de inferência: o que a base impõe é fato; o que você inferiu de um padrão é `[PREMISSA]`. Padrão visto em menos de três arquivos da mesma camada não é convenção do projeto.
5. Toda preocupação encontrada na base (acoplamento, dívida, segredo exposto, N+1, lacuna de teste no caminho da mudança) vira uma linha na seção Riscos, com mitigação ou aceite. Enquanto você não encontra a decisão que explica o desenho (ADR, commit, PR), essa preocupação fica marcada como `[PREMISSA]`: um desenho que parece errado hoje pode ter sido o melhor sob as restrições da época.
6. Reuso: cada componente novo referencia o componente existente que ele segue; componente sem reuso justifica por quê.

## Do risco à técnica

Antes de preencher as seções do design, liste o que pode falhar caro nesta mudança. Percorra as sete fontes: as dimensões implícitas da spec, as preocupações encontradas na base, integrações, dinheiro, regulação, contrato público e migração. Para cada risco, escolha a técnica que o reduz e faça só aquele trabalho. Risco sem técnica é um aceite registrado, na forma "aceito porque …".

| Risco típico | Técnica proporcional |
|---|---|
| Consistência entre contextos, evento perdido | Contrato de domain event explícito; eventual vs forte decidido; outbox ou equivalente |
| Concorrência, duplicata, retry | Modelo de idempotência; chave; lock otimista; tabela de transições |
| Integração externa instável | Anti-corruption layer; timeout, retry e circuit breaker declarados; fallback |
| Dinheiro, cálculo financeiro | Tipos de valor; regras isoladas e testáveis; precisão decimal declarada |
| Migração, compatibilidade | Estratégia de migração; dupla escrita; rollback |
| Performance | Orçamento (p95, throughput) e onde é gasto; índice; paginação |
| Segurança, dado regulado | Fronteira de autorização; retenção; mascaramento; auditoria |

Não imponha estilo arquitetural: o design fala a língua da base (ports e adapters, aggregates, ou o que houver nela). Introduzir um estilo novo é decisão de projeto e segue adr.md. Cerimônia sem risco que a justifique é peso morto.

## Critérios antes das abordagens

Quem propõe e quem julga é o mesmo agente; por isso, critério escrito depois da proposta vira racionalização. A ordem é fixa: critérios, crítica dos critérios e só então abordagens.

1. **Critérios.** Cada critério tem origem declarada: NFR do PRD, dimensão da spec, ADR, custo ou prazo. Critério é atributo de qualidade ou restrição, nunca mecanismo: "sem ponto único de falha" é critério; "usar Bloom filter" não é.
2. **Crítica dos critérios.** Pergunte: que critério falta para este tipo de problema (falso positivo em segurança, frescor do dado, custo de operação)? Que trade-off decide a escolha e ainda não está fixado? Critério de negócio ausente volta ao PRD como pergunta; critério de solution space é o usuário quem fixa, aqui no design. Apresente os critérios e a crítica e espere a resposta antes de propor qualquer abordagem. Quando todos os critérios vêm de NFR do PRD, a crítica não encontrou lacuna e não há alternativa real, apresente critérios e abordagem juntos, numa única espera.
3. **Abordagens.** Alternativa real é a abordagem que atende a todos os critérios e troca de lugar com a recomendada em pelo menos um deles; a seção existe só quando há uma. Nesse caso, apresente 2–3 abordagens materialmente viáveis, com o mesmo escopo, avaliadas contra os critérios (que são as colunas da tabela) e contra as quatro perguntas abaixo. A recomendada vem primeiro, com o racional, e é confirmada pelo usuário antes de você detalhar componentes. Sem alternativa real, a seção não existe; a última linha de Critérios de avaliação diz "Sem alternativa real: <motivo em uma frase>".

### As quatro perguntas de uma decisão arquitetural

1. Atende aos objetivos de negócio?
2. Respeita os atributos de qualidade?
3. Respeita as restrições (ADRs, base, regulação, time)?
4. **Existe forma mais barata ou menos arriscada de fazer o mesmo?**

A quarta é sempre respondida: complexidade (componentes × interconexões) é custo, e complexidade não justificada é custo desnecessário.

## Componentes, contratos e dados

- **Componentes.** Para cada componente: propósito em uma frase (sem "e"), path real, interfaces com tipos, dependências e o que reusa. As interfaces vêm antes da implementação: são o que as tasks consomem.
- **Domain events.** Para cada evento: produtor, consumidores conhecidos, payload semântico, chave de partição ou de ordenação, garantia de entrega e versionamento. At-least-once é a garantia normal; a idempotência do consumidor é o que torna a reentrega segura. Evento mal documentado é acoplamento implícito entre contextos.
- **Modelo de dados.** Presente quando a feature toca persistência: entidades, relacionamentos, invariantes e migração.
- **Tratamento de erro.** Uma linha por cenário: cenário (com o ID do requisito), tratamento e impacto. Todo `IF … THEN` da spec aparece aqui, com o mecanismo escolhido para tratá-lo.

## Unidade de deploy e reuso

### Três conceitos

São conceitos distintos; diga sempre de qual está falando:

- **Módulo:** fronteira de código — assembly, pacote ou namespace com interface pública.
- **Pacote de release:** o que é versionado e publicado.
- **Unidade de deploy:** o que sobe e cai junto.

### Ordem de preferência

1. Mudança no deployável existente.
2. Módulo novo no deployável existente.
3. Deployável novo.

O que justifica um deployável novo é demanda de **deploy independente**: time com ritmo próprio, stack diferente, estrangulamento de legado. Escalabilidade, resiliência e "separação de responsabilidades" não justificam sozinhos, porque réplica e módulo entregam o mesmo. Um deployável novo carrega contrato de interface, versionamento, compatibilidade retroativa e um dono nomeado.

Desvio da ordem de preferência registra o porquê na tabela de Decisões técnicas, não em seção própria.

### Biblioteca compartilhada e fronteiras de módulo

- Biblioteca compartilhada só entra com três condições: um dono; estabilidade, avaliada pelo custo de release contra o custo de divergência; e ausência de pacote público equivalente.
- Regra de negócio não vive em biblioteca de plataforma. `Utils` ou `Shared` como destino é o cheiro dessa regra não aplicada.
- Sem ciclo entre módulos com fronteira própria; um módulo é consumido só pela sua interface pública.

## Decisões técnicas

Registre só as decisões em que outra escolha era defensável, em tabela com quatro colunas: decisão, escolha, racional e tipo. O tipo distingue:

- **Contrato público:** API, evento, formato persistido ou exposto a terceiros. Muda com versionamento e aviso.
- **Decisão interna:** muda sem aviso.

Decisão que fixa convenção, restrição ou padrão para features futuras vira ADR, no formato de adr.md; decisão local à feature fica só na tabela.

## Seções

Cada seção existe quando há o que dizer; nenhuma seção vazia. Na ordem do documento:

1. Contexto de design — restrições da spec, do PRD e das ADRs; base lida e base ignorada.
2. Critérios de avaliação.
3. Riscos e técnicas.
4. Abordagens — só quando há alternativa real.
5. Visão da arquitetura.
6. Unidade de deploy — uma linha quando a mudança fica no deployável existente.
7. Componentes.
8. Domain Events.
9. Modelo de dados.
10. Tratamento de erros.
11. Decisões técnicas.
12. Arquivos a criar ou modificar — insumo direto do `tasks.md`.

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

Depois de gravar, rode `lint_design.py <design.md> --spec <spec.md>` e siga o ciclo de correção de SKILL.md, Scripts; depois apresente o design e espere antes de começar as Tasks.
