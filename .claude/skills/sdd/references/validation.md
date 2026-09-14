# Validação dos artefatos SDD

Verifique a forma e o conteúdo pertinentes ao artefato entregue. Não há verificador completo de SDD nesta skill; os checks abaixo exigem leitura, salvo os contratos que os scripts do repositório verificarem explicitamente.

Corrija problemas concretos dentro do escopo. Repita os checks afetados quando o conteúdo mudar. Continue enquanto houver progresso fundamentado; relate dependências que impeçam a correção. Não use pontuações de clareza nem limite fixo de rodadas.

## Regras comuns

- Destinos, comentários de máquina e caminhos seguem [specify.md](specify.md).
- Numeração única por pasta; IDs não são reutilizados.
- Seções e rótulos respeitam o contrato do artefato, com prosa em português.
- Links resolvem; tags de incerteza são `[ASSUMPTION]` e `[GAP]`.
- Exemplos e placeholders instrucionais não entram como fatos no documento entregue.
- Uma forma exigida pelo pedido ou pela convenção escrita pode prevalecer; cite a origem e relate eventual divergência do verificador.
- Incerteza explícita é informação. Diferencie-a de qualificadores vagos sem conteúdo.

## Spec

Confira comentário, título, linha `Requirement prefix:`, `Context` e `Requirements`, sem duplicações. Cada requisito usa ID único, prefixo declarado, um padrão EARS e resultado observável. A linha `Retired:` explica IDs aposentados e saltos.

Com PRD, confira arquivo, `prd-rev` contra seu hash atual e prefixo técnico distinto. IDs citados resolvem; `Traceability` cobre requisitos e cenários em escopo nos dois sentidos. Itens sem EARS têm justificativa `Design criterion:` ou `Outside this capability:`.

Revise se o requisito realiza o comportamento de negócio sem redefini-lo, se hipóteses herdadas preservam origem e se alguma decisão de negócio foi inventada. A spec deve permitir derivar testes; “rápido” sem critério não basta.

## Design

Confira comentário, destino da spec e IDs de `scope:`. Títulos e ordem seguem [design.md](design.md).

Com `Approaches`, as alternativas são reais e comparáveis. Sem a seção, `Evaluation Criteria` termina com `No real alternative:` e razão.

Cada requisito `IF ... THEN` em escopo aparece em `Error Handling`. Componentes declaram propósito, localização, interfaces, dependências e reuso. Diagramas precisam de sintaxe e representação coerentes.

Revise critérios e origem, riscos mitigados ou aceitos, custos, alternativas mais simples e conformidade aos ADRs. A extensão do texto deve servir à decisão; contagem de linhas não mede qualidade.

## Tasks

Confira comentário, spec, design opcional, escopo e descrição das verificações do projeto. As seções `Gate Commands`, `Execution Plan`, `Tasks` e `Traceability` são obrigatórias.

Na tabela de gates, nomes permitidos: `quick`, `full`, `build` e `Mutation`. Comandos são preenchidos; todo gate usado possui linha. `Mutation` aparece quando adotado pelo plano ou exigido pelo usuário.

Cada `Tn` ou `TCn` tem ID único e os campos What, Where, Depends on, Requirement, Interfaces, Done when, Tests e Gate, preenchidos uma vez. `Done when` contém o comando exato do gate e critérios observáveis. `Tests: none` exige justificativa e outra evidência apropriada.

Confira ordem das dependências, ausência de ciclos, correspondência com o plano e rastreabilidade nos dois sentidos. A última tarefa de uma fase não exige gate mais amplo por posição. A conclusão da implementação inclui os checks finais do projeto.

Revise a coesão da entrega, contratos consumidos e produzidos, testes pertinentes e resultados esperados. Referências vagas a outras tarefas não substituem contratos.

## ADR

Confira título `ADR NNNN:`, participantes, seções e ordem de [adr.md](adr.md). `Consequences` inclui `Negative:` com custo concreto. Alternativas correspondem a escolhas avaliadas ou à explicação de inexistência de alternativa viável.

Em `Derived rules`, cada regra tem caminho. `Supersedes:` e `Superseded by:` resolvem e são recíprocos.

Revise se a decisão estabelece regra de projeto, se as razões sobrevivem ao código e se participantes, benefícios e custos têm fonte.

## Execução e verificação

Use [execute.md](execute.md) e [verify.md](verify.md) para evidência de comportamento, checks finais, escopo e correções. Confirme que:

- O plano precede a implementação.
- Testes exercitam critérios reais.
- A versão examinada está identificada, inclusive quando sem commit.
- Spec e design têm evidências e ressalvas explícitas.
- Falhas de ambiente não são confundidas com defeitos.
- Um check não realizado não é apresentado como aprovado.

Aplique [prose.md](prose.md) durante a mesma revisão. Validade de formato não demonstra eficiência do modelo.
