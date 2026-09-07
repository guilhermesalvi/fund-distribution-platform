# Design

**Objetivo:** definir *como* construir — estrutura, componentes, interfaces, o que reusar — com profundidade proporcional ao **risco**, não ao tamanho. Design não gera código; prepara a implementação para não improvisar.

Leia até o fim antes de agir.

**Pule ou encolha** conforme SKILL.md, Tiers. Sem decisão arquitetural nem risco nomeado, a estrutura é dita em uma ou duas linhas do plano inline do Execute e este arquivo não é criado. Com risco nomeado, bastam duas seções curtas atacando aquele risco, não o template inteiro.

---

## 1. Carregar contexto

Leia, nesta ordem:

1. `changes/NNNN-<feature>/spec.md` (delta) e a `spec.md` viva da capability. A spec é o contrato; o design não a reinterpreta. Se o design precisar decidir *comportamento*, volte à spec (refine o contexto, não o erro).
2. **`project-memory.md`, nas Decisões `AD-NNN` ativas, obrigatório antes de qualquer escolha.** Cada decisão ativa é restrição de projeto. Conflito entre uma decisão anterior e o melhor para esta feature exige escolha explícita: conformar ou superseder (memory.md, Decisões e ADRs). Ignorar em silêncio cria inconsistência invisível entre features.
3. PRD, quando existe: `[PREMISSA-CRÍTICA]` do PRD e Trade-offs Declarados são restrições; Dependências e Riscos do PRD alimentam a seção de riscos; NFRs do PRD são a origem primeira dos critérios de avaliação (seção 4). PRD 0000, quando existe: o mapa de contextos fixa quem é upstream e a direção de mudança de contrato; o catálogo de eventos fixa produtor e consumidores da tabela Domain Events; as Decisões delegadas a ADR são decisões deste design ou de ADR própria (memory.md, Decisões e ADRs), com a exigência que o PRD cita (NFR) como critério.

---

## 2. Análise da base de código

**Estratégia para base grande.** Não leia tudo. Use a spec como guia de foco:

1. Identifique módulos e arquivos diretamente relacionados ao escopo.
2. Leia a estrutura de diretórios antes de abrir arquivos.
3. Priorize nesta ordem: interfaces e contratos, depois entidades de domínio, depois serviços e casos de uso, por último infraestrutura.
4. Leia implementação completa só quando assinatura e nome não bastam.
5. Declare o que foi lido e o que foi ignorado. Base extensa: "Analisei [X, Y, Z] por serem diretamente relevantes. [A, B] foram ignorados — podem conter restrições não consideradas."

**Tudo que a base impõe é `[FATO]`; tudo que você inferiu do padrão é `[PREMISSA]`.** Padrão inferido de dois arquivos não é convenção do projeto.

**Fontes da verdade: código e repositório.** Quem explica o sistema conta uma história; o repositório registra a que aconteceu. Antes de julgar a base, rode `python <skill-dir>/scripts/hotspots.py <repo>` (git log da janela, default 90 dias). Os poucos arquivos que concentram 90% das mudanças, cruzados com o número de autores, são indício de onde o remendo se acumula e de ownership difuso, e é por ali que a leitura começa. Indício não é prova: confirme com CODEOWNERS, ADRs e quem conhece a área antes de chamar de dívida. Complete com o que os pipelines de deploy dizem sobre as unidades de deploy (repositório não é deployable) e com o mapa de times (CODEOWNERS, organograma). Pela Lei de Conway, a estrutura de comunicação dos times antecipa a estrutura do sistema, e serve de mapa quando o acesso ao código demora. Peça o script, não a resposta: evidência que precisa de baseline ou comparação vem de script determinístico, porque leitura estocástica muda a cada execução e não se compara.

**Suspensão de julgamento.** Preocupação classificada como dívida, hack ou fragilidade só é `[FATO]` quando acompanhada da decisão que a explica (ADR, commit, PR, pessoa); sem ela é `[PREMISSA]`. Um desenho que parece errado hoje pode ter sido o melhor sob as restrições da época, e quem julga sem contexto propõe a refatoração que ninguém consegue fazer deploy. Learning docs (notas de exploração que você gera para si: estrutura, entry points, fluxos) ficam fora de `docs/`; documentação do projeto é a que o time consome.

**Sinalização de preocupações (obrigatória enquanto lê).** Ao percorrer as áreas que a feature toca, registre em `## Riscos e Preocupações`: código frágil (acoplamento, função grande, estado implícito), dívida (hack, API deprecada), risco de segurança (entrada não validada, segredo exposto), gargalo (N+1, loop sem limite, índice ausente), lacuna de teste no caminho da feature, hotspot do script. Cada linha traz a decisão que a explica ou "nenhuma encontrada". **Toda preocupação tem mitigação**: como o design ou uma task de follow-up a trata. "Nenhuma encontrada" é entrada válida.

**Reuso.** O que já existe e serve? Cada componente novo referencia o padrão existente que segue. Reuso reduz tokens e erro; componente sem "reusa" precisa justificar por que não.

---

## 3. Design orientado a risco (Fairbanks)

Antes de escolher técnicas ou preencher seções, liste os riscos: *o que pode falhar caro nesta mudança?* Fontes: dimensões implícitas da spec, preocupações da base, `[PREMISSA-CRÍTICA]`, integrações, dinheiro, regulação, contrato público, migração de dados.

Para cada risco, escolha a **técnica de design que o reduz** e só faça aquele trabalho. Seções do template que não atacam risco nomeado ficam curtas ou fora.

| Risco típico | Técnica proporcional |
|---|---|
| Consistência entre contextos / evento perdido | Contrato de domain event explícito; decisão eventual vs forte; outbox ou equivalente |
| Concorrência, duplicata, retry | Modelo de idempotência; chave; lock otimista; tabela de transições de estado |
| Integração externa instável | Anti-corruption layer; timeout/retry/circuit breaker declarados; fallback |
| Dinheiro / cálculo financeiro | Modelo de domínio com tipos de valor; regras isoladas e testáveis; precisão decimal declarada |
| Migração de dados / compatibilidade | Estratégia de migração; janela de dupla escrita; plano de rollback |
| Performance | Orçamento (p95, throughput) e onde ele é gasto; índice; paginação |
| Segurança / dado regulado | Fronteira de autorização; retenção; mascaramento; auditoria |

Risco sem técnica é aceite consciente: registre em Riscos com "aceito porque".

**Não imponha estilo arquitetural.** Se a base segue Hexagonal/tactical DDD, o design fala em ports, adapters, aggregates e usa a estrutura existente. Se a base é outra coisa, o design segue a base — introduzir estilo novo é decisão de projeto (`AD-NNN`), não decisão de feature. Cerimônia sem risco que a justifique é peso morto.

---

## 4. Critérios antes das abordagens

Fixe os critérios de avaliação antes de existir qualquer abordagem, porque quem propõe e julga é o mesmo agente: critério escrito depois da proposta vira racionalização, e o gate de aprovação vira carimbo. Três passos, cada um apresentado ao usuário antes do seguinte.

1. **Critérios.** Lista numerada dos critérios pelos quais a solução será avaliada, cada um com origem (NFR do PRD, dimensão implícita da spec, `AD-NNN`, restrição de custo ou prazo). Critério é atributo de qualidade ou restrição, nunca mecanismo: "sem ponto único de falha", não "usar Bloom filter". Mecanismo no critério fecha a busca antes de ela começar.
2. **Crítica dos critérios.** Que critério falta para este tipo de problema (falso positivo e falso negativo em segurança, frescor do dado, privacidade, comportamento offline, custo de operação)? Qual trade-off decide a escolha e não está fixado? Critério de negócio ausente ou trade-off não fixado volta ao PRD como pergunta com o critério que a resolve (specify.md, Origem e modo); critério de solution space o usuário fixa aqui. Nenhuma abordagem antes de o usuário confirmar a lista.
3. **Abordagens (Large/Complex).** 2–3 abordagens materialmente viáveis (que alguém defenderia; espantalho para fazer a preferida parecer boa não conta), mesmo escopo (alternativa de escopo não é alternativa de abordagem), avaliadas contra os critérios fixados, que viram colunas da tabela, mais as quatro perguntas abaixo. Recomendada primeiro, com o racional, para evitar paralisia por análise. Confirme a escolha com o usuário antes de detalhar componentes. Medium: só os passos 1 e 2, em três linhas, e uma abordagem.

As **quatro perguntas** de avaliação de uma decisão arquitetural:

1. Atende aos objetivos de negócio (PRD, Critérios de Sucesso da spec)?
2. Respeita os atributos de qualidade (dimensões implícitas, NFRs)?
3. Respeita as restrições (`AD-NNN` ativas, base existente, regulação, time)?
4. **Existe forma mais barata ou menos arriscada de fazer o mesmo?**

As três primeiras o design já lê; a quarta é a que costuma ficar sem resposta e a que paga o salário do arquiteto. Complexidade se converte em custo (número de componentes combinado com o número de interconexões) e complexidade não justificada é custo desnecessário. Tabela por abordagem: o que é, resposta a cada critério e pergunta, custo (TCO, não só construção), risco que reduz e risco que introduz.

---

## 5. Pesquisa e cadeia de verificação

Ao pesquisar, projetar ou decidir, em qualquer entrada, siga a cadeia em ordem estrita; nunca pule para o último passo com os anteriores disponíveis:

1. **Base de código**: padrões, convenções, código vizinho ao escopo (seção 2).
2. **Docs do projeto**: README, `docs/`, `project-memory.md` (decisões `AD-NNN` ativas), PRD.
3. **Documentação oficial** da biblioteca ou serviço (Context7 quando disponível, senão busca web em fonte primária).
4. **Busca web**: fontes reputadas, padrões da comunidade.
5. **Sinalize incerteza**: "não tenho certeza de X; meu raciocínio é Y, verifique". Nunca fabrique API, padrão ou comportamento: invenção propaga em cascata, da spec ao design, do design às tasks e das tasks ao código. "Não encontrei documentação" é resposta válida.

Gatilhos no design: biblioteca nova, API desconhecida, feature sensível a performance ou segurança, padrão que a base ainda não usa. Registre achados brevemente no design (uma linha com fonte).

---

## 6. Componentes, contratos e dados

**Componentes.** Cada um: propósito (uma frase), localização (path real), interfaces (assinaturas com tipos), dependências, o que reusa. Componente cujo propósito não cabe em uma frase sem "e" é sinal de divisão; a divisão se decide pela coesão e pelos motivos de mudança, não pela contagem de responsabilidades. Interfaces vêm antes de implementação — são o que as tasks consomem (`Interfaces: consumes / produces` no tasks.md).

**Domain events** (obrigatório quando a spec os tem). Por evento: nome, produtor, consumidores conhecidos, payload semântico, chave de partição/ordenação, garantia de entrega (at-least-once é o normal; idempotência do consumidor torna o processamento seguro sob reentrega, mas não é entrega exactly-once), versionamento do schema. Evento mal documentado é acoplamento implícito entre contextos.

**Modelo de dados** quando a feature toca persistência: entidades, relacionamentos, invariantes, migração.

**Tratamento de erro.** Tabela com colunas cenário, tratamento e impacto no usuário/consumidor. Todo `IF … THEN` da spec aparece aqui com o mecanismo escolhido.

---

## 6.5. Unidade de deploy e reuso

A decisão mais cara de um design é criar uma **unidade de deploy** nova — serviço, aplicação, biblioteca versionada. Três conceitos distintos: **módulo** (fronteira de código e de dependência: assembly, pacote de linguagem, namespace com interface pública), **pacote de release** (o que é versionado e publicado: biblioteca, imagem) e **unidade de deploy** (o que sobe e cai junto: aplicação, serviço, worker). Um módulo pode viver dentro de um deployável sem release próprio; uma biblioteca é pacote de release sem deploy próprio. Toda discussão de arquitetura diz de qual dos três está falando.

**Ordem de preferência, sempre nesta sequência:** primeiro, mudança dentro do deployável existente; depois, novo módulo dentro do deployável existente (monólito modular); só então, novo deployável. Um sistema complexo que funciona evoluiu de um simples que funcionava; decompor em serviços depois é decisão de deploy e é reversível, nascer distribuído não é.

**O que justifica um novo deployável** é a demanda de **deploy independente**, e ela vem tipicamente de: time separado com ritmo próprio; stack diferente com time próprio em torno dela; estrangulamento de legado (time do novo e time do velho precisam de esteiras separadas). **O que raramente justifica sozinho:** escalabilidade (réplicas do monólito escalam; separar processos troca desempenho por escala), resiliência (réplicas + load balancer entregam), "separação de responsabilidades" (módulo entrega). Isolamento de falha, perfil de carga incompatível e exigência regulatória ou de segurança são justificativas legítimas quando nomeiam a falha, a carga ou a norma e mostram por que réplica ou módulo não bastam. Comunicação interprocesso custa serialização, transporte, desserialização e I/O; o ganho tem de ser expressivo o suficiente para pagar isso *e* a gestão de contrato.

**Todo deployável novo carrega custo fixo**, e o design o declara antes de propor: contrato de interface, versionamento, compatibilidade retroativa (interface pública transforma bug em feature — você mantém o que expôs), e **um dono** nomeado. Deployável sem dono não tem qualidade; com dois donos, nenhum tem. Mudança demandada por um time num deployável de outro entra na priorização do dono; se a demanda for constante, transfira o ownership ou replique. Vários times editando a mesma unidade é situação a evitar, não veto: quando inevitável, o dono único integra e decide, e o Rastreamento de complexidade registra o porquê.

**Código compartilhado (REP — Reuse/Release Equivalence).** Toda unidade de reuso entre módulos é uma unidade de release, com o custo acima. Antes de propor biblioteca compartilhada, responda em ordem:

1. **Estabilidade e divergência:** se muda com frequência e os consumidores podem evoluir em ritmos diferentes, replicar costuma custar menos que versionar. Se muda com frequência mas os consumidores não podem divergir (regra regulatória, contrato de mensagem), a resposta é biblioteca versionada com dono e release disciplinado. Se é estável, é candidata a biblioteca versionada. O critério é o custo de release contra o custo de divergência, não a frequência sozinha.
2. **Já existe?** Problema estável e comum já tem pacote público mantido; use-o em vez de assumir versionamento interno.
3. **Dono e escopo:** um time dono; sem lógica de negócio em biblioteca de plataforma (plataforma fornece ecossistema — CI/CD, observabilidade, mensageria —, não regra). Regra de negócio compartilhada é sinal de contexto mal delimitado ou de time de subsistema complicado, não de "utils".
4. `Utils`/`Shared`/`Common` como destino é o cheiro da regra não aplicada: acoplamento aferente alto, dependência que arrasta 300 coisas para validar um CPF.

**Fronteiras entre módulos.** Sem ciclo entre unidades que têm fronteira própria (entre pacotes, entre módulos, entre serviços), porque ciclo entre fronteiras impede release e teste isolados. Relação bidirecional entre classes do mesmo módulo ou agregado (navegabilidade no modelo de domínio, entidade e coleção filha) é legítima enquanto fica dentro da fronteira; vira defeito quando a atravessa. Módulo é consumido **só pela sua interface pública**; nunca instancie classe interna de outro módulo. Coesão é o critério: quanto mais um módulo se resolve com o que tem dentro, melhor a fronteira.

Tudo nesta seção é preferência com justificativa, não veto: decisão `AD-NNN` ativa, risco concreto nomeado ou restrição do projeto vence a preferência, e o Rastreamento de complexidade registra o porquê.

Registre no design: a unidade de deploy escolhida (uma linha quando a mudança fica no deployável existente) e, para deployável ou biblioteca nova, a justificativa pelo critério de deploy independente, o dono, o contrato e o versionamento — além da linha correspondente no Rastreamento de complexidade.

## 7. Decisões e rastreamento de complexidade

**Decisões técnicas**, só as não óbvias: decisão, escolha, racional, tipo. O tipo distingue **restrição de produto ou contrato público** (API, evento, formato persistido ou exposto a terceiros: muda com versionamento e aviso) de **decisão interna** de implementação (muda sem aviso); modes.md, Proveniência. Decisão que fixa convenção ou restrição para features futuras vira ADR (memory.md, Decisões e ADRs); decisão local à feature fica só na tabela.

**Rastreamento de complexidade** — obrigatório quando o design **viola** uma decisão ativa, uma convenção da base ou o princípio de simplicidade (abstração para uso único, camada extra, flexibilidade não pedida), e **sempre** que propõe novo deployável, biblioteca compartilhada ou dependência entre módulos que antes não existia:

| Violação / adição | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| Novo deployável `X` | [time separado / stack / estrangulamento] — dono: [time] | Módulo no deployável existente rejeitado porque … |
| Biblioteca compartilhada `Y` | Estável desde …; sem pacote público equivalente; dono: [time] | Replicar rejeitado porque … |

Tabela vazia é o estado normal. Preenchida sem justificativa concreta é o sinal de design inflado. "Escala" ou "resiliência" como justificativa de deployável novo, sem a falha nomeada, é justificativa insuficiente.

---

## Template: `changes/NNNN-<feature-slug>/design.md`

```markdown
<!-- sdd: design | tier: large | spec: ./spec.md -->
# Reserva Parcial no Bookbuilding — Design

| | |
|---|---|
| **Status** | Rascunho / Aprovado |
| **Autor** | [nome] |
| **Data** | AAAA-MM-DD |
| **Spec** | ./spec.md |
| **Confiança** | Média — [razão] |

## Contexto de design

[Restrições vindas da spec, do PRD e das decisões AD-NNN ativas. Base lida vs ignorada. Hotspots de `hotspots.py` (janela, arquivos, autores) e o que os pipelines e o mapa de times dizem sobre deployables e donos.]

## Critérios de avaliação

| # | Critério | Origem | Fixado por |
|---|---|---|---|
| C1 | O livro lido pelo Allocation é idêntico ao congelado | BOOK-NFR-02 | PRD |
| C2 | Resultado visível ao ReservationBook em até 5s após `BookProcessed` | usuário, 2026-09-05 | usuário |

Trade-off não fixado devolvido ao PRD: [nenhum | descrição e pergunta registrada].

## Riscos e técnicas

| Risco | Fonte | Técnica adotada | Onde no design |
|---|---|---|---|
| Duplicata de reserva por retry do canal | RSV-10 | Idempotency key persistida; unicidade (investorId, offerId) | Componente ReservationService |

## Abordagens consideradas
<!-- Large/Complex; uma coluna por critério fixado, mais as quatro perguntas -->

| Abordagem | O que é | C1 | C2 | Objetivos de negócio | Restrições | Mais barato / menos arriscado? | Risco que reduz / introduz |
|---|---|---|---|---|---|---|---|

**Escolhida:** [qual] — [racional em 2–3 linhas]

## Visão da arquitetura

[Parágrafo + diagrama mermaid quando ajuda. Como os componentes interagem para atender às histórias P1.]

## Unidade de deploy

[Uma linha quando a mudança fica no deployável existente. Para deployável ou biblioteca nova: justificativa pelo critério de deploy independente, dono, contrato, versionamento, compatibilidade retroativa.]

## Reuso e pontos de integração

| Existente | Localização | Como usar |
|---|---|---|

## Componentes

### [Nome]
- **Propósito:** …
- **Localização:** `src/…`
- **Interfaces:** `Method(param: Type): Return` — …
- **Dependências:** … (sem ciclo entre módulos; consome outros módulos só pela interface pública)
- **Reusa:** …

## Domain Events

| Evento | Produtor | Consumidores | Payload | Chave / ordem | Entrega |
|---|---|---|---|---|---|

## Modelo de dados
<!-- quando aplicável -->

## Tratamento de erros

| Cenário (ID) | Tratamento | Impacto |
|---|---|---|

## Riscos e Preocupações

| Preocupação | Localização (file:line) | Decisão que explica (ADR, commit, PR) ou nenhuma | Impacto | Mitigação |
|---|---|---|---|---|

## Decisões técnicas

| Decisão | Escolha | Racional | Tipo (contrato público / interna) | ADR? |
|---|---|---|---|---|

## Rastreamento de complexidade

| Violação | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|

## Arquivos a criar ou modificar

[Lista com responsabilidade de cada um — é o insumo direto de tasks.md.]

## Ponto de Maior Fragilidade

[Decisão de design mais contestável; vetor de ataque; convite ao desafio.]
```

---

## Critério de saída para Tasks

O design está pronto quando: critérios de avaliação fixados e criticados antes das abordagens; estrutura clara e acordada; responsabilidade de cada componente definida; interfaces com assinatura; restrições da base mapeadas (lidas vs ignoradas declaradas); todo risco nomeado tem técnica ou aceite; unidade de deploy declarada e, se nova, justificada com dono; decisões `AD-NNN` conformadas ou supersedidas; `[LACUNA]` no caminho zero; Ponto de Maior Fragilidade nomeado.

Apresente e pare: gate de aprovação (SKILL.md, Posicionamento) antes de Tasks.

---

## Critérios de qualidade (passada Tier 2)

Cada item cita a seção que contém a regra.

- Profundidade proporcional ao risco: seção longa sem risco por trás é inflação; risco nomeado sem técnica ou aceite é buraco (seção 3).
- Critérios fixados e criticados antes das abordagens; trade-off não fixado devolvido ao PRD (seção 4).
- Preocupação sem a decisão que a explica marcada como `[PREMISSA]`; hotspots do script na tabela (seção 2).
- Nada de comportamento decidido aqui que devesse estar na spec (seção 1).
- Todo componente novo referencia reuso ou justifica ausência; interfaces com tipos; domain events com contrato completo (seções 2 e 6).
- Decisões ativas conformadas ou supersedidas; rastreamento de complexidade honesto (seção 7).
- Unidade de deploy e biblioteca compartilhada justificadas; sem ciclo entre módulos; módulos consumidos só pela interface pública; preferência vencida por decisão ativa ou risco registrada no Rastreamento; a quarta pergunta respondida por abordagem (seções 4 e 6.5).
- Base grande: lido vs ignorado declarado (seção 2).
- Ponto de Maior Fragilidade presente (specify.md, Ponto de Maior Fragilidade).
