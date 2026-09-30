# ADR 0001: BookBuilding como nome do contexto

## Participants

Autor do projeto. Nenhum outro participante está registrado.

## Context

O contexto que recebe reservas, fecha o livro e aloca as cotas precisa de um nome em inglês para o serviço, o código e a documentação. O nome vale para as capabilities [Livro de Reservas](../specs/bid-book/spec.md) e [Processamento do Livro](../specs/book-processing/spec.md) e já está adotado no serviço `src/BookBuilding`.

O critério é usar o termo que o mercado anglófono aplica ao processo modelado: abrir o livro, receber pedidos, fechar e alocar com scale-back. No modelo, o preço por cota é único e imutável depois da publicação (OFF-07, OFF-18), e não há coleta de intenções sem período de reserva.

## Decision

`BookBuilding` nomeia o contexto, o serviço `src/BookBuilding` e os namespaces dele, e é o nome usado nas specs das duas capabilities.

## Alternatives Considered

- `ReservationBook`: espelha o termo em português, sem uso equivalente nas fontes em inglês consultadas.
- `Booking`: em inglês significa registrar uma transação, não conduzir um livro de pedidos.

## Consequences

O nome coincide com o vocabulário dos comunicados de placement, inclusive em ofertas com preço fixado antes do livro, como as da Argo Blockchain e da Renalytix, em que o livro define só a quantidade. O custo aceito é que, no mercado, o termo cobre também a descoberta de preço, como na oferta da Lloyds TSB Group, que o modelo não tem.

## References

- Comunicados de placement lidos em 2026-09-13 e relidos em 2026-09-30, sem valor normativo. [Argo Blockchain](https://www.sec.gov/Archives/edgar/data/1841675/000165495423009326/a4294g.htm) e [Renalytix](https://www.sec.gov/Archives/edgar/data/1811115/000119312524230319/d896405dex992.htm) fixam o preço no anúncio, em 10 e 9 pence por ação, e deixam ao livro a quantidade. Na [Lloyds TSB Group](https://www.sec.gov/Archives/edgar/data/1160106/000119163808001657/lloy200809196k2.htm) o livro define o preço: "the Bookbuild will establish a single price". Os três usam "to bid in the Bookbuild" e "bids may be scaled down".
