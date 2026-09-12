# Validação da SDD

## Scripts

Os scripts ficam em `scripts/`, no diretório desta skill; `<skill-dir>` é a pasta que contém `SKILL.md`, nunca a pasta `references/`, e rodam com `python3 <skill-dir>/scripts/<nome>.py` (ou `python`, onde `python3` não existir); rodar sem argumentos imprime a docstring completa. O `lint_mermaid.py` exige Node além do Python.

### Ciclo básico

1. Execute o linter no artefato gravado.
2. Resolva primeiro erro de uso ou bloqueio de ambiente pela tabela abaixo.
3. Separe HARD de forma mantidos por pedido/convenção dos demais HARD.
4. Se não restar HARD corrigível, encerre o ciclo básico.
5. Corrija os HARD corrigíveis e execute novamente: correção 1.
6. Se ainda houver HARD corrigível, corrija e execute: correção 2.
7. Se persistirem achados, apresente o artefato e relate cada um com o motivo, sem declarar validação completa.
8. Trate cada WARN: corrija ou registre uma linha de razão no chat, exceto `prd-rev` desatualizado.
9. Faça a revisão de conteúdo (Revisão por entrada) e aplique sua revalidação própria.

| Situação | Ação | Consome uma correção do ciclo básico? |
|---|---|---|
| HARD de forma explicitamente exigida pelo pedido ou comprovada pela convenção | Mantenha e relate qual HARD e qual origem o mantém, com "mantido por pedido" ou "mantido por convenção" | Não |
| Python/Node indisponível | Relate bloqueio de ambiente; apresente sem essa verificação e não afirme que validou | Não |
| Mermaid exit 3 por parser ausente | Peça autorização de `--setup` uma vez, antes de apresentar; autorizada, instale e repita o linter; recusada/sem resposta, apresente sem essa verificação | Não |
| Exit 2: arquivo ausente, opção desconhecida ou codificação fora de UTF-8 | Corrija a invocação como HARD; a execução inicial identifica o erro | Sim, quando há rodada de correção |
| WARN `prd-rev` desatualizado | Re-derive os requisitos afetados e atualize o hash (specify.md, Comentário de máquina) | Não pode ser dispensado como WARN comum |

Apresentação com achados remanescentes é permitida; não equivale a aprovação nem abre a próxima entrada sem os pré-requisitos (workflow.md, Aprovação e autorizações). O gate do Execute tem protocolo próprio: execução inicial e até duas tentativas de correção, total de três execuções antes de parar (execute.md, Ciclo por task).

### Forma mantida por pedido ou convenção

Pedido válido para manter um HARD nomeia literalmente a seção, o campo ou a forma de onde ele sai, por exemplo "inclua uma seção Plano de Rollout no design". Convenção válida é forma comprovada em pelo menos três artefatos commitados do mesmo tipo, ou escrita no AGENTS.md do repositório. Diga o número de exemplares no chat.

Para reconhecer uma convenção por exemplos, use a versão dos arquivos presente em HEAD. Liste os arquivos com `git ls-tree -r --name-only HEAD -- docs/specs` e filtre os Markdown do tipo em análise: `spec.md`, `design.md` ou `tasks.md`, separadamente. Leia cada exemplo com `git show "HEAD:<caminho>"`. A convenção precisa aparecer em pelo menos três desses exemplos. Um arquivo apenas staged ou untracked não conta. Uma alteração local em arquivo já commitado também não altera a convenção de HEAD. Se HEAD não existir, não há convenção comprovada por exemplos; a convenção escrita no guia do repositório continua sendo uma fonte válida. Para ADR, aplique o diretório e a seleção de (adr.md, Arquivo).

### Heurísticas de redação

Escreva de forma declarativa. `lint_spec.py`, `lint_design.py`, `lint_tasks.py` e `lint_adr.py` acusam hedging, meta-narração e placeholder como WARN, cada um no seu artefato. Tag fora de `[PREMISSA]` e `[LACUNA]` é HARD nos quatro. A revisão aplica (prose.md, Checklist editorial), sem novo linter de estilo.

Linter verde comprova o esqueleto; a revisão confere o conteúdo.

### Comandos

| Antes de | Comando |
|---|---|
| criar a pasta de uma mudança ou uma ADR | `seq.py next <dir> --slug <slug>`: imprime `NNNN-<slug>` com o próximo número da pasta; recusa alocar sobre número duplicado |
| apresentar qualquer artefato numerado | `seq.py check <dir>`: acusa número duplicado na pasta. Renumere o item cujo branch entra depois: mova-o para um nome sem o prefixo `NNNN-` (o `next` recusa alocar enquanto a duplicata existe), rode `seq.py next <dir> --slug <slug>`, mova-o para o nome devolvido e rode o check de novo |
| apresentar a spec | `lint_spec.py <spec.md>` |
| apresentar o design | `lint_design.py <design.md> --spec <spec.md>` |
| apresentar as tasks | `lint_tasks.py <tasks.md> --spec <spec.md>` |
| apresentar a ADR | `lint_adr.py <adr.md \| dir>` |
| apresentar qualquer artefato com diagrama Mermaid | `lint_mermaid.py <arquivo.md \| dir>`: faz o parse de todo bloco Mermaid. Bloco que não passou ou fence sem fechamento é HARD, porque diagrama não validado é diagrama não entregue. `--self-test` prova a extração e o parser; `--setup` instala o parser com `npm ci`, é o único modo com rede e só roda quando o usuário o autorizou na sessão |

## Revisão por entrada

Faça esta revisão antes de apresentar cada artefato, além de rodar o linter. Vale para todas as entradas: nenhuma seção existe só para cumprir a forma.

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

A revisão vem depois do ciclo básico do linter. Se alterou o artefato, rode o linter uma vez mais, fora do teto do ciclo básico; corrija HARD uma vez e execute para conferir. Se persistir, liste no chat. Essa execução extra não reabre indefinidamente a revisão. O checklist editorial (prose.md, Checklist editorial) concretiza a revisão existente, sem nota, seção ou ciclo adicional.

### Specify

- `SHALL` e ID único já são HARD de `lint_spec.py`, e padrão EARS é WARN dele; aqui: o padrão está correto, o valor de cada requisito é concreto e dá para escrever o teste que o afirma. Se não dá, reescreva o requisito.
- Cada cenário dos Critérios de Aceitação do PRD aparece na Rastreabilidade com os IDs EARS que o cobrem: a presença é HARD de `lint_spec.py` quando o PRD os lista em tabela; aqui, os IDs listados de fato cobrem o cenário.
- Requisito que vem do PRD cita o ID e não reescreve a regra.
- Nenhuma regra de negócio foi decidida por premissa nova na spec; premissa herdada do PRD, com origem anotada, não conta.
- Toda inferência está marcada.
- Se o Design vai precisar decidir comportamento, a spec ficou incompleta.

### Design

- Profundidade proporcional ao risco: as linhas de cada seção não se contam a olho, `lint_design.py` acusa como WARN a seção acima de dez linhas de corpo; aqui você decide, para cada seção acusada, se o assunto dela aparece em Riscos e técnicas — se não aparece, é inflação e a seção encolhe. Risco sem técnica ou aceite é buraco.
- Critérios fixados e criticados antes das abordagens; a quarta pergunta (existe forma mais barata ou menos arriscada de fazer o mesmo?) respondida.
- Nenhum comportamento decidido aqui que devia estar na spec.
- Interfaces com tipos; a cobertura de todo `IF/THEN` da spec no tratamento de erros já é HARD de `lint_design.py`.
- ADRs conformadas ou supersedidas (adr.md, Conformar e superseder).

### Tasks

- Cobertura requisito para task e task para requisito já é HARD de `lint_tasks.py`; aqui: nenhuma task cita em `Requisito` um ID que ela não exercita.
- `Consome` e `Produz` consistentes entre as tasks e com o design, suficientes sem ler outra task; o executor também lê os requisitos citados e o trecho pertinente do design (tasks.md, Interfaces).
- `Tests` coerente com a camada da task, com teste co-locado.
- `Pronto quando` com critério de comportamento que a spec define; `lint_tasks.py` já exige que o comando entre crases seja o do gate da task e que exista critério além dele, o conteúdo do critério é você quem confere.

### ADR

Quatro itens, os que `lint_adr.py` não alcança porque são conteúdo, não forma:

- A decisão fixa convenção, restrição ou padrão que features futuras seguem; decisão local à feature é ocorrência, e o destino dela é o design (adr.md, Quando a decisão é de projeto).
- Cada linha de Alternativas consideradas é uma alternativa realmente avaliada, derrubada contra os mesmos critérios que sustentam a decisão; alternativa escrita para encher a tabela é ocorrência.
- A linha `Negativas` nomeia o custo aceito desta decisão; risco genérico, que qualquer decisão teria, é ocorrência.
- Toda regra de projeto que a decisão cria ou altera está em Regras derivadas; o bullet e o path do arquivo já são HARD de `lint_adr.py` (adr.md, Conformar e superseder), aqui: cada regra listada é mesmo criada ou alterada por esta decisão, e ADR que não cria regra não tem a seção.

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
