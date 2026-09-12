# Processo de escrita e validação

## Workflow

1. **Entender.** Avalie o escopo, a riqueza do contexto, o material de discovery e a necessidade de pesquisa conforme intake.md; é lá que estão o teto de perguntas e o que fazer quando o usuário recusa discovery.
2. **Escrever.** Aplique o que está em writing.md: capability test, lente DDD, uma regra, um lugar, IDs, PRD 0000, diagramas, seções e redação. Grave o arquivo conforme (conventions.md, Gravar).
3. **Checar.** Faça a checagem de forma abaixo antes de apresentar.

### Checar

Leia o PRD gravado e confira cada item da lista abaixo. Todo achado se corrige antes de apresentar, com uma nova leitura do trecho corrigido; achado de forma exigido pelo pedido ou comprovado pela convenção fica como está e é informado no chat com a fonte, usando "mantido por pedido" ou "mantido por convenção". Achado que você não conseguiu corrigir é relatado ao apresentar, sem declarar validação completa. Depois da checagem, faça a revisão de cinco itens (workflow.md, Revisão antes de apresentar).

1. **Numeração.** O número do arquivo é único na pasta: liste os `NNNN-*.md` sob `/docs/prd` e confira que nenhum outro usa o mesmo número (conventions.md, Caminho e numeração).
2. **Header.** Título `#`, tabela de um campo com um dos rótulos aceitos, linha de prefixo na forma fixada e, quando existe PRD 0000, a frase que o aponta (conventions.md, Header).
3. **Seções.** As obrigatórias presentes; nenhuma `##` fora da tabela de Seções; ordem da tabela; nenhuma seção vazia ou reduzida a "Nenhuma.", "N/A" ou equivalente (writing.md, Seções).
4. **IDs.** Todo FR com prioridade MoSCoW e com o prefixo declarado; NFR sem MoSCoW; nenhum ID definido duas vezes; toda citação de ID resolve para uma definição em algum PRD da pasta; nenhum `FR-nn` ou `NFR-nn` sem prefixo (writing.md, IDs).
5. **Formas por seção.** Trade-offs Declarados com *Custo* e *Razão* em cada bullet, de até duas linhas; Métricas de Sucesso com guardrail; premissa "se falsa" só como primeiro bullet, em negrito, de Perguntas em Aberto; Ponto de Maior Fragilidade seguido só de Referências; cenário Dado/Quando/Então citando ID; bullet de Considerações Regulatórias apontando ID, com nota de até 20 palavras; contexto listado em `; afeta` com linha em Dependências e Riscos (writing.md, Seções).
6. **Links.** Todo link Markdown para arquivo local resolve, relativo à pasta do PRD ou a partir da raiz do repositório.
7. **PRD 0000.** `<!-- prd: overview -->` na primeira linha, número 0000, sem requisito definido; com dois ou mais prefixos na pasta ele existe; cada PRD comum o referencia por link na linha de prefixo (writing.md, PRD 0000).
8. **Diagramas.** Cada bloco Mermaid lido linha a linha: fence fechado, tipo de diagrama declarado, sintaxe que renderiza, nenhuma palavra reservada como alias, rótulo citando ID e, no `stateDiagram-v2`, a tabela com coluna Identificador ao lado (writing.md, Diagramas).
9. **Tags e placeholders.** Só `[PREMISSA]` e `[LACUNA]` entre colchetes; nenhum TBD, TODO ou `[nome]`; nenhum parágrafo de prosa repetido de outro PRD da pasta.
10. **Síntese do material.** Com material de discovery em texto, as três frases mais longas do PRD não aparecem literalmente nele (intake.md, Material de discovery).

Pedido válido para manter um achado é o da sessão que nomeia literalmente a seção, o campo ou a forma que o provoca, como "inclua uma seção Plano de Rollout". A precedência é definida na raiz (SKILL.md, Precedência). Convenção se comprova pela regra seguinte.

### Convenção em HEAD

Para reconhecer uma convenção por exemplos, use a versão dos arquivos presente em HEAD. Liste os arquivos com `git ls-tree -r --name-only HEAD -- docs/prd` e filtre os Markdown do tipo de PRD em análise. Leia cada exemplo com `git show "HEAD:<caminho>"`. A convenção precisa aparecer em pelo menos três desses exemplos. Um arquivo apenas staged ou untracked não conta. Uma alteração local em arquivo já commitado também não altera a convenção de HEAD. Se HEAD não existir, não há convenção comprovada por exemplos; a convenção escrita no guia do repositório (AGENTS.md) continua sendo uma fonte válida.

### Revalidação após a revisão

Se a revisão de conteúdo alterou o PRD, repita a checagem de forma sobre os trechos alterados. Corrija o que encontrar uma vez; se persistir, liste no chat com os motivos. Esta revalidação não reabre a revisão. Apresentar um artefato com achados remanescentes não comprova aprovação.

## Revisão antes de apresentar

Depois da checagem de forma, avalie cada um dos cinco itens abaixo em todas as seções do PRD. A nota por item é `max(0, 100 - 20 × ocorrências)`.

| Ocorrências | Nota | Ação |
|---|---|---|
| 0 | 100 | Item passa |
| 1 | 80 | Corrigir o item |
| 2 | 60 | Corrigir o item |
| 3 | 40 | Corrigir o item |
| 4 | 20 | Corrigir o item |
| 5 ou mais | 0 | Corrigir o item |

Item abaixo de 90 é corrigido; item com 90 ou mais fica como está. Depois da correção, repontue somente esse item: são no máximo duas passadas por item. Se a segunda ainda terminar abaixo de 90, apresente o PRD e diga no chat o item, a nota e o que falta. Aplique o checklist editorial na mesma revisão (prose.md, Checklist editorial), sem criar nota ou ciclo adicional.

1. **Capability test.** A Solução Proposta, a frase de solução do Resumo Executivo e cada FR descrevem comportamento observável, não mecanismo (writing.md, Capability test); em reverse PRD o alcance é outro, e quem o fixa é uma fonte só (modes.md, Modo reverse PRD). Cada nome de mecanismo (tecnologia, componente, padrão de implementação) na Solução Proposta, na frase de solução do Resumo Executivo ou num FR é uma ocorrência; no reverse PRD, em qualquer seção. Termo que o pedido ou o material fixa como parte do produto, com uma linha de razão no chat, não é ocorrência.
2. **Uma regra, um lugar.** Cada regra existe em um único FR e o resto cita o ID. Paráfrase que diverge do FR não se resolve aqui: vira `[LACUNA]` em Perguntas em Aberto (writing.md, Uma regra, um lugar).
3. **Tags.** Toda inferência está marcada `[PREMISSA]` ou `[LACUNA]`; discovery sintetizado tem a origem marcada (intake.md, Material de discovery).
4. **Forma.** Nenhuma seção existe só para cumprir forma (writing.md, Seções). O que é forma verificável já foi conferido na checagem de forma (workflow.md, Checar), inclusive a seção `##` fora da tabela; aqui sobram os dois que só a leitura de conteúdo pega:
   - bullet inserido para completar contagem, isto é, bullet cuja remoção não tira informação nenhuma do PRD; bullet que uma regra de writing.md exige, como o guardrail de Métricas de Sucesso marcado `[PREMISSA]` (writing.md, Seções), nunca é ocorrência;
   - Ponto de Maior Fragilidade sem decisão de julgamento sobre fatos conhecidos (corte de escopo, threshold, priorização ou usuário-alvo), isto é, cosmético.
5. **Idioma e headings.** Seguem a precedência; há um conceito por parágrafo (writing.md, Redação). Ocorrência: heading fora do par PT/EN do idioma fixado, parágrafo com dois assuntos, ou dois parágrafos adjacentes sobre o mesmo ponto. Heading mantido por pedido ou convenção no passo Checar não é ocorrência aqui, porque a razão já o fechou.

## Apresentar e iterar

Ao apresentar o PRD:

1. Informe o caminho do arquivo.
2. Aponte o Ponto de Maior Fragilidade, quando a seção existir.
3. Apresente todas as perguntas que efetivamente entraram em Perguntas em Aberto (writing.md, Seções).
4. Acrescente, somente quando aplicável: usuário-alvo ainda não identificado e sinais faltantes após recusa de discovery (intake.md, Casos de borda); busca não realizada (intake.md, Pesquisa).
5. Relate os achados de forma mantidos ou não corrigidos (workflow.md, Checar).

Não invente fragilidade, pergunta ou seção para preencher esta apresentação.

- Mudança pedida pelo usuário que toca duas ou mais seções, ou que altera Contexto e Problema ou Solução Proposta, regenera o PRD inteiro, porque a consistência entre seções é o que se perde no ajuste pontual. Mudança localizada (um FR, um threshold, uma frase, uma `[LACUNA]`) é ajuste pontual. Regeneração ou ajuste pedido pelo usuário reinicia o passo Checar.
- Antes de alterar ou remover um FR, liste quem cita os IDs tocados (writing.md, IDs).
