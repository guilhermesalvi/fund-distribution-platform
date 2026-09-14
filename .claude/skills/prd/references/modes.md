# Modos condicionais

Leia apenas o modo correspondente ao pedido. As regras de [writing.md](writing.md) e [intake.md](intake.md) continuam aplicáveis.

## PRD de produto existente

Documente comportamento observável, regras aplicadas e decisões que o sistema toma. Código, testes, documentos e telas são fontes de comportamento; a intenção de negócio precisa de evidência própria.

Aplique o teste de capacidade a todas as seções: descreva os resultados para o negócio e cite mecanismos apenas quando forem parte do produto ou da interface pública.

- Intenção inferida recebe `[ASSUMPTION]`, com a origem.
- Comportamento sem justificativa identificável recebe `[GAP]`.
- Intenções concorrentes entram em `Open Questions`; não fabrique coerência.
- Preserve a diferença entre comportamento observado e comportamento desejado.

## Plataforma, infraestrutura, SDK ou API como produto

O usuário é o time ou sistema consumidor. Expresse o trabalho que ele precisa realizar, como integrar autenticação sem administrar estado de sessão.

Escolha métricas pertinentes ao consumo: percentis de latência, taxa de erro, adoção e tempo de integração, quando houver fonte. O resultado comercial pode pertencer ao consumidor.

Critérios de aceitação incluem estabilidade do contrato, SLA e compatibilidade quando fizerem parte do pedido. Ao substituir uma interface publicada, registre o custo de descontinuação em `Declared Trade-offs`; exclusões sem quebra entram em `Non-goals`. Cite a interface afetada e a migração prevista. Não transforme uma sugestão de cronograma em compromisso.
