# Redação do PRD

Passos 3 e 4 do workflow. Regras de conteúdo: o que entra, em que forma e por quê. Onde o arquivo é gravado e o header: output.md. Como revisar: review.md.

## Convenção de confiança

Prefixo quando a fonte importa:

- `[FATO]`: confirmado pelo usuário ou por fonte autoritativa (regulação oficial, política formalizada, decisão registrada).
- `[PREMISSA]`: inferido pela skill; precisa de validação.
- `[PREMISSA-CRÍTICA]`: load-bearing; se falsa, invalida a abordagem inteira do PRD, não só um requisito. Máximo 1–3 por documento, porque se tudo é crítico nada é. Declarada uma vez, na seção a que pertence, com a cláusula "se falsa, …" e o plano de validação na mesma linha. Perguntas em Aberto a lista como blocker por referência (Seções), sem repetir o texto: o leitor a encontra ao fim sem que ela exista em dois lugares.
- `[LACUNA]`: informação insuficiente para preencher com substância.

Nunca preencha com especulação sem tag: lacuna é informação, exponha.

O campo Confiança do header tem três valores. **Alta**: não há `[LACUNA]` material nem `[PREMISSA-CRÍTICA]` pendente; o campo é omitido, porque declarar Alta é ruído. **Média**: há lacunas ou premissas que não bloqueiam, e toda `[PREMISSA-CRÍTICA]` tem plano de validação. **Baixa**: há `[PREMISSA-CRÍTICA]` sem plano, ou múltiplas `[LACUNA]` bloqueando escopo, métrica ou viabilidade.

Confiança e Status andam juntos: Rascunho admite `[LACUNA]` material e Confiança Baixa; Em Revisão e Aprovado exigem Média ou Alta (output.md, Header). Não converta `[LACUNA]` em `[PREMISSA]` para subir a Confiança: rascunho que diz o que falta é entregável; rascunho que esconde não é.

## Tier

Profundidade proporcional à complexidade; o tier fixa o piso de seções (tabela Seções) e vai no comentário de máquina (output.md, Header).

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
- O prefixo é declarado na linha logo após a tabela do header (output.md, Header) e na tabela de contextos do PRD 0000.
- Definição: `- **OFF-01 (Must)** condição.` MoSCoW (Must, Should, Could, Won't) dentro dos parênteses. NFR sem MoSCoW.
- Toda citação resolve para uma definição em algum PRD da pasta; ID removido morre e não é reciclado, porque citação para ID reaproveitado muda de significado em silêncio.
- Rótulo de transição ou de ramo em diagrama cita o ID, não reescreve a condição (Diagramas).
- PRD com spec derivada (`/docs/specs`, skill `spec-driven`): cada requisito EARS da spec cita o ID deste PRD ao fim da linha. Antes de alterar ou remover um FR, procure o ID em `/docs/specs` e liste as specs afetadas ao apresentar; o linter da spec confere que o ID existe, não que o texto continua o mesmo.

## PRD 0000

Quando há mais de um contexto com PRD próprio, o PRD `0000` (tier `overview`) concentra o que é compartilhado e não contém regra de negócio: toda regra vive no PRD dono e é citada pelo ID.

| Seção | Conteúdo |
|---|---|
| Propósito | O projeto em um parágrafo, com tags de confiança |
| Contextos | Tabela: contexto, responsabilidade, PRD, prefixo de ID, posição (upstream, consome, devolve) e as regras de integração (persistência, direção de mudança de contrato) |
| Catálogo de eventos | Tabela: evento, produtor, consumidores, gatilho, IDs que o governam. Um evento só entra com consumidor que o PRD consumidor declara; sem consumidor é candidato, listado como tal, porque evento sem consumidor é acoplamento inventado |
| Fluxos entre contextos | `sequenceDiagram` por fluxo (caminho feliz, revogação, falha); rótulos citam IDs |
| Termos por contexto | Tabela: conceito, termo em cada contexto; só quando o mesmo conceito tem nomes diferentes entre contextos (intake.md, Ontologia). Cada PRD mantém o glossário do seu contexto; o 0000 mantém a correspondência |
| Decisões delegadas a ADR | Tabela: decisão, exigência que o ADR precisa satisfazer (cita o NFR). A ADR resultante segue o formato da skill `spec-driven` (memory.md, Decisões e ADRs): alternativas, consequências, participantes |

Cada PRD referencia o 0000 na linha de prefixo do header em vez de repetir propósito, mapa ou catálogo.

## Diagramas

Mermaid substitui prosa quando a estrutura é um grafo: `stateDiagram-v2` para máquina de estados, `flowchart` para pipeline de decisão com desigualdades curtas nos nós de decisão, `sequenceDiagram` para fluxo entre contextos (no 0000). Rótulo de transição, aresta ou mensagem cita o ID do requisito e não reescreve a condição, porque o diagrama é índice, não segunda fonte. Ao lado do `stateDiagram-v2` vai uma tabela com estado, identificador e significado. A mesma coluna Identificador vale para toda enumeração que o código vai carregar (motivo de resultado, categoria, tipo de declaração). Essa tabela fica junto do FR que a define ou no Glossário, porque a spec usa esse identificador nos requisitos EARS (skill `spec-driven`, specify.md, Origem e modo), e nome inventado na spec é decisão de linguagem tomada fora do PRD.

Palavra reservada do Mermaid não serve de alias de participante nem de nó: `off`, `end`, `on` e derivadas falham no parse mesmo em maiúsculas (`participant OFF as Offering` quebra); use o nome completo. Todo bloco passa por parse antes de apresentar (review.md, Passada mecânica).

## Seções

Quatro seções são bloqueantes em qualquer tier de profundidade (HARD no linter): Contexto e Problema, Usuário-alvo, Solução Proposta e Ponto de Maior Fragilidade. O PRD 0000 (`overview`) tem as seções da tabela PRD 0000 e não tem Ponto de Maior Fragilidade. As demais são esperadas a partir do tier indicado (WARN se ausentes) ou condicionais; omissão deliberada é legítima.

| Seção | Entra quando | Forma |
|---|---|---|
| Resumo Executivo | `media`+ | 3–5 linhas: problema, solução, métrica primária |
| Alinhamento Estratégico | `complexa`, ou quando precisa justificar investimento | 3–5 linhas conectando a objetivo de negócio |
| Contexto e Problema | Sempre | O problema; fatos e premissas com tag; sem regra de negócio |
| Usuário-alvo / JTBD | Sempre | Um bullet por ator com o job; plataforma e infra em intake.md |
| Oportunidade / Hipótese | Problema ainda em validação | Hipótese e como será validada |
| Solução Proposta | Sempre | Capability, não mecanismo; máquina de estados ou pipeline em Mermaid; regra citada por ID; fecha dizendo o que é downstream |
| Glossário de Domínio | ≥5 termos ou sinônimos concorrentes | Termo e definição de uma linha, vindos das passadas de conceitos e termos da ontologia quando há transcrição (intake.md); termo cuja definição é regra cita o ID; termo de outro contexto aponta o PRD dono |
| Functional Requirements | `media`+ | Lista por subtítulo temático, cada linha um ID e uma condição (IDs). Atributo ou opção que só se aplica sob condição ganha FR dizendo o que acontece quando informado fora dela (rejeitado ou ignorado), porque a spec não decide problem space (skill `spec-driven`, specify.md, Origem e modo) |
| Domain Events | O contexto produz ou consome evento | Um parágrafo: produz X (ID), consome Y (ID); catálogo e sequências no 0000 |
| Non-functional Requirements | `complexa` | `<PREFIXO>-NFR-nn`; são os critérios pelos quais o design será avaliado, então atributo de qualidade e restrição, nunca mecanismo (skill `spec-driven`, design.md, Critérios antes das abordagens); exigência que um ADR precisa satisfazer diz qual ADR |
| Considerações Regulatórias | `complexa`, ou qualquer tier com dependência de norma ou órgão regulador | Uma linha por artigo: `[FATO] Art. N: o que diz → ID que o modela`; fonte e data de leitura no topo |
| Não-objetivos | `simples`+; omita só sem risco de scope creep | Um bullet por exclusão; o que não faremos |
| Trade-offs Declarados | Decisão com custo consciente | `**Decisão.** *Custo:* … *Razão:* …`, até duas linhas; Custo e Razão obrigatórios; todos mantidos, porque evitam re-litígio. Diferente de Não-objetivos (não faremos) e de Perguntas em Aberto (não decidido) |
| Métricas de Sucesso | `simples`+ | Exatamente três bullets: leading (proxy, agora), lagging (resultado), guardrails (o que não pode degradar; sem eles, Lei de Goodhart). Plataforma e infra em intake.md |
| Critérios de Aceitação | `media`+ | Cenário numérico em tabela: caso, entrada, valores intermediários, ramo, resultado; a primeira coluna nomeia o caso porque a spec e o teste o citam pelo nome (skill `spec-driven`, specify.md, Origem e modo). Dado/Quando/Então só para o que a tabela não expressa, citando o FR que exercita. Só o que acrescenta valores ao FR; "usuário pode X" é tautologia |
| Dependências e Riscos | `media`+ | Tabela item, tipo, impacto; acoplamento entre contextos cita o 0000 e só o lado dono o descreve |
| Perguntas em Aberto | `simples`+ | Pendências reais, uma linha cada: a pergunta, o impacto, o dono e o critério que a resolve, quando conhecidos. `[PREMISSA-CRÍTICA]` do corpo entra aqui por referência como blocker, com o plano de validação (Convenção de confiança); `[LACUNA]` que bloqueia decisão também. "Nenhuma." só quando não há pendência. Decisão tomada não entra: com custo vive em Trade-offs, sem custo vive no FR que a aplica; decisão arquitetural delegada é candidata a ADR (PRD 0000, Decisões delegadas a ADR) |
| Ponto de Maior Fragilidade | Sempre, última seção de conteúdo; só Referências vem depois | Abaixo |
| Referências | Fonte usada | Link, artigos lidos, data de leitura, PRDs citados |

## Ponto de Maior Fragilidade

Todo PRD termina nomeando uma decisão: a decisão de julgamento mais contestável, a que um revisor cético e competente atacaria primeiro.

É distinta das tags de confiança. `[PREMISSA-CRÍTICA]` é crença que pode ser falsa (risco factual) e é a única coisa chamada load-bearing. `[LACUNA]` é informação que falta (risco de cobertura). O ponto de maior fragilidade é decisão especificada, baseada em `[FATO]`, sem lacuna, e ainda assim possivelmente errada (risco de julgamento): corte de escopo, threshold, priorização de trade-off, escolha de usuário-alvo.

- Exatamente uma, última seção de conteúdo, depois de Perguntas em Aberto; só Referências vem depois.
- Forma: a decisão; o vetor de ataque concreto de um cético; o convite ao autor para desafiá-la antes de aprovar.
- É exposição, não auto-correção: quem tem contexto de domínio para resolver é o autor. A skill nomeia e entrega.
- Sempre presente, nos três tiers: mesmo em PRD sólido existe uma decisão mais contestável; se bem defendida, diga por que ainda merece vigilância. Ausência sinaliza análise rasa, não PRD perfeito.
- Calibre ao custo do erro: decisão de baixo custo (típico em `simples`) merece duas linhas. Retórica adversarial desproporcional é auto-crítica cosmética melhor escrita.
- Sem auto-crítica cosmética: fraqueza menor e segura nomeada para parecer rigor é falha. A pergunta é "se este PRD falhar, qual decisão terá sido a causa?".
- Em rascunho com `[LACUNA]` material, não fabrique vetor de ataque sustentado por fatos que não existem: aponte a decisão cuja sustentação depende da lacuna ou da `[PREMISSA]` pendente e diga o que a validação mudaria.

## Interface com a skill spec-driven

O PRD é a entrada da Specify (skill `spec-driven`, specify.md, Origem e modo, "A partir do PRD, seis regras"). Esta tabela é o lado do PRD do mesmo contrato; cada linha diz o que a spec consome e onde a regra deste lado vive.

| A spec consome | O PRD fornece | Regra deste lado |
|---|---|---|
| Status Aprovado como pré-requisito; Rascunho ou Em Revisão só com decisão explícita do usuário | Status na enumeração, coerente com Confiança e Perguntas em Aberto | output.md, Header |
| Revisão exata (`prd-rev`: hash Git ou sha256 do conteúdo) | Arquivo estável; alteração material volta o Status a Em Revisão e invalida specs que citam os IDs tocados | IDs; output.md, Header |
| IDs `X-nn` e `X-NFR-nn` citados ao fim de cada requisito EARS, com prefixo declarado | Prefixo na linha após o header; ID nunca reciclado | IDs |
| Identificadores de estado, evento e enumeração (motivo, categoria, declaração) | Coluna Identificador nas tabelas de estado e de enumeração; nome do evento no catálogo do 0000 | Diagramas; PRD 0000 |
| Comportamento de atributo condicional fora da condição | FR diz se é rejeitado ou ignorado | Seções, Functional Requirements |
| Cenários herdados, citados pelo nome do caso ou pelo FR | Primeira coluna da tabela de Critérios de Aceitação nomeia o caso; Dado/Quando/Então cita o FR | Seções, Critérios de Aceitação |
| NFR observável vira EARS; NFR de qualidade vira critério de design | NFR é atributo de qualidade ou restrição, nunca mecanismo | Seções, Non-functional Requirements |
| Mapa de contextos, catálogo de eventos e decisões delegadas a ADR | PRD 0000 | PRD 0000 |
| `[FATO]` vira fato; `[PREMISSA]` continua premissa mesmo após aprovação | Tags de confiança em toda afirmação relevante | Convenção de confiança |
| Lacuna de regra de negócio devolvida ao PRD, nunca decidida na spec | Perguntas em Aberto com dono e critério; correção no PRD antes da spec | Seções, Perguntas em Aberto; SKILL.md, Apresente e itere |

## Redação

Tom direto, preciso, orientado a decisão; sem linguagem genérica ("melhorar experiência") sem âncora em métrica ou comportamento. O texto é lido por humanos e por LLMs downstream, então:

- Voz declarativa e ativa: "o sistema bloqueia a ativação", não "seria bloqueado".
- Sem hedging ("provavelmente", "talvez", "poderia", "na verdade", "muito").
- Sem meta-narração ("este PRD descreve", "vamos discutir", "é importante notar"): o título já diz o que é.
- Sem qualificador redundante nem filler: "de modo a" vira "para"; "devido ao fato de que" vira "porque"; "com zero X necessário" vira "sem X".
- Um conceito por parágrafo; dois parágrafos adjacentes sobre o mesmo ponto se fundem.
- Preserve o contexto de decisão: Razão do trade-off, racional do guardrail e "se falsa" da `[PREMISSA-CRÍTICA]` carregam sinal.
- Hierarquia: `#` título, `##` seções, `###` subseções; lista para requisitos e critérios; tabela para comparação, dependência, cenário numérico.
