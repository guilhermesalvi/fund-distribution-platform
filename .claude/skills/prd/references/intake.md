# Avaliação da entrada

## Material e escopo

Extraia do pedido e dos documentos o problema, a evidência, o usuário, a direção da solução, as métricas e as restrições. Use o que já está disponível antes de formular perguntas.

| Situação | Ação |
|---|---|
| Usuário e problema ou direção identificados | Escreva o PRD; marque os sinais ausentes |
| Contexto parcial | Escreva com `[ASSUMPTION]` e `[GAP]`; não force descoberta |
| Apenas um nome ou ideia genérica | Se perguntas forem permitidas e necessárias, priorize problema, usuário e evidência de sucesso |
| Domínio amplo ou várias iniciativas | Proponha um recorte; adote-o como `[ASSUMPTION]` se a decisão foi delegada |
| Pedido de tela, serviço ou CRUD | Identifique pelo material qual capacidade ou decisão de negócio ele atende |

Agrupe as dúvidas indispensáveis e de maior impacto. Pergunte apenas quando a resposta não puder ser obtida do contexto e mudar a entrega. Se o usuário pedir para não fazer perguntas, produza o documento com as lacunas explícitas e decisões dentro da autonomia concedida. Uma lacuna de negócio não vira fato por falta de resposta.

## Fontes de descoberta

Documentos, apresentações, reuniões, código e PRDs antigos trazem sinais com graus diferentes de autoridade. Preserve a origem:

- Política formalizada, decisão registrada ou confirmação do usuário sustenta um fato.
- Uma intenção deduzida do material recebe `[ASSUMPTION]`, com documento e página ou seção.
- Fontes que divergem geram `[GAP]` com o ponto a reconciliar.
- Reorganize o conteúdo conforme o problema. Revise trechos suspeitos de cópia no contexto da fonte; uma contagem de frases não demonstra síntese.

Classifique um PRD antigo pelo pedido: base de um incremento, documento a atualizar ou referência de inspiração. Se a distinção for material e continuar desconhecida, registre a lacuna ou esclareça conforme a autorização de perguntas. Em atualização, preserve o arquivo e os IDs.

Para comportamento existente ou produto consumido por outro time, consulte [modes.md](modes.md).

## Pesquisa

Verifique fontes externas quando o documento depender de normas vigentes, benchmarks, concorrentes ou fatos não sustentados pelo material. Prefira fontes primárias; cite link, trecho ou seção pertinente e data da consulta. Diferencie o fato consultado da interpretação aplicada ao produto.

Sem acesso à fonte, marque `[GAP]`, informe qual verificação ficou pendente e continue o que for independente. A ausência de pesquisa não autoriza preencher o dado de memória.

Em domínio regulado, leia a norma vigente antes de tratá-la como restrição. `Regulatory Considerations` segue [writing.md](writing.md); artigo ainda não conferido permanece hipótese, sem adquirir força normativa.
