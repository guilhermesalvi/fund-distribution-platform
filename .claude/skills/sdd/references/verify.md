# Verificação

Reúna evidência de conformidade à spec e aderência ao design. Um pedido de verificação parcial também é válido: delimite os requisitos e não declare conclusão do restante.

## Independência e versão

Releia requisitos e testes sem partir da conclusão do autor. Use revisão independente por subagente quando a complexidade ou o risco justificar e a delegação estiver disponível e autorizada. Caso contrário, faça uma nova passagem própria e informe seu grau de independência. Disponibilidade da ferramenta não cria obrigação de delegar.

Identifique a spec atual por caminho e hash de conteúdo. Ela pode estar modificada ou ainda não rastreada. Inclua staged, unstaged e novos arquivos pertinentes no exame. Se o conteúdo mudar durante a verificação, renove a evidência afetada. Não verifique uma versão antiga para evitar a análise da atual.

## Escopo e base

A base preferencial é o `Base:` registrado antes da implementação. Na ausência, use uma base de branch ou começo de mudança demonstrável pelo histórico e relate como foi obtida. O último commit da spec não é automaticamente a base da implementação.

Sem base recuperável, verifique o estado atual e declare a comparação histórica indisponível. Não atribua causalidade a falhas nem invente um hash. Alterações alheias ao escopo ficam preservadas; não use stash, restauração ou limpeza da árvore do usuário para verificar.

## Conformidade à spec

Para cada requisito em escopo, apresente resultado esperado, `arquivo:linha`, asserção ou outra evidência adequada e um resultado: `covered`, `gap` ou `precision gap`.

- A evidência deve testar o resultado definido; uma asserção qualquer não basta.
- Antes de declarar ausência, procure o ID e os identificadores de erro, estado ou evento nos testes pertinentes.
- Falta de precisão na spec é `precision gap`, não cobertura.
- Cenários de aceitação do PRD em escopo precisam de evidência.
- Requisito aposentado exige conferir a remoção do comportamento e a justificativa dos testes alterados.

Uma tabela de evidências pode agrupar cenários equivalentes, desde que cada obrigação permaneça localizável.

## Checks e falhas

Execute ou confirme evidência vigente dos checks finais do projeto, conforme [execute.md](execute.md). Informe comandos, saída, aprovados, falhos e ignorados quando aplicável. Não repita um check aprovado para a mesma versão sem motivo.

Queda na contagem de testes é sinal a investigar. Consolidação de casos, parametrização ou aposentadoria pode justificá-la se a cobertura de comportamento for preservada ou sua mudança estiver autorizada. Testes ignorados não demonstram comportamento. Uma suíte que deveria executar testes e executa zero não comprova cobertura; um check documental sem testes é avaliado pelo seu próprio contrato.

Classifique separadamente:

| Resultado | Tratamento |
|---|---|
| Defeito demonstrado na mudança | Corrigir dentro da autorização ou registrar tarefa de correção |
| Falha confirmada também na base | Relatar como preexistente, com evidência |
| Falha com base indisponível | Relatar a falha atual e a atribuição inconclusiva |
| SDK, permissão ou dependência indisponível | Relatar verificação impedida e recurso necessário |

Uma falha ambiental não vira defeito de código só porque não foi possível testar a base.

Quando a comparação exigir outra árvore, crie uma worktree temporária em caminho novo e identificado, rode nela o mesmo comando e registre o resultado. Antes de removê-la, confira o caminho absoluto, o registro em `git worktree list` e se os arquivos pertencem ao teste. Use remoção forçada apenas para os artefatos gerados nessa árvore; não presuma propriedade pelo nome da pasta. Se a preparação ou limpeza falhar, investigue alternativas proporcionais e informe o que permaneceu.

## Aderência ao design

Compare estrutura, propósito dos componentes, interfaces, dependências, fronteiras, eventos e mitigação dos riscos com o design ou plano atual.

Arquivos indispensáveis descobertos e registrados em `Where` não são desvios por si só. Mudança de comportamento requer corrigir o artefato de origem; desvio técnico autorizado deve ter justificativa.

Cada teste novo deve corresponder a requisito, cenário de erro, regressão ou critério de conclusão. Avalie abstrações e flexibilidade pelo uso concreto, sem presumir defeito apenas por um único consumidor.

## Correções e relatório

Defeitos demonstrados recebem `TCn` em `Correction Tasks` ou no plano da conversa, com os campos de [tasks.md](tasks.md) e rastreabilidade. Em implementação autorizada, execute as correções e verifique novamente os pontos afetados.

Continue enquanto houver correção fundamentada ou nova evidência. Quando a mesma tentativa não trouxer progresso, mude a hipótese ou informe a dependência real; não pare pelo número arbitrário de rodadas.

O relatório na conversa apresenta:

1. Cobertura dos requisitos em escopo e grau de independência.
2. Versão examinada, base e evidências dos checks.
3. Ressalvas de aderência ao design.
4. Defeitos, lacunas de precisão e verificações impedidas, com impacto.
5. Trabalho concluído e pendências necessárias.

Persista relatório apenas se o pedido ou a convenção exigir. Diferencie resultado observado, hipótese e check não realizado.

## Mutation testing

Avalie mutation testing quando a alteração envolver cálculo financeiro, segurança, concorrência, duplicação ou reprocessamento. Registre a decisão de usar ou dispensar com relação ao risco e às demais evidências.

Execute quando o usuário exigir ou o plano o adotar como mitigação. Com `tasks.md`, declare comando na linha `Mutation` de `Gate Commands`; sem ele, use `; mutation: <comando>` no plano. Declare também os arquivos ou regras abrangidos e o critério de avaliação.

Use ferramenta existente e apropriada, com compatibilidade confirmada. Mutante sobrevivente requer análise: pode expor lacuna de teste, equivalência ou comportamento fora do escopo. Registre a conclusão com evidência. Ferramenta indisponível impede a verificação prometida; não permite declará-la realizada.
