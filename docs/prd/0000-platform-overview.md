<!-- prd: overview -->
# Visão Geral da Plataforma

| | |
|---|---|
| **Scope** | Propósito, mapa de contextos, catálogo de eventos e fluxos entre contextos; regras de negócio pertencem aos PRDs donos e são referenciadas por ID. |

## Purpose

A plataforma demonstra um recorte executável da distribuição de cotas de classe fechada por uma corretora a investidores finais, com base nas Resoluções CVM 160 e CVM 175. O operador atua em nome do investidor; liquidação financeira e integrações externas ficam fora do modelo. O projeto não tem uso em produção: suas métricas medem correção por cenários e invariantes verificáveis. O recorte e as decisões de produto são do autor e estão registrados nos PRDs de domínio, junto com as fontes normativas.

## Contexts

| Contexto | Responsabilidade | PRD | Prefixo de ID | Posição |
|---|---|---|---|---|
| Offering | Definição imutável da oferta e sua máquina de estados (OFF-01 a OFF-33) | [0001](0001-offering-offer-lifecycle.md) | `OFF` | Upstream: o BookBuilding consome a definição e o estado e não os altera; o Offering consome o desfecho só para terminar o ciclo. |
| BookBuilding | Reservas contra oferta Aberta, livro congelado no fechamento, processamento único do livro fechado (vedação a vinculadas, formação, condicionamento e rateio) e status por reserva (BOOK-01 a BOOK-18, BOOK-20, BOOK-21, ALLOC-01 a ALLOC-26) | [0002](0002-book-building-bid-lifecycle.md) ciclo de vida da reserva; [0003](0003-book-building-book-processing.md) processamento do livro | `BOOK`, `ALLOC` | Contexto core: consome o Offering e devolve o desfecho. |

Cada contexto mantém sua persistência; as relações usam eventos. O Offering permanece upstream para mudanças incompatíveis de contrato. O BookBuilding tem um PRD por capability, cada um com seu prefixo; o desfecho do livro, formada ou não formada, pertence a ele (OFF-30), e o Offering o consome para encerrar o ciclo (OFF-31 a OFF-33).

Os requisitos são citados pelo prefixo e número; sua definição ocorre somente no PRD dono. Identificadores de domínio seguem os glossários desses documentos.

## Event Catalog

| Evento | Produtor | Consumidores | Gatilho | IDs |
|---|---|---|---|---|
| `OfferPublished` | Offering | BookBuilding | Publicação; inclui a definição completa | OFF-03, BOOK-01 |
| `OfferClosed` | Offering | BookBuilding | Fechamento pelo operador | OFF-07, BOOK-15, ALLOC-01 |
| `OfferRevoked` | Offering | BookBuilding | Revogação pelo operador em Aberta ou Fechada | OFF-12, BOOK-18, ALLOC-03 |
| `BookProcessed` | BookBuilding | Offering | Conclusão do processamento; carrega desfecho, `D`, `Dn`, `D'`, `E`, ramo e resultado por reserva | ALLOC-26, OFF-31 a OFF-33 |

Todo evento identifica a oferta, o estado resultante da operação e seu instante. Em `BookProcessed`, o estado comunicado é o desfecho do processamento; a aceitação no Offering segue OFF-33. A definição completa acompanha `OfferPublished`; a informação do processamento segue ALLOC-26. Encerrada não tem evento próprio na v1 porque não há consumidor; a formação viaja em `BookProcessed` e não vira estado da oferta (OFF-30). Congelamento do livro, processamento e aplicação do resultado são internos ao BookBuilding e não geram evento entre contextos (BOOK-15, ALLOC-01, BOOK-17).

São candidatos futuros, condicionados à existência de consumidores: `OfferBecameUnconditional`, `OfferLapsed`, `OfferCompleted`, `BidPlaced`, `BidChanged` e `BidWithdrawn`.

## Flows Between Contexts

Os diagramas mostram a ordem lógica das operações; transporte e sincronização precisam atender ao NFR relacionado na decisão delegada a ADR.

```mermaid
sequenceDiagram
    participant Operador
    participant Offering
    participant BookBuilding
    Operador->>Offering: publicar (OFF-03)
    Offering-->>BookBuilding: OfferPublished (OFF-03)
    loop período de reserva (BOOK-01)
        Operador->>BookBuilding: registrar (BOOK-01 a BOOK-09)
        Operador->>BookBuilding: alterar ou cancelar (BOOK-10, BOOK-11)
    end
    Operador->>Offering: fechar (OFF-07)
    Offering-->>BookBuilding: OfferClosed (OFF-07)
    BookBuilding->>BookBuilding: congelar o livro (BOOK-15)
    BookBuilding->>BookBuilding: processar o livro fechado (ALLOC-01 a ALLOC-26)
    BookBuilding->>BookBuilding: aplicar status e quantidade (BOOK-17)
    BookBuilding-->>Offering: BookProcessed (ALLOC-26)
    alt formada (ALLOC-10)
        Offering->>Offering: registrar desfecho (OFF-32)
        Operador->>Offering: encerrar (OFF-13)
    else não formada (ALLOC-09)
        Offering->>Offering: Encerrada (OFF-31)
    end
```

A revogação é permitida em Aberta e Fechada (OFF-12); os dois contextos convergem ao mesmo estado final independentemente da ordem de entrega. No BookBuilding, a revogação interrompe o processamento em curso (ALLOC-03) e torna as reservas sem efeito, antes ou depois do resultado (BOOK-18); um desfecho já emitido não muda (ALLOC-03) e, chegando ao Offering depois da revogação, é descartado (OFF-33).

```mermaid
sequenceDiagram
    participant Operador
    participant Offering
    participant BookBuilding
    Operador->>Offering: revogar (OFF-12)
    Offering-->>BookBuilding: OfferRevoked (OFF-12)
    alt processamento em curso (ALLOC-03)
        BookBuilding->>BookBuilding: interromper sem emitir (ALLOC-03)
    else desfecho já emitido (ALLOC-03)
        BookBuilding-->>Offering: BookProcessed tardio (ALLOC-26)
        Offering->>Offering: descartar e registrar (OFF-33)
    end
    BookBuilding->>BookBuilding: reservas Sem efeito, histórico preservado (BOOK-18)
```

## Decisions Delegated to ADR

| Decisão | Exigência que a ADR precisa satisfazer |
|---|---|
| Transporte dos eventos entre contextos | OFF-NFR-03 |
