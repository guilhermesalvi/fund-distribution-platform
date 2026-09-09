# Redação do PRD

Passo 3 do workflow: o que entra, em que forma e por quê. Onde o arquivo é gravado e o header: SKILL.md, Gravar. Como revisar: review.md.

## Tags

Texto sem tag é fato: confirmado pelo usuário ou por fonte autoritativa (regulação oficial, política formalizada, decisão registrada). Duas tags marcam o que não é:

- `[PREMISSA]`: inferido pela skill; precisa de validação.
- `[LACUNA]`: informação insuficiente para preencher com substância.

Nunca preencha com especulação sem tag: lacuna é informação, exponha. Premissa que, se falsa, derruba a abordagem do PRD, e não só um requisito, é a primeira linha de Perguntas em Aberto, em negrito, com a cláusula "se falsa, …" e como validar; declarada uma vez, ali, e citada onde importa.

## Capability test

O PRD vive no problem space: diz o que precisa acontecer no negócio, não como o software é construído. Aplique à Solução Proposta, à frase de solução do Resumo Executivo e a cada FR: o texto não nomeia UI (telas, wizards, modais, dashboards), serviços e módulos, mecanismos (banco, fila, cache, event bus, webhook), padrão de UX, stack ou vendor. Se nomeou, reescreva como mudança de comportamento observável. Exceção: quando a mudança de UX ou de interface pública é a capability, essa categoria pode ser nomeada; componente, protocolo e schema continuam downstream.

| Mecanismo | Capability |
|---|---|
| Portal web com wizard de upload em 3 passos e notificação por email | Submissão assíncrona de documentos com visibilidade de status para todas as partes |
| Tópico Kafka publicando `CustomerVerified` para serviços downstream | Status de verificação observável por outros contextos sem acoplamento síncrono |
| Sistema exibe modal de confirmação antes da exclusão | Exclusão de registro ativo exige confirmação explícita do usuário |
| Sistema publica na fila de auditoria a cada mudança de estado | Toda mudança de estado é auditável, com quem mudou e quando |

## Lente DDD

Quando o time opera em DDD ou tem vocabulário de domínio explícito; fora disso, Bounded Context, Ubiquitous Language e Domain Events usam o rótulo do time (módulo, área, integração).

- **Ubiquitous Language.** Termos dos especialistas de domínio, não jargão genérico; o significado importa mais que a palavra, e o idioma não importa. Nomes concorrentes para o mesmo conceito dentro de um contexto viram `[LACUNA]`: alinhe antes de redigir. Entre especialistas de áreas diferentes, o mesmo conflito é sinal de fronteira, não de lacuna.
- **Subdomínio.** Core (diferencial competitivo): rigor máximo, critérios precisos, não-objetivos explícitos, questione se a solução preserva o diferencial. Supporting: PRD padrão. Generic: questione comprar, contratar ou reusar; pode virar não-objetivo.
- **Bounded Context como âncora de escopo.** A fronteira se revela pelo vocabulário: dois especialistas usando termos diferentes para a mesma coisa, ou o mesmo termo para coisas diferentes, são indício de contextos distintos (evidência: passada de termos da ontologia, intake.md); a fronteira se confirma quando regras e motivos de mudança também divergem. A feature tem um contexto originário, nomeado no header. Quando vários contextos são tocados, o originário é dono da decisão e os outros entram em Dependências e Riscos com o impacto na autonomia declarado. Escopo cruzando contextos sem origem clara é risco: force a discussão antes de redigir. Mais de um contexto com PRD próprio exige o PRD 0000.
- **Domain Events.** Evento é o reconhecimento de uma operação que mudou o estado e interessa a outro contexto: contrato de domínio, não detalhe de implementação; mal documentado, vira acoplamento implícito. Evento, transição da máquina de estados e FR de transição saem da mesma pergunta, feita por atributo: em que cenário muda, quem dispara, quem precisa saber (intake.md, Ontologia, passada 7). O catálogo vive no PRD 0000; cada PRD declara só o que produz e consome.

## Uma regra, um lugar

- **O FR é a única fonte da regra.** Solução Proposta, Glossário, Considerações Regulatórias, Critérios de Aceitação, Dependências, Perguntas em Aberto e o PRD 0000 citam o ID (`OFF-28`) e não parafraseiam: paráfrase diverge com o tempo. Se paráfrase e FR divergem, decida qual está certo antes de apagar a paráfrase; a divergência é a informação, não o ruído.
- **Um FR, uma unidade comportamental verificável.** Obrigações independentes, que podem falhar separadamente, vão em FRs separados, porque citação e teste apontam para uma só; condição conjunta e efeito indivisível ficam no mesmo FR, porque fragmentá-los inventa estados intermediários que o negócio não tem.
- **Atributo condicional tem FR para fora da condição.** Atributo ou opção que só se aplica sob condição ganha FR dizendo o que acontece quando informado fora dela (rejeitado ou ignorado), porque é decisão de negócio, não de implementação.
- **Seção que só reafirma FRs não entra.** Métrica que repete um FR, critério de aceitação sem valor novo e dependência descrevendo dos dois lados o mesmo acoplamento são custo sem informação.
- **Fato compartilhado vive no 0000.** Propósito do projeto, mapa de contextos, catálogo de eventos e acoplamentos entre contextos ficam no PRD 0000 e cada PRD referencia, porque repetido dos dois lados diverge.

## IDs

- Formato `<PREFIXO>-nn` para FR e `<PREFIXO>-NFR-nn` para NFR, com prefixo por contexto (`OFF-12`, `BOOK-18`, `OFF-NFR-03`), porque `FR-14` local a cada PRD significava coisas diferentes em documentos que se citam. O prefixo é declarado na linha logo após a tabela do header (SKILL.md, Gravar) e na tabela de contextos do PRD 0000.
- Definição: `- **OFF-01 (Must)** condição.` MoSCoW (Must, Should, Could, Won't) dentro dos parênteses; NFR sem MoSCoW. Toda citação resolve para uma definição em algum PRD da pasta.
- ID removido morre e não é reciclado, porque citação para ID reaproveitado muda de significado em silêncio. Antes de alterar ou remover um FR, procure quem cita o ID fora deste PRD (outros PRDs, specs, testes) e liste ao apresentar: a citação continua apontando para o ID, mas o texto atrás dele mudou.
- Estado, motivo de resultado, categoria e toda enumeração que o código vai carregar têm coluna Identificador na tabela que os define (ao lado do diagrama, junto do FR ou no Glossário), porque o código carrega esse nome e nome inventado fora do PRD é decisão de linguagem tomada fora dele.

## PRD 0000

Quando há mais de um contexto com PRD próprio, o PRD 0000 (`0000-<slug>-overview.md`, com `<!-- prd: overview -->` na primeira linha) concentra o que é compartilhado e não contém regra de negócio: toda regra vive no PRD dono e é citada pelo ID.

| Seção | Conteúdo |
|---|---|
| Propósito | O projeto em um parágrafo |
| Contextos | Tabela: contexto, responsabilidade, PRD, prefixo de ID, posição (upstream, consome, devolve) e as regras de integração (persistência, direção de mudança de contrato) |
| Catálogo de eventos | Tabela: evento, produtor, consumidores, gatilho, IDs que o governam. Um evento só entra com consumidor que o PRD consumidor declara; sem consumidor é candidato, listado como tal, porque evento sem consumidor é acoplamento inventado |
| Fluxos entre contextos | `sequenceDiagram` por fluxo (caminho feliz, revogação, falha); rótulos citam IDs |
| Termos por contexto | Só quando o mesmo conceito tem nomes diferentes entre contextos: conceito, termo em cada contexto (intake.md, Ontologia). Cada PRD mantém o glossário do seu contexto; o 0000 mantém a correspondência |
| Decisões delegadas a ADR | Tabela: decisão, exigência que a ADR precisa satisfazer (cita o NFR); o formato da ADR não é assunto do PRD |

Cada PRD referencia o 0000 na linha de prefixo do header em vez de repetir propósito, mapa ou catálogo.

## Diagramas

Mermaid substitui prosa quando a estrutura é um grafo: `stateDiagram-v2` para máquina de estados, `flowchart` para pipeline de decisão com desigualdades curtas nos nós de decisão, `sequenceDiagram` para fluxo entre contextos (no 0000). Rótulo de transição, aresta ou mensagem cita o ID do requisito e não reescreve a condição, porque o diagrama é índice, não segunda fonte. Ao lado do `stateDiagram-v2` vai a tabela estado, identificador, significado (IDs).

Palavra reservada do Mermaid não serve de alias de participante nem de nó: `off` e `end` falham no parse mesmo em maiúsculas (`participant OFF as Offering` quebra; `on` passa no parser pinado); use o nome completo. Todo bloco passa por `lint_mermaid.py` antes de apresentar (review.md, Passada mecânica).

## Seções

Obrigatórias, HARD no linter: Contexto e Problema, Usuário-alvo, Solução Proposta e, quando o PRD define IDs, Requisitos Funcionais. O PRD 0000 tem as seções da tabela PRD 0000. Toda outra seção entra quando o critério da coluna "Entra quando" se cumpre e nunca por forma: seção vazia, "Nenhuma." ou bullet inventado para completar contagem é defeito, não conformidade. A ordem é a da tabela.

| Seção | Entra quando | Forma |
|---|---|---|
| Resumo Executivo | O leitor precisa decidir sem ler o resto | 3–5 linhas: problema, solução, métrica primária |
| Alinhamento Estratégico | Precisa justificar investimento | 3–5 linhas conectando a objetivo de negócio |
| Contexto e Problema | Sempre | O problema; fatos e premissas (Tags); sem regra de negócio |
| Usuário-alvo / JTBD | Sempre | Um bullet por ator com o job |
| Oportunidade / Hipótese | Problema ainda em validação | Hipótese e como será validada |
| Solução Proposta | Sempre | Capability, não mecanismo; máquina de estados ou pipeline em Mermaid; regra citada por ID; fecha dizendo o que é downstream |
| Glossário de Domínio | Há termo cujo significado não é óbvio ou tem sinônimos concorrentes | Termo e definição de uma linha, vindos das passadas de conceitos e termos da ontologia quando há transcrição (intake.md); termo cuja definição é regra cita o ID; termo de outro contexto aponta o PRD dono |
| Requisitos Funcionais | Há requisito | Lista por subtítulo temático, cada linha um ID e uma condição (IDs; Uma regra, um lugar) |
| Domain Events | O contexto produz ou consome evento | Um parágrafo: produz X (ID), consome Y (ID); catálogo e sequências no 0000 |
| Requisitos Não Funcionais | Há atributo de qualidade ou restrição pelo qual o design será avaliado | `<PREFIXO>-NFR-nn`; atributo de qualidade e restrição, nunca mecanismo; exigência que uma ADR precisa satisfazer diz qual |
| Considerações Regulatórias | Norma identificada e lida | Fonte e data de leitura no topo; uma linha por artigo: `Art. N: o que diz → ID que o modela`; artigo não conferido no texto é `[PREMISSA]` |
| Não-objetivos | Há risco de scope creep | Um bullet por exclusão; o que não faremos |
| Trade-offs Declarados | Há decisão com custo consciente | `**Decisão.** *Custo:* … *Razão:* …`, até duas linhas, os dois obrigatórios porque evitam re-litígio. Diferente de Não-objetivos (não faremos) e de Perguntas em Aberto (não decidido) |
| Métricas de Sucesso | Há como medir o resultado | Uma linha por tipo que existe: leading (proxy, agora), lagging (resultado), guardrail (o que não pode degradar; sem ele a métrica vira alvo). Plataforma e infra em intake.md |
| Critérios de Aceitação | Há valor que o FR não expressa | Cenário numérico em tabela: caso, entrada, valores intermediários, ramo, resultado; a primeira coluna nomeia o caso porque teste cita pelo nome. Dado/Quando/Então só para o que a tabela não expressa, citando o FR que exercita; "usuário pode X" é tautologia |
| Dependências e Riscos | Há dependência ou risco fora do controle do contexto | Tabela item, tipo, impacto; acoplamento entre contextos cita o 0000 e só o lado dono o descreve |
| Perguntas em Aberto | Há pendência real | Uma linha cada: a pergunta, o impacto, o dono e o critério que a resolve, quando conhecidos. Premissa que derruba o PRD vem primeiro, em negrito, com "se falsa, …" e como validar (Tags); `[LACUNA]` que bloqueia decisão também entra. Decisão tomada não entra: com custo vive em Trade-offs, sem custo vive no FR que a aplica; decisão arquitetural delegada é candidata a ADR (PRD 0000) |
| Ponto de Maior Fragilidade | Há decisão de julgamento que um revisor cético e competente atacaria primeiro | Última seção de conteúdo, só Referências depois. A decisão; o vetor de ataque concreto; o convite ao autor para desafiá-la antes de aprovar. É distinto das tags: `[PREMISSA]` pode ser falsa (risco factual), `[LACUNA]` é informação que falta (risco de cobertura); aqui é decisão sobre fatos, sem lacuna, e ainda assim contestável (corte de escopo, threshold, priorização, usuário-alvo). Exposição, não auto-correção: quem tem contexto para resolver é o autor. Calibre ao custo do erro; fraqueza menor nomeada para parecer rigor é auto-crítica cosmética. Com `[LACUNA]` material, aponte a decisão que depende da lacuna e o que a validação mudaria, sem fabricar vetor de ataque |
| Referências | Há fonte usada | Link, artigos lidos, data de leitura, PRDs citados |

## Redação

Tom direto, preciso, orientado a decisão; sem linguagem genérica ("melhorar experiência") sem âncora em métrica ou comportamento. O texto é lido por humanos e por LLMs downstream, então:

- Voz declarativa e ativa: "o sistema bloqueia a ativação", não "seria bloqueado".
- Sem hedging ("provavelmente", "talvez", "poderia", "na verdade", "muito").
- Sem meta-narração ("este PRD descreve", "vamos discutir", "é importante notar"): o título já diz o que é.
- Sem qualificador redundante nem filler: "de modo a" vira "para"; "devido ao fato de que" vira "porque"; "com zero X necessário" vira "sem X".
- Um conceito por parágrafo; dois parágrafos adjacentes sobre o mesmo ponto se fundem. Regra dita duas vezes ou FR com mais de uma condição é o que faz o PRD crescer sem informação (Uma regra, um lugar).
- Preserve o contexto de decisão: Razão do trade-off, racional do guardrail e "se falsa" da premissa que derruba o PRD carregam sinal.
- Hierarquia: `#` título, `##` seções, `###` subseções; lista para requisitos e critérios; tabela para comparação, dependência, cenário numérico.
