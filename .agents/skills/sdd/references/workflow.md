# Workflow da SDD

## Abrir uma mudança

### Quanto artefato a mudança pede

Duas perguntas decidem quais artefatos a mudança pede, além da spec:

1. Há decisão de deploy, de estilo arquitetural ou de biblioteca compartilhada (design.md, Unidade de deploy e reuso); arquivo novo numa camada com menos de três arquivos rastreados do mesmo tipo, contados antes de decidir com `git ls-files '<glob da camada>'` — sem três exemplares não há convenção a copiar (design.md, Base de código); interação entre três ou mais componentes a planejar; ou risco de integração, dinheiro, regulação, contrato público, migração ou preocupação encontrada na base (as fontes de design.md, Do risco à técnica, fora as dimensões implícitas, que já viraram requisito)? Se sim, a mudança pede `design.md`.
2. Há mais de cinco passos, ou algum passo depende de outro que não é o imediatamente anterior? Se sim, a mudança pede `tasks.md`.

**Catraca.** Se a mudança revelar um gatilho de design ou tasks, interrompa somente o trabalho que depende do artefato ausente, apresente a descoberta e produza esse artefato respeitando os pré-requisitos. O nível já exigido não é reduzido.

Numa implementação autorizada, Specify e Execute nunca são pulados: sempre se sabe *o quê* antes de fazer. Quando não há `tasks.md`, o Execute começa por um plano inline (execute.md, Plano inline).

### Entradas e pré-requisitos

| Entrada | Pré-requisito | Referência |
|---|---|---|
| Specify | PRD, pedido com usuário-alvo e problema (specify.md, Origem) ou código a documentar | [specify.md](specify.md) |
| Design | spec commitada | [design.md](design.md) |
| Tasks | design commitado, ou spec quando o Design foi dispensado | [tasks.md](tasks.md) |
| Execute | tasks commitadas, ou plano inline aprovado | [execute.md](execute.md) |
| Verify | última task fechada | [verify.md](verify.md) |
| ADR | decisão que fixa convenção para features futuras | [adr.md](adr.md) |

Para uma entrada nova, leia a referência inteira e suas dependências normativas. Para correção localizada, leia o trecho afetado, seus pré-requisitos, exceções e citadores; amplie a leitura quando surgir dependência. O layout de arquivos e os comentários de máquina estão definidos na referência de Specify (specify.md, Layout).

## Aprovação e autorizações

**Aprovação é o commit.** Árvore suja é trabalho em elaboração; a entrada seguinte usa a versão aprovada e commitada. Apresente cada artefato e espere a aprovação de seu conteúdo antes de começar o seguinte. Um commit feito pelo próprio usuário do artefato apresentado também satisfaz essa aprovação.

Autorização para editar permite produzir o resultado solicitado. Autorização para commitar permite a operação local de Git durante a mudança: "commita", dito uma vez, autoriza os commits locais dela, um por artefato e um por task. Essa autorização não elimina a apresentação e a aprovação exigidas para o conteúdo de cada artefato. Push, deploy e outros efeitos externos continuam exigindo autorização própria.

| Situação observada | Pode fazer | Deve parar onde |
|---|---|---|
| Pedido só de spec/design/tasks | Produzir o artefato pedido, respeitando pré-requisitos | Antes de implementar ou de começar uma entrada não autorizada |
| Conteúdo aprovado no chat e commit já autorizado para a mudança | Commit local do artefato aprovado e avanço permitido | Na próxima aprovação exigida |
| Conteúdo aprovado no chat, sem autorização de commit | Pedir uma vez que o usuário commite ou autorize o commit | Antes da entrada que exige o artefato commitado |
| “Commita” dado antes do próximo artefato existir | Guardar a autorização da operação local | Ainda apresentar e obter aprovação do novo conteúdo |
| Plano inline aprovado no chat | Iniciar Execute conforme o plano (execute.md, Plano inline) | Nos bloqueios e limites de escopo já definidos |
| Silêncio | Continuar apenas trabalho independente já autorizado | Não tratar como aprovação |

O plano inline é a exceção à aprovação por commit: vive no chat e é aprovado no chat. Delegação explícita de escolhas técnicas continua valendo; não delega decisões de negócio nem efeitos externos. Não grave campos de aprovação nos artefatos.

Dentro do escopo autorizado, conclua as edições, as verificações exigidas e as correções permitidas pelos tetos da entrada. Não peça uma nova aprovação para leitura, inspeção ou teste local já autorizado. Se uma decisão bloquear parte do trabalho, conclua primeiro o que for independente dela. Ao relatar o bloqueio, identifique a ação bloqueada e a regra local que exige a decisão. A apresentação de um rascunho não encerra uma implementação autorizada que ainda requer verificação.

Essa autorização para teste local exige comando e isolamento comprovados na configuração do projeto. Não afirme que testes não acessam produção sem verificar. Instalação, acesso externo, commit, push e deploy continuam sujeitos às autorizações já definidas. A precedência local opera dentro dos controles de segurança e permissões do ambiente.

## Tags e dúvidas

- **Tags.** `[PREMISSA]` marca inferência com default e racional; `[LACUNA]` marca informação insuficiente para decidir. Texto sem tag é fato, com origem no PRD, no usuário, no código ou na documentação. Aprovação não converte premissa em fato.
- **Fatos você procura; decisões você pergunta.** A cadeia de pesquisa para um fato, nesta ordem: base de código, docs do projeto, documentação oficial, web; se nada responder, sinalize a incerteza. Nunca fabrique API, padrão ou comportamento; "não encontrei" é resposta válida.

Toda dúvida cai em uma de três categorias:

| Condição | Ação | Bloqueio |
|---|---|---|
| 1. Decisão dentro da autonomia delegada por escrito no pedido da sessão ou no AGENTS.md | Decida, registre e siga | Só a apresentação de cada artefato espera |
| 2. Inferência de solution space sem delegação escrita | Marque `[PREMISSA]` com default e racional e avance; a premissa fica revisável | Pergunte nas exceções de Clarify e Design abaixo |
| 3. Decisão material do usuário: escopo, regra de negócio, trade-off ou efeito externo | Pergunte; sem resposta, não adote default | Bloqueie somente o que depende da resposta |

Sem delegação escrita, escolha de negócio é categoria 3 e escolha de solution space é categoria 2. Nesta última, pergunte no Clarify quando a resposta muda arquitetura, modelo de dados, decomposição, desenho de teste ou aceitação (specify.md, Clarify), e no Design sobre critérios e abordagem (design.md, Critérios antes das abordagens). Com delegação escrita para o solution space, essas duas exceções caem e só a apresentação de cada artefato espera.

- **Refine o contexto, não o erro.** Artefato downstream errado (teste que não deveria passar, código que contradiz o design, task impossível) não se remenda: corrija o artefato upstream que carregava a causa e re-derive o downstream. Regra de negócio errada volta ao PRD.
- **Precedência**, do que prevalece para o que cede:
  1. Pedido da sessão.
  2. Convenção do repositório.
  3. Defaults desta skill.

  A lista fechada de seções de cada artefato é default desta skill, degrau 3: HARD que decorre de um dos dois primeiros degraus é mantido, não corrigido (validation.md, Scripts).

## Idioma e redação

### Idioma

- **O artefato é escrito em português ou em inglês, nunca em outro idioma.** Os quatro linters casam os headings por igualdade com os aliases PT/EN da lista de seções do artefato, e cada lista traz os dois nomes: spec (specify.md, Seções), design (design.md, Seções), tasks (tasks.md, Seções do `tasks.md`) e ADR (adr.md, Template). Seção fora da lista é HARD em `lint_design.py`, `lint_tasks.py` e `lint_adr.py`; em `lint_spec.py` é WARN, porque spec real pode carregar seção herdada do PRD. Artefato em terceiro idioma sai com um achado por seção — HARD nos três, WARN na spec — e sem correção possível.
- Qual dos dois: o idioma do PRD; sem PRD, o do material recebido (com material em mais de um idioma, o do documento que o pedido cita primeiro ou, sem citação, o do primeiro anexo); sem os dois, o do pedido; se o pedido mistura idiomas, português.
- Quando o idioma que essa regra devolve não é português nem inglês, o artefato fica em inglês e a apresentação diz, em uma linha, qual era o idioma do material e que o artefato saiu em inglês por isso.
- Termo canônico com tradução de mesma força se traduz: Requisitos, Fora de Escopo, Perguntas em Aberto, Dado/Quando/Então.
- Termo sem tradução de mesma força fica em inglês: domain event, outbox, idempotency key, retry, circuit breaker, aggregate, value object, port/adapter, trade-off, gate.
- Keywords EARS, IDs, código, paths, slugs e identificadores não se traduzem.
- Termo que o time usa em português (AGENTS.md, glossário do PRD ou código) fica em português mesmo que esteja na lista acima: é a precedência de Tags e dúvidas.

### Redação

Aplique as [Convenções de escrita](prose.md#convenções-de-escrita). As heurísticas de redação e as tags que os linters verificam estão em (validation.md, Scripts).
