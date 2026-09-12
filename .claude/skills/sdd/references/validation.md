# Validação da SDD

## Checagem de forma

Antes de apresentar um artefato, leia o arquivo gravado e confira cada item da lista do seu tipo. Todo achado se corrige antes de apresentar, com uma nova leitura do trecho corrigido; achado de forma exigido pelo pedido ou comprovado pela convenção fica como está e é relatado no chat com a origem, usando "mantido por pedido" ou "mantido por convenção" (Forma mantida por pedido ou convenção). Achado que não conseguiu corrigir é relatado ao apresentar, sem declarar validação completa. Depois da checagem, faça a revisão de conteúdo (Revisão por entrada).

Apresentação com achados remanescentes é permitida; não equivale a aprovação nem abre a próxima entrada sem os pré-requisitos (workflow.md, Aprovação e autorizações). O gate do Execute tem protocolo próprio: execução inicial e até duas tentativas de correção, total de três execuções antes de parar (execute.md, Ciclo por task).

### Numeração

Antes de criar a pasta de uma mudança ou uma ADR, liste os filhos diretos da pasta, tome o maior `NNNN` e some 1; pasta sem item começa em 0001. O slug é kebab-case ASCII minúsculo. Antes de apresentar qualquer artefato numerado, confira que nenhum número se repete na pasta; a duplicata nasce quando dois branches alocam o mesmo número. Renumere o item cujo branch entra depois: mova-o para o próximo número livre, atualize quem o cita e confira de novo.

### Spec

- Comentário de máquina na primeira linha não vazia, na forma `<!-- sdd: spec | capability: <domínio>/<capability> [| prd: <path> | prd-rev: git:<hash>] -->` (specify.md, Comentário de máquina).
- Linha de prefixo logo abaixo do título, na forma `Prefixo dos requisitos: \`RSV\`.` (ou `Requirement prefix:`).
- `## Contexto` e `## Requisitos` presentes, sem seção duplicada; toda `##` na lista de Seções (specify.md, Seções), com a seção herdada do PRD como única tolerância.
- Todo requisito com um `SHALL` por linha, num padrão EARS (WHEN, WHILE, WHERE, IF ou `The <system> SHALL`), na forma `- **PFX-NN** — texto`, sem termo vago.
- Prefixo dos IDs igual ao declarado; ID único; ID aposentado (linha `Aposentados:`) não reutilizado; número pulado só quando consta dos aposentados.
- Prefixo distinto de todo prefixo declarado em PRD e sem as duas primeiras letras em comum com algum deles.
- Com `prd:`: o PRD existe; `prd-rev` igual a `git hash-object <prd>`; toda citação `X-nn` ou `X-NFR-nn` resolve para uma definição no PRD; `## Rastreabilidade` presente, com todo FR em escopo e todo cenário da tabela de Critérios de Aceitação que cita FR em escopo, e só IDs EARS que existem na spec; linha só com IDs de PRD que nenhum requisito cita começa com `Critério de design:`.
- Contexto com 3 a 5 linhas; Requisitos com subtítulos `###` a partir de 8 requisitos e sem eles abaixo disso.
- Tags só `[PREMISSA]` e `[LACUNA]`; nenhum placeholder, hedging ou meta-narração; todo link Markdown local resolve.

### Design

- Comentário de máquina `<!-- sdd: design | spec: ../spec.md [| scope: ...] -->` cujo `spec:` resolve para arquivo; todo ID em `scope:` existe na spec.
- Toda `##` na lista de Seções, na ordem dela, sem seção vazia ou reduzida a "Nenhuma." ou "N/A" (design.md, Seções).
- Sem `## Abordagens`, a última linha de `## Critérios de avaliação` é `Sem alternativa real: <motivo>`; com a seção, essa linha não existe.
- Todo requisito `IF ... THEN` da spec (no escopo) citado em `## Tratamento de erros`.
- Seção com mais de dez linhas de corpo só quando o assunto dela aparece em `## Riscos e técnicas`; em `## Componentes`, cada `- **Propósito:**` com uma frase e um propósito.
- Todo bloco Mermaid lido linha a linha: fence fechado, sintaxe que renderiza, nenhuma palavra reservada como alias.
- Tags só `[PREMISSA]` e `[LACUNA]`; nenhum placeholder, hedging ou meta-narração.

### Tasks

- Comentário de máquina `<!-- sdd: tasks | spec: ../spec.md [| design: ./design.md] [| scope: ...] -->` cujos destinos resolvem para arquivo.
- Parágrafo "Como este repositório testa" antes de `## Comandos de Gate`, com a contagem-base de testes do gate Build.
- `## Comandos de Gate`, `## Plano de execução` e `## Rastreabilidade` presentes; toda `##` na lista de Seções (tasks.md, Seções do `tasks.md`).
- Tabela Comandos de Gate com linhas só entre `quick`, `full`, `build` e `Mutação`, nenhuma célula de comando vazia; a linha `Mutação` presente quando a tabela Riscos e técnicas do design tem risco que obriga mutação (verify.md, Mutação); todo valor de `Gate` usado tem linha.
- Cada task `### Tn:` ou `### TCn:` com ID único e os campos O quê, Onde, Depende de, Requisito, Interfaces, Pronto quando, Tests e Gate, uma vez cada e preenchidos (tasks.md, Campos).
- `Pronto quando` com o comando do gate da task entre crases, copiado da tabela, e ao menos um critério de comportamento; `Tests` e `Gate` na combinação que o campo `Gate` fixa; última task de cada fase com `build`.
- Todo requisito da spec (no escopo) com task e toda task com ao menos um requisito existente; `## Rastreabilidade` coerente com os campos `Requisito` nos dois sentidos.
- Dependências só para trás na ordem do plano, sem ciclo e sem `T` dependendo de `TC`; toda task citada no plano com corpo e toda task `T` com corpo citada no plano.
- `O quê` com um entregável; `Onde` com paths reconhecíveis; `Tests` `none` só quando todo path de `Onde` é config, schema ou migration.
- Tags só `[PREMISSA]` e `[LACUNA]`; nenhum placeholder, hedging ou meta-narração.

### ADR

- Título `# ADR NNNN: título`; linha `Participantes:` com nome antes da primeira `##`.
- `## Contexto`, `## Decisão`, `## Alternativas consideradas` e `## Consequências` presentes, nessa ordem, sem seção vazia; nenhuma `##` fora dessas e de `## Regras derivadas`, que quando existe é a última (adr.md, Template).
- Alternativas consideradas com tabela preenchida: cada linha com alternativa e razão.
- Consequências com a linha `- Negativas: <texto>`.
- `## Regras derivadas` com ao menos um bullet, cada um com o path do arquivo onde a regra vive entre crases (adr.md, Conformar e superseder).
- `Substitui: NNNN` e `Substituída por: NNNN` apontando para ADR existente na pasta, com a linha recíproca na outra ADR.
- Tags só `[PREMISSA]` e `[LACUNA]`; nenhum placeholder, hedging ou meta-narração.

### Forma mantida por pedido ou convenção

Pedido válido para manter um achado de forma nomeia literalmente a seção, o campo ou a forma de onde ele sai, por exemplo "inclua uma seção Plano de Rollout no design". Convenção válida é forma comprovada em pelo menos três artefatos commitados do mesmo tipo, ou escrita no CLAUDE.md do repositório. Diga o número de exemplares no chat.

Para reconhecer uma convenção por exemplos, use a versão dos arquivos presente em HEAD. Liste os arquivos com `git ls-tree -r --name-only HEAD -- docs/specs` e filtre os Markdown do tipo em análise: `spec.md`, `design.md` ou `tasks.md`, separadamente. Leia cada exemplo com `git show "HEAD:<caminho>"`. A convenção precisa aparecer em pelo menos três desses exemplos. Um arquivo apenas staged ou untracked não conta. Uma alteração local em arquivo já commitado também não altera a convenção de HEAD. Se HEAD não existir, não há convenção comprovada por exemplos; a convenção escrita no guia do repositório continua sendo uma fonte válida. Para ADR, aplique o diretório e a seleção de (adr.md, Arquivo).

### Heurísticas de redação

Escreva de forma declarativa. Hedging, meta-narração, placeholder e tag fora de `[PREMISSA]` e `[LACUNA]` são achados da checagem de forma nos quatro artefatos. A revisão aplica (prose.md, Checklist editorial), sem novo ciclo de estilo.

Checagem de forma limpa comprova o esqueleto; a revisão confere o conteúdo.

## Revisão por entrada

Faça esta revisão antes de apresentar cada artefato, depois da checagem de forma. Vale para todas as entradas: nenhuma seção existe só para cumprir a forma.

A lista da entrada é fechada. Em Specify, Design, Tasks e ADR:

- percorra o artefato inteiro para cada item e dê ao item a nota `max(0, 100 - 20 × ocorrências)`; uma ocorrência já derruba o item, e a nota existe para registrar quantas;
- item abaixo de 90 é reescrito; item com 90 ou mais fica como está;
- reescreveu, dê nota de novo: são no máximo duas passadas por artefato;
- item que continuar abaixo de 90 na segunda passada não segura o artefato: apresente e diga no chat qual item é, com a nota e o que falta.

Em Execute e Verify os itens são binários, atendido ou não: item não atendido se corrige dentro dos tetos do próprio ciclo (execute.md, Ciclo por task; verify.md, Gaps e tasks de correção).

| Ocorrências | Nota | Ação |
|---|---|---|
| 0 | 100 | Item passa |
| 1 | 80 | Corrigir o item |
| 2 | 60 | Corrigir o item |
| 3 | 40 | Corrigir o item |
| 4 | 20 | Corrigir o item |
| 5 ou mais | 0 | Corrigir o item |

### Revalidação após revisão

A revisão vem depois da checagem de forma. Se alterou o artefato, repita a checagem de forma sobre os trechos alterados; corrija o que achar uma vez e releia para conferir. Se persistir, liste no chat. Essa passada extra não reabre indefinidamente a revisão. O checklist editorial (prose.md, Checklist editorial) concretiza a revisão existente, sem nota, seção ou ciclo adicional.

### Specify

- `SHALL`, ID único e padrão EARS já estão na checagem de forma; aqui: o padrão está correto, o valor de cada requisito é concreto e dá para escrever o teste que o afirma. Se não dá, reescreva o requisito.
- Cada cenário dos Critérios de Aceitação do PRD aparece na Rastreabilidade com os IDs EARS que o cobrem: a presença já está na checagem de forma quando o PRD os lista em tabela; aqui, os IDs listados de fato cobrem o cenário.
- Requisito que vem do PRD cita o ID e não reescreve a regra.
- Nenhuma regra de negócio foi decidida por premissa nova na spec; premissa herdada do PRD, com origem anotada, não conta.
- Toda inferência está marcada.
- Se o Design vai precisar decidir comportamento, a spec ficou incompleta.

### Design

- Profundidade proporcional ao risco: a checagem de forma marca a seção acima de dez linhas de corpo; aqui você decide, para cada seção marcada, se o assunto dela aparece em Riscos e técnicas — se não aparece, é inflação e a seção encolhe. Risco sem técnica ou aceite é buraco.
- Critérios fixados e criticados antes das abordagens; a quarta pergunta (existe forma mais barata ou menos arriscada de fazer o mesmo?) respondida.
- Nenhum comportamento decidido aqui que devia estar na spec.
- Interfaces com tipos; a cobertura de todo `IF/THEN` da spec no tratamento de erros já está na checagem de forma.
- ADRs conformadas ou supersedidas (adr.md, Conformar e superseder).

### Tasks

- Cobertura requisito para task e task para requisito já está na checagem de forma; aqui: nenhuma task cita em `Requisito` um ID que ela não exercita.
- `Consome` e `Produz` consistentes entre as tasks e com o design, suficientes sem ler outra task; o executor também lê os requisitos citados e o trecho pertinente do design (tasks.md, Interfaces).
- `Tests` coerente com a camada da task, com teste co-locado.
- `Pronto quando` com critério de comportamento que a spec define; a checagem de forma já exige que o comando entre crases seja o do gate da task e que exista critério além dele; o conteúdo do critério é você quem confere.

### ADR

Quatro itens, os que a checagem de forma não alcança porque são conteúdo, não forma:

- A decisão fixa convenção, restrição ou padrão que features futuras seguem; decisão local à feature é ocorrência, e o destino dela é o design (adr.md, Quando a decisão é de projeto).
- Cada linha de Alternativas consideradas é uma alternativa realmente avaliada, derrubada contra os mesmos critérios que sustentam a decisão; alternativa escrita para encher a tabela é ocorrência.
- A linha `Negativas` nomeia o custo aceito desta decisão; risco genérico, que qualquer decisão teria, é ocorrência.
- Toda regra de projeto que a decisão cria ou altera está em Regras derivadas; o bullet e o path do arquivo já estão na checagem de forma (adr.md, Conformar e superseder), aqui: cada regra listada é mesmo criada ou alterada por esta decisão, e ADR que não cria regra não tem a seção.

### Execute

- Plano declarado antes do código.
- Testes da spec falhando antes da implementação.
- Implementação mínima.
- Gate verde.
- Tabela de evidência preenchida.
- Nenhuma lacuna resolvida em silêncio.
- Só os arquivos da task tocados.

### Verify

- Cobertura re-derivada com olhos frescos, com o grau de independência declarado no relatório.
- Toda linha de evidência com `file:line` e assertion.
- Lacuna de precisão reportada, nunca aprovada.
- Os dois eixos percorridos: conformidade à spec e aderência ao design.
- Gaps ordenados por severidade (verify.md, Relatório no chat) e convertidos em tasks de correção `TCn`.
