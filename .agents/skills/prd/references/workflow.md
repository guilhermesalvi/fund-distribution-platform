# Processo de escrita e validação

## Workflow

1. **Entender.** Avalie o escopo, a riqueza do contexto, o material de discovery e a necessidade de pesquisa conforme intake.md; é lá que estão o teto de perguntas e o que fazer quando o usuário recusa discovery.
2. **Escrever.** Aplique o que está em writing.md: capability test, lente DDD, uma regra, um lugar, IDs, PRD 0000, diagramas, seções e redação. Grave o arquivo conforme (conventions.md, Gravar).
3. **Checar.** Siga o ciclo e as exceções abaixo antes de apresentar.

### Checar

1. Execute os scripts da tabela de Scripts no artefato gravado.
2. Resolva primeiro erro de uso ou bloqueio de ambiente pela tabela de exceções.
3. Separe os HARD de forma mantidos por pedido ou convenção dos demais HARD.
4. Se não restar HARD corrigível, encerre o ciclo básico e siga para os WARN e a revisão.
5. Corrija os HARD corrigíveis e execute novamente: correção 1.
6. Se ainda houver HARD corrigível, corrija e execute novamente: correção 2.
7. Se persistirem achados após a segunda correção, apresente o PRD e relate cada HARD com o motivo, sem declarar validação completa.
8. Trate cada WARN: corrija ou mantenha com uma linha de razão no chat.
9. Faça a revisão de cinco itens (workflow.md, Revisão antes de apresentar) e aplique sua revalidação quando o texto mudar.

| Situação | Ação | Consome correção do ciclo básico? |
|---|---|---|
| HARD de forma exigida pelo pedido ou comprovada pela convenção | Mantenha e informe o HARD e a fonte, usando "mantido por pedido" ou "mantido por convenção" | Não |
| Python ou Node indisponível | Relate bloqueio de ambiente e apresente sem essa verificação | Não |
| Mermaid exit 3: parser ausente | Peça autorização de `--setup` uma vez antes de apresentar; autorizada, instale e repita o linter; recusada ou sem resposta, apresente sem essa verificação | Não |
| Exit 2: caminho, opção ou nome de arquivo inválido | Corrija a invocação; a execução inicial identifica o erro e cada rodada de correção usa o teto de duas | Sim, quando há rodada de correção |
| `seq.py` exit 1: slug inválido ou número duplicado | Corrija como HARD | Sim |

Pedido válido para manter um HARD é o da sessão que nomeia literalmente a seção, o campo ou a forma que o provoca, como "inclua uma seção Plano de Rollout". A precedência é definida na raiz (SKILL.md, Precedência). Convenção se comprova pela regra seguinte.

### Convenção em HEAD

Para reconhecer uma convenção por exemplos, use a versão dos arquivos presente em HEAD. Liste os arquivos com `git ls-tree -r --name-only HEAD -- docs/prd` e filtre os Markdown do tipo de PRD em análise. Leia cada exemplo com `git show "HEAD:<caminho>"`. A convenção precisa aparecer em pelo menos três desses exemplos. Um arquivo apenas staged ou untracked não conta. Uma alteração local em arquivo já commitado também não altera a convenção de HEAD. Se HEAD não existir, não há convenção comprovada por exemplos; a convenção escrita no guia do repositório (AGENTS.md) continua sendo uma fonte válida.

### Revalidação após a revisão

Se a revisão de conteúdo alterou o PRD, execute os scripts uma vez mais, fora do teto do ciclo básico. Corrija os HARD dessa execução uma vez; se persistirem, liste-os no chat com os motivos. Esta revalidação não reabre a revisão nem reinicia o ciclo básico. Apresentar um artefato com achados remanescentes não comprova aprovação.

## Revisão antes de apresentar

Depois do linter, avalie cada um dos cinco itens abaixo em todas as seções do PRD. A nota por item é `max(0, 100 - 20 × ocorrências)`.

| Ocorrências | Nota | Ação |
|---|---|---|
| 0 | 100 | Item passa |
| 1 | 80 | Corrigir o item |
| 2 | 60 | Corrigir o item |
| 3 | 40 | Corrigir o item |
| 4 | 20 | Corrigir o item |
| 5 ou mais | 0 | Corrigir o item |

Item abaixo de 90 é corrigido; item com 90 ou mais fica como está. Depois da correção, repontue somente esse item: são no máximo duas passadas por item. Se a segunda ainda terminar abaixo de 90, apresente o PRD e diga no chat o item, a nota e o que falta. Aplique o checklist editorial na mesma revisão (prose.md, Checklist editorial), sem criar nota ou ciclo adicional.

1. **Capability test.** A Solução Proposta, a frase de solução do Resumo Executivo e cada FR descrevem comportamento observável, não mecanismo (writing.md, Capability test); em reverse PRD o alcance é outro, e quem o fixa é uma fonte só (modes.md, Modo reverse PRD). Os termos de mecanismo da lista do script não se contam a olho: `lint_prd.py`, na forma da tabela de Scripts, acusa cada um como WARN em Solução Proposta e Requisitos Funcionais, e no alcance alargado quando roda com `--reverse`; termo cujo WARN você manteve com uma linha de razão no passo Checar (Workflow) não é ocorrência aqui. A leitura cobre o que a lista do script não tem e a frase de solução do Resumo Executivo.
2. **Uma regra, um lugar.** Cada regra existe em um único FR e o resto cita o ID. Paráfrase que diverge do FR não se resolve aqui: vira `[LACUNA]` em Perguntas em Aberto (writing.md, Uma regra, um lugar).
3. **Tags.** Toda inferência está marcada `[PREMISSA]` ou `[LACUNA]`; discovery sintetizado tem a origem marcada (intake.md, Material de discovery).
4. **Forma.** Nenhuma seção existe só para cumprir forma (writing.md, Seções). O que é forma verificável já é HARD ou WARN de `lint_prd.py` (docstring) — inclusive a seção `##` fora da tabela, que é HARD, então o conjunto de headings também não se confere a olho; aqui sobram os dois que só a leitura pega:
   - bullet inserido para completar contagem, isto é, bullet cuja remoção não tira informação nenhuma do PRD; bullet que uma regra de writing.md exige, como o guardrail de Métricas de Sucesso marcado `[PREMISSA]` (writing.md, Seções), nunca é ocorrência;
   - Ponto de Maior Fragilidade sem decisão de julgamento sobre fatos conhecidos (corte de escopo, threshold, priorização ou usuário-alvo), isto é, cosmético.
5. **Idioma e headings.** Seguem a precedência; há um conceito por parágrafo (writing.md, Redação). Ocorrência: heading fora do par PT/EN do idioma fixado, parágrafo com dois assuntos, ou dois parágrafos adjacentes sobre o mesmo ponto. Os headings não se contam a olho: `lint_prd.py --lang`, na forma da tabela de Scripts, acusa cada um como WARN; heading cujo WARN você manteve com uma linha de razão no passo Checar (Workflow) não é ocorrência aqui, porque a razão já o fechou. A leitura cobre só os dois casos de parágrafo.

## Apresentar e iterar

Ao apresentar o PRD:

1. Informe o caminho do arquivo.
2. Aponte o Ponto de Maior Fragilidade, quando a seção existir.
3. Apresente todas as perguntas que efetivamente entraram em Perguntas em Aberto (writing.md, Seções).
4. Acrescente, somente quando aplicável: usuário-alvo ainda não identificado e sinais faltantes após recusa de discovery (intake.md, Casos de borda); busca não realizada (intake.md, Pesquisa).
5. Relate os achados de validação pendentes (workflow.md, Checar).

Não invente fragilidade, pergunta ou seção para preencher esta apresentação.

- Mudança pedida pelo usuário que toca duas ou mais seções, ou que altera Contexto e Problema ou Solução Proposta, regenera o PRD inteiro, porque a consistência entre seções é o que se perde no ajuste pontual. Mudança localizada (um FR, um threshold, uma frase, uma `[LACUNA]`) é ajuste pontual. Regeneração ou ajuste pedido pelo usuário reinicia o passo Checar com os tetos zerados.
- Antes de alterar ou remover um FR, liste quem cita os IDs tocados (writing.md, IDs).

## Scripts

- Os scripts ficam na pasta `scripts/` do diretório desta skill e são chamados pelo caminho completo, `python <skill-dir>/scripts/<nome>.py` (ou `python3`, onde `python` não existir), de qualquer diretório de trabalho. `<skill-dir>` é o diretório que contém `SKILL.md`; nunca a pasta `references/`. O parser Mermaid exige Node.
- `/docs/prd` nos exemplos é caminho relativo à raiz do repositório; passe o caminho real.
- A docstring completa de cada script sai ao rodá-lo sem argumentos.
- O ciclo de correção, o teto e as exceções estão no passo Checar (Workflow). `WARN` é heurística com risco de falso-positivo.
- Linter verde comprova a forma; a revisão de conteúdo continua obrigatória.
- Hedging lexical e meta-narração são heurísticas WARN de `lint_prd.py`; a lista é a do script, sem segunda lista editorial. A ausência de WARN não comprova qualidade da escrita.

| Comando | Quando | O que faz |
|---|---|---|
| `python <skill-dir>/scripts/seq.py next /docs/prd --slug <domain-slug>-<feature-slug>` | Antes de criar o arquivo | Imprime `NNNN-<slug>` com o próximo número; recusa alocar quando há número duplicado |
| `python <skill-dir>/scripts/seq.py check /docs/prd` | Antes de apresentar | Acusa número duplicado; a rota de renumeração está em uma fonte só (conventions.md, Caminho e numeração) |
| `python <skill-dir>/scripts/lint_prd.py <arquivo.md \| /docs/prd> --lang <pt\|en> [--source <material>] [--reverse]` | Antes de apresentar | Forma das seções e do header, IDs, links, PRD 0000 e heurísticas de redação; a lista completa de HARD e WARN é a docstring do script (rode-o sem argumentos) e não é repetida aqui. `--lang` é sempre o idioma fixado do PRD, `pt` ou `en` (conventions.md, Idioma). `--source` entra uma vez por arquivo de material de discovery em texto no disco, e acusa reformatação (intake.md, Material de discovery). `--reverse` é a opção do modo reverse PRD: quando ela entra e o que ela estende estão em uma fonte só (modes.md, Modo reverse PRD) |
| `python <skill-dir>/scripts/lint_mermaid.py <arquivo.md \| dir>` | Antes de apresentar PRD com diagrama | Faz o parse de todo bloco Mermaid. Bloco que não passou ou fence sem fechamento é HARD, porque diagrama não validado é diagrama não entregue; parser indisponível (exit 3) é bloqueio de ambiente e segue o passo Checar (Workflow). `--self-test` prova a extração e o parser; `--setup` instala o parser com `npm ci`, é o único modo com rede e só roda quando o usuário o autorizou na sessão, na ordem fixada em Checar |
