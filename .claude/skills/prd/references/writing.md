# Redação do PRD

Regras do passo Escrever do workflow (SKILL.md, Workflow): o que entra no PRD, em que forma e por quê. Onde o arquivo é gravado e como é o header estão em SKILL.md, Gravar. O que muda no modo reverse PRD e no modo plataforma, infra, SDK ou API como produto está em modes.md.

## Tags

Texto sem tag é fato: foi confirmado pelo usuário ou vem de fonte autoritativa (regulação oficial, política formalizada, decisão registrada). Duas tags marcam o que não é fato:

- `[PREMISSA]`: inferência feita pela skill; precisa de validação.
- `[LACUNA]`: informação insuficiente para preencher o trecho com substância.

Regras de uso:

- Nunca preencha uma lacuna com especulação sem tag. A lacuna é informação: exponha-a.
- Premissa que, se falsa, derruba a abordagem do PRD, e não só um requisito, é a primeira linha de Perguntas em Aberto, em negrito, com a cláusula "se falsa, …" ("if false, …" em PRD em inglês) e como validar. Ela é declarada uma vez, ali, e citada onde importa.

## Capability test

O PRD vive no problem space: diz o que precisa acontecer no negócio, não como o software é construído.

Aplique o teste à Solução Proposta, à frase de solução do Resumo Executivo e a cada FR. O texto passa quando não nomeia:

- UI: telas, wizards, modais, dashboards;
- serviços e módulos;
- mecanismos: banco, fila, cache, event bus, webhook;
- padrão de UX, stack ou vendor.

Se nomeou, reescreva como mudança de comportamento observável.

Exceção: quando a mudança de UX ou de interface pública é a própria capability, essa categoria pode ser nomeada. Componente, protocolo e schema continuam downstream.

| Mecanismo | Capability |
|---|---|
| Portal web com wizard de upload em 3 passos e notificação por email | Submissão assíncrona de documentos com visibilidade de status para todas as partes |
| Tópico Kafka publicando `CustomerVerified` para serviços downstream | Status de verificação observável por outros contextos sem acoplamento síncrono |
| Sistema exibe modal de confirmação antes da exclusão | Exclusão de registro ativo exige confirmação explícita do usuário |
| Sistema publica na fila de auditoria a cada mudança de estado | Toda mudança de estado é auditável, com quem mudou e quando |

## Lente DDD

Aplique esta lente quando o time opera em DDD ou tem vocabulário de domínio explícito: glossário, catálogo de eventos ou nomes de contexto no material recebido. Fora disso, Bounded Context, Ubiquitous Language e Domain Events usam o rótulo do time (módulo, área, integração).

### Ubiquitous Language

- Use os termos dos especialistas de domínio, não jargão genérico. O significado importa mais que a palavra, e o idioma não importa.
- Nomes concorrentes para o mesmo conceito dentro de um contexto viram `[LACUNA]`: alinhe antes de redigir.
- Entre especialistas de áreas diferentes, o mesmo conflito é sinal de fronteira entre contextos, não de lacuna.

### Subdomínio

| Subdomínio | O que muda no PRD |
|---|---|
| Core (o material recebido ou o PRD 0000 o nomeia como diferencial competitivo) | Rigor máximo: critérios precisos; questione se a solução preserva o diferencial; Não-objetivos entra pela regra da tabela de Seções |
| Supporting (nem Core nem Generic) | PRD padrão |
| Generic (existe produto ou pacote de mercado que cobre a capability) | Questione comprar, contratar ou reusar; pode virar não-objetivo |

### Bounded Context como âncora de escopo

- A fronteira se revela pelo vocabulário: dois especialistas usando termos diferentes para a mesma coisa, ou o mesmo termo para coisas diferentes, são indício de contextos distintos, não prova. A fronteira se confirma quando regras e motivos de mudança também divergem.
- A feature tem um contexto originário, nomeado no header (SKILL.md, Gravar).
- Quando vários contextos são tocados, o originário é dono da decisão; os outros entram em Dependências e Riscos, com o impacto na autonomia deles declarado.
- Escopo que cruza contextos sem origem clara é risco: pergunte qual contexto é o originário antes de redigir; se o usuário não souber ou recusar responder, o campo Contexto Originário do header recebe `[LACUNA]` e o PRD sai assim.
- Mais de um contexto com PRD próprio exige o PRD 0000 (ver PRD 0000, abaixo).

### Domain Events

- Evento é o reconhecimento de uma operação que mudou o estado e interessa a outro contexto. É contrato de domínio, não detalhe de implementação; mal documentado, vira acoplamento implícito.
- Evento, transição da máquina de estados e FR de transição saem da mesma pergunta, feita atributo por atributo: em que cenário muda, quem dispara, quem precisa saber.
- O catálogo de eventos vive no PRD 0000; cada PRD declara só o que produz e o que consome.

## Uma regra, um lugar

- **O FR é a única fonte da regra.** Solução Proposta, Glossário, Considerações Regulatórias, Critérios de Aceitação, Dependências, Perguntas em Aberto e o PRD 0000 citam o ID (`OFF-28`) e não repetem a condição, porque paráfrase diverge com o tempo; a exceção é o Glossário, que define o termo em uma linha e cita o ID (ver Seções). Se paráfrase e FR divergem, não apague nenhum dos dois nem escolha um lado: a divergência é decisão de negócio e entra como `[LACUNA]` em Perguntas em Aberto, citando o ID.
- **Um FR, uma unidade comportamental verificável.** Obrigações independentes, que podem falhar separadamente, vão em FRs separados, porque citação e teste apontam para uma só. Condição conjunta e efeito indivisível ficam no mesmo FR, porque fragmentá-los inventa estados intermediários que o negócio não tem.
- **Atributo condicional tem FR para fora da condição.** Atributo ou opção que só se aplica sob condição ganha um FR dizendo o que acontece quando é informado fora dela (rejeitado ou ignorado), porque essa é decisão de negócio, não de implementação.
- **Seção que só reafirma FRs não entra.** Métrica que repete um FR, critério de aceitação sem valor novo e dependência que descreve dos dois lados o mesmo acoplamento são custo sem informação.
- **Fato compartilhado vive no 0000.** Propósito do projeto, mapa de contextos, catálogo de eventos e acoplamentos entre contextos ficam no PRD 0000, e cada PRD os referencia, porque o que é repetido dos dois lados diverge.

## IDs

- **Formato.** `<PREFIXO>-nn` para FR e `<PREFIXO>-NFR-nn` para NFR, com prefixo por contexto (`OFF-12`, `BOOK-18`, `OFF-NFR-03`). O prefixo existe porque `FR-14`, numerado localmente em cada PRD, significava coisas diferentes em documentos que se citam. O prefixo é declarado na linha logo após a tabela do header (SKILL.md, Gravar) e na tabela de contextos do PRD 0000.
- **Definição.** `- **OFF-01 (Must)** condição.` A prioridade MoSCoW (Must, Should, Could, Won't) vai dentro dos parênteses; NFR não leva MoSCoW. Toda citação de ID resolve para uma definição em algum PRD da pasta.
- **Remoção.** ID removido morre e não é reciclado, porque citação para ID reaproveitado muda de significado em silêncio. Antes de alterar ou remover um FR, procure quem cita o ID fora deste PRD com `git grep -n <ID>` na raiz do repositório e liste esses citadores ao apresentar: a citação continua apontando para o ID, mas o texto atrás dele mudou.
- **Enumerações.** Estado, motivo de resultado, categoria e toda enumeração que o código vai carregar têm coluna Identificador na tabela que os define (ao lado do diagrama, junto do FR ou no Glossário), porque o código carrega esse nome, e nome inventado fora do PRD é decisão de linguagem tomada fora dele.

## PRD 0000

Quando há mais de um contexto com PRD próprio, o PRD 0000 concentra o que é compartilhado entre eles. O arquivo é `0000-<slug>-overview.md`, com `<!-- prd: overview -->` na primeira linha (SKILL.md, Gravar). Ele não contém regra de negócio: toda regra vive no PRD dono e é citada pelo ID.

A primeira coluna traz o par de nomes na forma da tabela de Seções (ver Seções).

| Seção (pt / en) | Conteúdo |
|---|---|
| Propósito (Purpose) | O projeto em um parágrafo |
| Contextos (Contexts) | Tabela: contexto, responsabilidade, PRD, prefixo de ID, posição (upstream, consome, devolve) e as regras de integração (persistência, direção de mudança de contrato) |
| Catálogo de eventos (Event Catalog) | Tabela: evento, produtor, consumidores, gatilho, IDs que o governam. Um evento só entra com consumidor que o PRD consumidor declara; evento sem consumidor é candidato, listado como tal, porque evento sem consumidor é acoplamento inventado |
| Fluxos entre contextos (Flows Between Contexts) | `sequenceDiagram` por fluxo (caminho feliz, revogação, falha); os rótulos citam IDs |
| Termos por contexto (Terms per Context) | Só quando o mesmo conceito tem nomes diferentes entre contextos: o conceito e o termo em cada contexto. Cada PRD mantém o glossário do seu contexto; o 0000 mantém a correspondência |
| Decisões delegadas a ADR (Decisions Delegated to ADR) | Tabela: decisão, exigência que a ADR precisa satisfazer (cita o NFR). O formato da ADR não é assunto do PRD |

Cada PRD referencia o 0000 na linha de prefixo do header, em vez de repetir propósito, mapa de contextos ou catálogo de eventos.

## Diagramas

Mermaid substitui prosa quando a estrutura é um grafo do tamanho indicado abaixo; abaixo do limiar, prosa:

- `stateDiagram-v2` para máquina de estados, a partir de 3 estados;
- `flowchart` para pipeline de decisão, a partir de 2 pontos de decisão, com desigualdades curtas nos nós de decisão;
- `sequenceDiagram` para fluxo entre contextos, a partir de 3 contextos trocando mensagens, no PRD 0000.

Regras:

- Rótulo de transição, aresta ou mensagem cita o ID do requisito e não reescreve a condição, porque o diagrama é índice, não segunda fonte.
- Ao lado do `stateDiagram-v2` vai a tabela estado, identificador, significado (ver IDs).
- Palavra reservada do Mermaid não serve de alias de participante nem de nó: `off` e `end` falham no parse mesmo em maiúsculas (`participant OFF as Offering` quebra; `on` passa no parser pinado). Use o nome completo.
- Todo bloco passa por `lint_mermaid.py` antes de apresentar (SKILL.md, Scripts).

## Seções

Cinco seções são obrigatórias, e o linter as trata como HARD: Resumo Executivo, Contexto e Problema, Usuário-alvo, Solução Proposta e, quando o PRD define IDs, Requisitos Funcionais. O PRD 0000 tem as seções da tabela em PRD 0000, acima.

Toda outra seção entra quando o critério da coluna "Entra quando" se cumpre, e nunca por forma: seção vazia, "Nenhuma." ou bullet inventado para completar contagem é defeito, não conformidade. A ordem das seções no PRD é a ordem da tabela. Três seções têm regras de forma que não cabem na célula; elas estão nas subseções depois da tabela.

A tabela é fechada: seção `##` fora dela não tem critério de entrada nem posição, e `lint_prd.py` a acusa como HARD (SKILL.md, Scripts). No PRD 0000 a lista fechada é a tabela da seção PRD 0000, acima. Conteúdo que não cabe em nenhuma seção da tabela vai para a seção que o cobre; `###` é subseção e fica livre. Seção que falta à tabela e não vem do pedido da sessão nem da convenção do repositório (SKILL.md, Precedência) muda a tabela primeiro, e com ela o script — o teste de sincronização cobra as duas; vindo de um dos dois, o HARD é mantido pela regra do passo Checar (SKILL.md, Workflow) e a tabela não muda.

A primeira coluna dá o nome da seção nos dois idiomas em que o PRD é escrito (SKILL.md, Idioma): o nome em português e, entre parênteses, o nome em inglês. O heading usa o nome do idioma fixado para o PRD; seção cujo nome é o mesmo nos dois idiomas aparece uma vez só.

| Seção (pt / en) | Entra quando | Forma |
|---|---|---|
| Resumo Executivo (Executive Summary) | Sempre | Um parágrafo de 3–5 frases: problema, solução, métrica primária |
| Alinhamento Estratégico (Strategic Alignment) | O material recebido ou a conversa cita o objetivo de negócio, OKR ou meta a que a feature responde | Um parágrafo de 3–5 frases conectando a objetivo de negócio |
| Contexto e Problema (Context and Problem) | Sempre | O problema; fatos e premissas (ver Tags); sem regra de negócio |
| Usuário-alvo / JTBD (Target User / JTBD) | Sempre | Um bullet por ator com o job |
| Oportunidade / Hipótese (Opportunity / Hypothesis) | Problema ainda em validação | Hipótese e como será validada |
| Solução Proposta (Proposed Solution) | Sempre | Capability, não mecanismo; máquina de estados ou pipeline em Mermaid quando passa o limiar de Diagramas, senão em prosa; regra citada por ID; fecha dizendo o que é downstream |
| Glossário de Domínio (Domain Glossary) | Há termo de domínio usado em dois ou mais requisitos sem definição no PRD 0000 nem no material recebido, ou com sinônimos concorrentes | Termo e definição de uma linha; termo cuja definição é regra cita o ID; termo de outro contexto aponta o PRD dono |
| Requisitos Funcionais (Functional Requirements) | Há requisito | Lista por subtítulo temático, cada linha um ID e uma condição (ver IDs e Uma regra, um lugar) |
| Domain Events | O contexto produz ou consome evento | Um parágrafo: produz X (ID), consome Y (ID); catálogo e sequências ficam no 0000 |
| Requisitos Não Funcionais (Non-functional Requirements) | Há atributo de qualidade ou restrição pelo qual o design será avaliado | `<PREFIXO>-NFR-nn`; atributo de qualidade e restrição, nunca mecanismo; exigência que uma ADR precisa satisfazer diz qual ADR |
| Considerações Regulatórias (Regulatory Considerations) | Norma identificada e lida | Fonte e data de leitura no topo; uma linha por artigo, com `→ ID que o modela` após o que o artigo diz (a norma e o artigo abrem a linha; depois do ID cabe uma nota de até 20 palavras, contadas por `lint_prd.py` como WARN, e o que não couber nela é regra e vive no FR); artigo não conferido no texto é `[PREMISSA]`; norma não identificada é bullet `[LACUNA]`, sem ID |
| Não-objetivos (Non-goals) | O material recebido ou a conversa cita funcionalidade adjacente que o PRD não cobre | Um bullet por exclusão: o que não faremos |
| Trade-offs Declarados (Declared Trade-offs) | Há decisão tomada na conversa ou no material recebido cuja alternativa rejeitada tem custo nomeável | `**Decisão.** *Custo:* … *Razão:* …`, até duas linhas; Custo e Razão são obrigatórios porque evitam re-litígio. Diferente de Não-objetivos (não faremos) e de Perguntas em Aberto (não decidido) |
| Métricas de Sucesso (Success Metrics) | O material recebido ou a conversa nomeia uma métrica ou um número-alvo | Uma linha por tipo que existe: leading (proxy, agora), lagging (resultado); e sempre um guardrail (o que não pode degradar; sem ele a métrica vira alvo; o linter o exige), marcado `[PREMISSA]` quando o material não o nomeia. Plataforma e infra: ver modes.md, Modo plataforma, infra, SDK ou API como produto |
| Critérios de Aceitação (Acceptance Criteria) | Há FR cujo resultado depende de mais de um valor numérico ou de ramificação | Cenário numérico em tabela (caso, entrada, valores intermediários, ramo, resultado); Dado/Quando/Então só para o que a tabela não expressa. Regras em Critérios de Aceitação, abaixo |
| Dependências e Riscos (Dependencies and Risks) | Há dependência ou risco fora do controle do contexto, ou o campo do header declara contexto afetado em `; afeta` (SKILL.md, Header) | Tabela: item, tipo, impacto; uma linha por contexto afetado do header, mesmo quando o impacto é só observar; acoplamento entre contextos cita o 0000, e só o lado dono o descreve |
| Perguntas em Aberto (Open Questions) | Há premissa que, se falsa, derruba a abordagem do PRD (Tags), `[PREMISSA]` ou `[LACUNA]` citada por um FR Must ou pela Solução Proposta, divergência entre FR e paráfrase (Uma regra, um lugar) ou intenções concorrentes em reverse PRD | Uma linha por pergunta: a pergunta, o impacto, o dono e o critério que a resolve, quando conhecidos. Regras em Perguntas em Aberto, abaixo |
| Ponto de Maior Fragilidade (Weakest Point) | Há decisão de julgamento sobre fatos conhecidos (corte de escopo, threshold, priorização ou usuário-alvo) que, se errada, invalida a Solução Proposta ou a métrica primária | Última seção de conteúdo, só Referências depois: a decisão, o vetor de ataque concreto e o convite ao autor para desafiá-la antes de aprovar. Regras em Ponto de Maior Fragilidade, abaixo |
| Referências (References) | Há fonte usada | Link, artigos lidos, data de leitura, PRDs citados |

### Critérios de Aceitação

- A primeira coluna da tabela nomeia o caso, porque o teste cita o cenário pelo nome.
- Cada Dado/Quando/Então cita o FR que exercita.
- "Usuário pode X" é tautologia, não critério.

### Perguntas em Aberto

- O conteúdo é o que a coluna "Entra quando" da tabela de Seções lista, e nada além: o critério está escrito lá, uma vez. A premissa que derruba o PRD é o primeiro item dessa coluna, e por ele a seção entra; quando existe, ela é a primeira linha, na forma fixada em Tags. Bullet com "se falsa" em outra seção é a mesma premissa declarada fora do lugar, e `lint_prd.py` o acusa como HARD.
- Decisão tomada não entra: com custo, vive em Trade-offs Declarados; sem custo, vive no FR que a aplica. Decisão arquitetural delegada é candidata a ADR (ver PRD 0000, Decisões delegadas a ADR).

### Ponto de Maior Fragilidade

- É distinto das tags. `[PREMISSA]` pode ser falsa (risco factual); `[LACUNA]` é informação que falta (risco de cobertura). Aqui a decisão é sobre fatos, sem lacuna, e ainda assim contestável: corte de escopo, threshold, priorização, usuário-alvo.
- É exposição, não auto-correção: quem tem contexto para resolver é o autor.
- Calibre ao custo do erro: a decisão só entra se, estando errada, invalida a Solução Proposta ou a métrica primária. Fraqueza menor nomeada para parecer rigor é auto-crítica cosmética.
- `[LACUNA]` material é a que entra em Perguntas em Aberto pela coluna "Entra quando" da tabela de Seções (ver Seções); lacuna fora desse critério não é material aqui. Com uma delas, aponte a decisão que depende da lacuna e o que a validação mudaria, sem fabricar vetor de ataque.

## Redação

Tom direto, preciso, orientado a decisão. Sem linguagem genérica ("melhorar experiência") que não tenha âncora em métrica ou comportamento. O texto é lido por humanos e por LLMs downstream; por isso:

- **Voz declarativa e ativa.** "O sistema bloqueia a ativação", não "seria bloqueado".
- **Sem hedging.** A lista de palavras é a de `lint_prd.py`, que as acusa como WARN; não há segunda lista.
- **Sem meta-narração.** Nada de "este PRD descreve", "vamos discutir", "é importante notar": o título já diz o que o documento é.
- **Sem qualificador redundante nem filler.** "De modo a" vira "para"; "devido ao fato de que" vira "porque"; "com zero X necessário" vira "sem X".
- **Um conceito por parágrafo.** Dois parágrafos adjacentes sobre o mesmo ponto se fundem. Regra dita duas vezes ou FR com mais de uma condição é o que faz o PRD crescer sem informação (ver Uma regra, um lugar).
- **Preserve o contexto de decisão.** A Razão do trade-off, o racional do guardrail e o "se falsa" da premissa que derruba o PRD carregam sinal.
- **Hierarquia.** `#` título, `##` seções, `###` subseções; lista para requisitos e critérios; tabela para comparação, dependência e cenário numérico.
