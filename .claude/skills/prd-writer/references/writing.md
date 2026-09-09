# Redação do PRD

Passos 3 e 4 do workflow. Regras de conteúdo: o que entra, em que forma e por quê. Onde o arquivo é gravado e o header: SKILL.md, Gravar. Como revisar: review.md.

## Tags

Texto sem tag é fato: confirmado pelo usuário ou por fonte autoritativa (regulação oficial, política formalizada, decisão registrada). Duas tags marcam o que não é:

- `[PREMISSA]`: inferido pela skill; precisa de validação.
- `[LACUNA]`: informação insuficiente para preencher com substância.

Nunca preencha com especulação sem tag: lacuna é informação, exponha. Premissa que, se falsa, derruba a abordagem do PRD, e não só um requisito, é a primeira linha de Perguntas em Aberto, em negrito, com a cláusula "se falsa, …" e como validar; declarada uma vez, ali, e citada onde importa.

## Tier

Profundidade proporcional à complexidade; o tier fixa o piso de seções (tabela Seções) e vai no comentário de máquina (SKILL.md, Gravar).

| Tier | Critério |
|---|---|
| `simples` | Um ator, domínio direto, sem regulação relevante |
| `media` | Múltiplos atores, regras não triviais, dependências relevantes |
| `complexa` | Regulatória, multi-ator, alto risco, impacto sistêmico |
| `overview` | O PRD 0000 (seção PRD 0000); não tem tier de profundidade |

Na dúvida entre dois tiers, declare o maior: subdimensionar produz PRD cego (a seção que faltou nunca entra em discussão); superdimensionar custa seções omitíveis.

Tamanho: tier complexa fica em até 3500–4000 palavras. Linhas não são a métrica; acima disso, alguma regra está sendo dita duas vezes ou algum FR carrega mais de uma condição (Uma regra, um lugar).

## Lente DDD

Aplicável quando o time opera em DDD ou tem vocabulário de domínio explícito. Fora disso, capability vs feature e problem space vs solution space continuam universais; Bounded Context, Ubiquitous Language e Domain Events usam o rótulo do time (módulo, área, integração).

**Problem space vs solution space.** O PRD diz o que precisa acontecer no negócio, não como o software é construído. Quando aparece descrição de tecnologia, arquitetura ou implementação, reescreva um nível acima.

**Capability test.** Aplique à Solução Proposta, à frase de solução do Resumo Executivo e a cada FR. O texto não nomeia UI (telas, wizards, modais, dashboards), serviços e módulos, mecanismos técnicos (banco, fila, cache, event bus, webhook), padrão específico de UX, stack ou vendor. Se algum foi nomeado, reescreva como mudança de comportamento observável, não mecanismo. Exceção: quando o ponto do PRD é a mudança de UX ou de interface pública, essa categoria é a capability e pode ser nomeada; componente, protocolo e schema continuam downstream.

| Mecanismo | Capability |
|---|---|
| Portal web com wizard de upload em 3 passos e notificação por email | Submissão assíncrona de documentos com visibilidade de status para todas as partes |
| Tópico Kafka publicando `CustomerVerified` para serviços downstream | Status de verificação observável por outros contextos sem acoplamento síncrono |
| Sistema exibe modal de confirmação antes da exclusão | Exclusão de registro ativo exige confirmação explícita do usuário |
| Sistema publica na fila de auditoria a cada mudança de estado | Toda mudança de estado é auditável, com quem mudou e quando |

**Ubiquitous Language.** Termos dos especialistas de domínio, não jargão genérico; o significado importa mais que a palavra, e o idioma não importa. Nomes concorrentes para o mesmo conceito dentro de um contexto viram `[LACUNA]`: alinhe antes de redigir. Entre especialistas de áreas diferentes, o mesmo conflito é sinal de fronteira, não de lacuna (Bounded Context).

**Subdomínio.** Core (diferencial competitivo): rigor máximo, critérios precisos, não-objetivos explícitos, questione se a solução preserva o diferencial. Supporting: PRD padrão. Generic: questione comprar, contratar ou reusar; pode virar não-objetivo.

**Bounded Context como âncora de escopo.** A fronteira se revela pelo vocabulário: dois especialistas usando termos diferentes para a mesma coisa, ou o mesmo termo para coisas diferentes (paciente, cliente e vida para a mesma pessoa), são indício de contextos distintos, não prova. A evidência vem da passada de termos da ontologia (intake.md), e a fronteira se confirma quando as regras e os motivos de mudança também divergem. A feature tem um contexto originário, nomeado no header. Quando vários contextos são tocados, o originário é dono da decisão e os outros entram em Dependências e Riscos com o impacto na autonomia declarado. Escopo cruzando contextos sem origem clara é risco: force a discussão antes de redigir. Mais de um contexto com PRD próprio exige o PRD 0000.

**Domain Events.** Evento é o reconhecimento de uma operação que mudou o estado e interessa a outro contexto. É contrato de domínio, não detalhe de implementação; mal documentado, vira acoplamento implícito. Evento, transição da máquina de estados e FR de transição saem da mesma pergunta, feita por atributo: em que cenário muda, quem dispara, quem precisa saber (intake.md, Ontologia, passada 7). O catálogo vive no PRD 0000; cada PRD declara só o que produz e consome (tabela Seções).

## Uma regra, um lugar

- **O FR é a única fonte da regra.** Solução Proposta, Glossário, Considerações Regulatórias, Critérios de Aceitação, Dependências, Perguntas em Aberto e o PRD 0000 citam o ID (`OFF-28`) e não parafraseiam. Paráfrase diverge com o tempo: um glossário chamou de denominador o que a fórmula do FR usa como numerador.
- **Um FR, uma unidade comportamental verificável.** Obrigações independentes, que podem falhar separadamente, vão em FRs separados, porque citação e teste precisam apontar para uma só; condição conjunta e efeito indivisível ficam no mesmo FR, porque fragmentá-los inventa estados intermediários que o negócio não tem. Resumo, glossário e cenário podem repetir informação derivada citando o ID; o que não pode existir é uma segunda regra concorrente.
- **Seção que só reafirma FRs não entra.** Métrica que repete um FR, critério de aceitação sem valor novo e dependência descrevendo dos dois lados o mesmo acoplamento são custo sem informação; a forma mínima de cada seção está na tabela Seções.
- **Fato compartilhado vive no 0000.** Propósito do projeto, mapa de contextos, catálogo de eventos e acoplamentos entre contextos ficam no PRD 0000 e cada PRD referencia, porque repetido dos dois lados diverge.

## IDs

- Formato `<PREFIXO>-nn` para FR e `<PREFIXO>-NFR-nn` para NFR, com prefixo por contexto (`OFF-12`, `BOOK-18`, `ALLOC-17`, `OFF-NFR-03`), porque `FR-14` local a cada PRD significava coisas diferentes em documentos que se citam.
- O prefixo é declarado na linha logo após a tabela do header (SKILL.md, Gravar) e na tabela de contextos do PRD 0000.
- Definição: `- **OFF-01 (Must)** condição.` MoSCoW (Must, Should, Could, Won't) dentro dos parênteses. NFR sem MoSCoW.
- Toda citação resolve para uma definição em algum PRD da pasta; ID removido morre e não é reciclado, porque citação para ID reaproveitado muda de significado em silêncio.
- Rótulo de transição ou de ramo em diagrama cita o ID, não reescreve a condição (Diagramas).
- Antes de alterar ou remover um FR, procure quem cita o ID fora deste PRD (outros PRDs, specs, testes) e liste ao apresentar: a citação continua apontando para o ID, mas o texto atrás dele mudou.

## PRD 0000

Quando há mais de um contexto com PRD próprio, o PRD `0000` (tier `overview`) concentra o que é compartilhado e não contém regra de negócio: toda regra vive no PRD dono e é citada pelo ID.

| Seção | Conteúdo |
|---|---|
| Propósito | O projeto em um parágrafo |
| Contextos | Tabela: contexto, responsabilidade, PRD, prefixo de ID, posição (upstream, consome, devolve) e as regras de integração (persistência, direção de mudança de contrato) |
| Catálogo de eventos | Tabela: evento, produtor, consumidores, gatilho, IDs que o governam. Um evento só entra com consumidor que o PRD consumidor declara; sem consumidor é candidato, listado como tal, porque evento sem consumidor é acoplamento inventado |
| Fluxos entre contextos | `sequenceDiagram` por fluxo (caminho feliz, revogação, falha); rótulos citam IDs |
| Termos por contexto | Tabela: conceito, termo em cada contexto; só quando o mesmo conceito tem nomes diferentes entre contextos (intake.md, Ontologia). Cada PRD mantém o glossário do seu contexto; o 0000 mantém a correspondência |
| Decisões delegadas a ADR | Tabela: decisão, exigência que a ADR precisa satisfazer (cita o NFR); o formato da ADR não é assunto do PRD |

Cada PRD referencia o 0000 na linha de prefixo do header em vez de repetir propósito, mapa ou catálogo.

## Diagramas

Mermaid substitui prosa quando a estrutura é um grafo: `stateDiagram-v2` para máquina de estados, `flowchart` para pipeline de decisão com desigualdades curtas nos nós de decisão, `sequenceDiagram` para fluxo entre contextos (no 0000). Rótulo de transição, aresta ou mensagem cita o ID do requisito e não reescreve a condição, porque o diagrama é índice, não segunda fonte. Ao lado do `stateDiagram-v2` vai uma tabela com estado, identificador e significado. A mesma coluna Identificador vale para toda enumeração que o código vai carregar (motivo de resultado, categoria, tipo de declaração). Essa tabela fica junto do FR que a define ou no Glossário, porque o código carrega esse nome, e nome inventado fora do PRD é decisão de linguagem tomada fora dele.

Palavra reservada do Mermaid não serve de alias de participante nem de nó: `off` e `end` falham no parse mesmo em maiúsculas (`participant OFF as Offering` quebra; `on` passa no parser pinado); use o nome completo. Todo bloco passa por parse antes de apresentar (review.md, Passada mecânica).

## Seções

Quatro seções são bloqueantes em qualquer tier de profundidade (HARD no linter): Contexto e Problema, Usuário-alvo, Solução Proposta e Ponto de Maior Fragilidade. O PRD 0000 (`overview`) tem as seções da tabela PRD 0000 e não tem Ponto de Maior Fragilidade. As demais são esperadas a partir do tier indicado (WARN se ausentes) ou condicionais; omissão deliberada é legítima. Uma condicional é HARD em qualquer tier: Functional Requirements, quando o PRD define IDs de requisito ou tem Non-functional Requirements.

| Seção | Entra quando | Forma |
|---|---|---|
| Resumo Executivo | `media`+ | 3–5 linhas: problema, solução, métrica primária |
| Alinhamento Estratégico | `complexa`, ou quando precisa justificar investimento | 3–5 linhas conectando a objetivo de negócio |
| Contexto e Problema | Sempre | O problema; fatos e premissas (Tags); sem regra de negócio |
| Usuário-alvo / JTBD | Sempre | Um bullet por ator com o job; plataforma e infra em intake.md |
| Oportunidade / Hipótese | Problema ainda em validação | Hipótese e como será validada |
| Solução Proposta | Sempre | Capability, não mecanismo; máquina de estados ou pipeline em Mermaid; regra citada por ID; fecha dizendo o que é downstream |
| Glossário de Domínio | ≥5 termos ou sinônimos concorrentes | Termo e definição de uma linha, vindos das passadas de conceitos e termos da ontologia quando há transcrição (intake.md); termo cuja definição é regra cita o ID; termo de outro contexto aponta o PRD dono |
| Functional Requirements | `media`+ | Lista por subtítulo temático, cada linha um ID e uma condição (IDs). Atributo ou opção que só se aplica sob condição ganha FR dizendo o que acontece quando informado fora dela (rejeitado ou ignorado), porque é decisão de negócio, não de implementação |
| Domain Events | O contexto produz ou consome evento | Um parágrafo: produz X (ID), consome Y (ID); catálogo e sequências no 0000 |
| Non-functional Requirements | `complexa` | `<PREFIXO>-NFR-nn`; são os critérios pelos quais o design será avaliado, então atributo de qualidade e restrição, nunca mecanismo; exigência que um ADR precisa satisfazer diz qual ADR |
| Considerações Regulatórias | `complexa`, ou qualquer tier com dependência de norma ou órgão regulador | Fonte e data de leitura no topo; uma linha por artigo: `Art. N: o que diz → ID que o modela`; artigo não conferido no texto é `[PREMISSA]` |
| Não-objetivos | `simples`+; omita só sem risco de scope creep | Um bullet por exclusão; o que não faremos |
| Trade-offs Declarados | Decisão com custo consciente | `**Decisão.** *Custo:* … *Razão:* …`, até duas linhas; Custo e Razão obrigatórios; todos mantidos, porque evitam re-litígio. Diferente de Não-objetivos (não faremos) e de Perguntas em Aberto (não decidido) |
| Métricas de Sucesso | `simples`+ | Exatamente três bullets: leading (proxy, agora), lagging (resultado), guardrails (o que não pode degradar; sem eles, Lei de Goodhart). Plataforma e infra em intake.md |
| Critérios de Aceitação | `media`+ | Cenário numérico em tabela: caso, entrada, valores intermediários, ramo, resultado; a primeira coluna nomeia o caso porque teste cita pelo nome. Dado/Quando/Então só para o que a tabela não expressa, citando o FR que exercita. Só o que acrescenta valores ao FR; "usuário pode X" é tautologia |
| Dependências e Riscos | `media`+ | Tabela item, tipo, impacto; acoplamento entre contextos cita o 0000 e só o lado dono o descreve |
| Perguntas em Aberto | `simples`+ | Pendências reais, uma linha cada: a pergunta, o impacto, o dono e o critério que a resolve, quando conhecidos. Premissa que derruba o PRD vem primeiro, em negrito, com "se falsa, …" e como validar (Tags); `[LACUNA]` que bloqueia decisão também entra. "Nenhuma." só quando não há pendência. Decisão tomada não entra: com custo vive em Trade-offs, sem custo vive no FR que a aplica; decisão arquitetural delegada é candidata a ADR (PRD 0000, Decisões delegadas a ADR) |
| Ponto de Maior Fragilidade | Sempre, última seção de conteúdo; só Referências vem depois | Abaixo |
| Referências | Fonte usada | Link, artigos lidos, data de leitura, PRDs citados |

## Ponto de Maior Fragilidade

Todo PRD termina nomeando uma decisão: a decisão de julgamento mais contestável, a que um revisor cético e competente atacaria primeiro.

É distinto das tags. `[PREMISSA]` é crença que pode ser falsa (risco factual). `[LACUNA]` é informação que falta (risco de cobertura). O ponto de maior fragilidade é decisão especificada, baseada em fatos, sem lacuna, e ainda assim possivelmente errada (risco de julgamento): corte de escopo, threshold, priorização de trade-off, escolha de usuário-alvo.

- Exatamente uma, última seção de conteúdo, depois de Perguntas em Aberto; só Referências vem depois.
- Forma: a decisão; o vetor de ataque concreto de um cético; o convite ao autor para desafiá-la antes de aprovar.
- É exposição, não auto-correção: quem tem contexto de domínio para resolver é o autor. A skill nomeia e entrega.
- Sempre presente, nos três tiers: mesmo em PRD sólido existe uma decisão mais contestável; se bem defendida, diga por que ainda merece vigilância. Ausência sinaliza análise rasa, não PRD perfeito.
- Calibre ao custo do erro: decisão de baixo custo (típico em `simples`) merece duas linhas. Retórica adversarial desproporcional é auto-crítica cosmética melhor escrita.
- Sem auto-crítica cosmética: fraqueza menor e segura nomeada para parecer rigor é falha. A pergunta é "se este PRD falhar, qual decisão terá sido a causa?".
- Em rascunho com `[LACUNA]` material, não fabrique vetor de ataque sustentado por fatos que não existem: aponte a decisão cuja sustentação depende da lacuna ou da `[PREMISSA]` pendente e diga o que a validação mudaria.

## Redação

Tom direto, preciso, orientado a decisão; sem linguagem genérica ("melhorar experiência") sem âncora em métrica ou comportamento. O texto é lido por humanos e por LLMs downstream, então:

- Voz declarativa e ativa: "o sistema bloqueia a ativação", não "seria bloqueado".
- Sem hedging ("provavelmente", "talvez", "poderia", "na verdade", "muito").
- Sem meta-narração ("este PRD descreve", "vamos discutir", "é importante notar"): o título já diz o que é.
- Sem qualificador redundante nem filler: "de modo a" vira "para"; "devido ao fato de que" vira "porque"; "com zero X necessário" vira "sem X".
- Um conceito por parágrafo; dois parágrafos adjacentes sobre o mesmo ponto se fundem.
- Preserve o contexto de decisão: Razão do trade-off, racional do guardrail e "se falsa" da premissa que derruba o PRD carregam sinal.
- Hierarquia: `#` título, `##` seções, `###` subseções; lista para requisitos e critérios; tabela para comparação, dependência, cenário numérico.
