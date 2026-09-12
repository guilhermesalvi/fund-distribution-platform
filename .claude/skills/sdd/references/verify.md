# Verify

**Objetivo:** depois da última task, provar com evidência que a implementação atende à spec (eixo 1) e ao design (eixo 2). O relatório vai no chat; nenhum relatório é persistido em arquivo.

## Olhos frescos

Re-derive a cobertura a partir da spec e dos testes da mudança. Use um revisor independente quando o ambiente permitir, conforme os modos abaixo. Faça essa re-derivação sem partir da tabela de evidência do Execute (na passada do próprio autor, a tabela só é aberta no fim, para comparar), e declare no relatório qual foi o grau de independência da verificação:

- **Sub-agente fresco:** verificação independente, feita por quem não escreveu o código. É o modo obrigatório quando a ferramenta de sub-agente existe no ambiente.
- **Passada do próprio autor:** independência parcial, só quando não há ferramenta de sub-agente; diga isso explicitamente.

O grau de independência não muda o resto: cada requisito tem evidência ou conta como zero, e os dois eixos são verificados.

## Escopo

O objeto da verificação é o diff da mudança, `git diff <base>`, mais os arquivos staged, unstaged e untracked listados nos campos `Onde` das tasks (ou no plano inline).

`<base>` é o resultado da primeira destas regras que devolve um hash, nesta ordem:

1. a base registrada antes da primeira task: o hash da linha `Base: <hash>` do parágrafo "Como este repositório testa" do `tasks.md`, ou do slot `; base: <hash>` da linha `Gate` do plano inline (execute.md, Antes da primeira task);
2. com branch próprio: `git merge-base HEAD <branch principal>`;
3. `git log --diff-filter=A --format=%H --reverse -- <capability-dir>/NNNN-<change-slug> | head -n 1`, o primeiro commit que adicionou arquivo na pasta da mudança, isto é, o que criou a pasta; a base é `<hash>^`. O `--reverse` com `head -n 1` é o que devolve o primeiro: `-1` devolveria o commit mais recente que tocou a pasta, e com `design.md` e `tasks.md` em commits separados (workflow.md, Aprovação e autorizações) os dois divergem.

O commit que tocou a `spec.md` nunca serve de base: a spec é viva e o último commit dela pode ser de outra mudança, ou do meio desta. Nenhuma das três devolve hash: a verificação está bloqueada por falta de base. Diga qual regra falhou e pergunte qual commit é a base; não adivinhe.

Pela regra 3, commit alheio feito entre a criação da pasta e o HEAD entra no diff. Arquivo que veio de commit assim não é gap: nomeie-o no relatório como fora da mudança e deixe-o fora dos dois eixos; `git log --format=%h --follow -- <arquivo>` diz de qual commit ele veio.

Alterações do usuário fora da mudança ficam fora da verificação e intocadas: o Verify não faz `add`, `stash`, `checkout` nem "restaura" arquivo algum. Rodar o gate em `<base>` não é exceção: tem rota própria, em árvore separada, que não toca esta (Gate Build).

## Eixo 1: conformidade à spec

Antes de calcular cobertura, confirme a versão commitada da spec pelos três comandos e pela saída de bloqueio definidos em (execute.md, Depois da última task).

Para cada requisito em escopo, preencha uma linha da tabela de evidência. A coluna Resultado recebe um destes valores: `coberto`, `gap` ou `lacuna de precisão`.

| Requisito | Resultado definido pela spec | `file:line` + assertion | Resultado |
|---|---|---|---|
| RSV-07 | rejeita com `MIN_INVESTMENT_NOT_MET`, livro inalterado | `tests/…/PartialReservationTests.cs:41` — `result.Error.Should().Be(ReservationError.MinInvestmentNotMet)` | coberto / gap / lacuna de precisão |

- A assertion precisa mirar exatamente o resultado que a spec define; a existência de uma assertion qualquer não basta.
- Requisito sem `file:line` conta como não coberto. Antes de declarar ausência, busque o ID do requisito e o identificador do resultado que a spec define (erro, evento, status) nos testes do diff e nos testes da camada, e mostre no relatório os termos buscados.
- Requisito cuja spec não define um resultado preciso é lacuna de precisão: entra no relatório como tal e nunca é aprovado em silêncio.
- Requisito aposentado na spec (specify.md, Spec viva) exige confirmar que o comportamento não existe mais: o teste foi removido com a razão registrada e nenhum caminho de código vivo ainda o implementa.

## Gate Build

Rode o gate Build: o comando da tabela Comandos de Gate (tasks.md, Comandos de Gate) ou, quando a mudança usa plano inline, o gate declarado no plano. Registre no relatório o comando, o total de testes, os passados, os falhos, os pulados e o exit code.

Compare a contagem de testes com a contagem-base registrada no parágrafo "Como este repositório testa" do `tasks.md` ou na linha `Gate` do plano inline (tasks.md, Como o repositório testa) e investigue qualquer queda: só a aposentadoria de requisito com razão registrada justifica menos testes; queda sem essa razão é gap.

- Teste pulado não é evidência.
- Zero testes executados não é gate verde.
- Gate que não pode rodar é bloqueio com motivo declarado, não falha.
- **Gate vermelho não fecha a mudança.** Cada teste falho entra em Gaps com o nome do teste e vira uma task de correção `TCn` (Gaps e tasks de correção); a asserção não se afrouxa, não se pula e não se mocka. Teste que já falhava na base é reportado como pré-existente, fica fora dos gaps desta mudança e não vira `TCn` — e só com a confirmação abaixo.

Confirmar falha pré-existente tem uma rota, e é esta:

1. `git worktree add <dir-temporário> <base>`, com `<base>` sendo o hash do Escopo e `<dir-temporário>` um diretório que ainda não existe, fora da árvore de trabalho da mudança.
2. Rode dentro de `<dir-temporário>` o mesmo comando de gate que rodou na árvore da mudança.
3. `git worktree remove --force <dir-temporário>` ao fim, sempre, tenha o teste falhado lá ou não. O `--force` é obrigatório: o gate deixa artefato não rastreado dentro do worktree (`bin/`, `obj/`, `node_modules/`, `__pycache__`) e sem ele o remove sai 128 com `contains modified or untracked files`. Ali não há nada do usuário — o diretório só tem o que o passo 1 e o passo 2 puseram.

O worktree checa `<base>` numa árvore separada e não mexe na árvore de trabalho da mudança. Por isso a proibição de `add`, `stash`, `checkout` e de "restaurar" arquivo algum (Escopo) continua valendo inteira: esta rota não usa nenhum dos quatro, e nenhum outro caminho até `<base>` está liberado.

`git worktree add` que sai com código diferente de 0 encerra a tentativa: reporte o teste como falha não confirmada na base e trate-o como qualquer teste falho — entra em Gaps e vira `TCn`. Não repita o comando, não tente outra rota e não pergunte ao usuário. Se for o `git worktree remove --force` que sair diferente de 0, o resultado do gate na base vale do mesmo jeito; nomeie no relatório o diretório que ficou para trás e siga.

## Eixo 2: aderência ao design

Compare com o `design.md`, com a estrutura declarada no `tasks.md` ou com o plano inline, conforme o que a mudança tem. Verifique:

- **Estrutura:** arquivos, componentes e localização batem com o design. Arquivo que o design não listava e que uma task registrou no campo `Onde` com a nota de descoberta conta como conformidade, não como gap: a regra está em execute.md (execute.md, Ciclo por task) e é ela que vale aqui. Arquivo no diff que nem o design lista nem nota alguma explica é gap, exceto o que veio de commit alheio dentro da janela da base (Escopo).
- **Responsabilidades:** cada componente faz o que o design diz, e só isso.
- **Interfaces:** assinaturas iguais às do design.
- **Dependências:** nenhuma fora do planejado (pacote, módulo, serviço).
- **Fronteiras entre módulos:** nenhum ciclo entre módulos; nenhuma classe interna de outro módulo instanciada.
- **Domain events:** conformes ao contrato do design.
- **Riscos:** mitigados como o design prometeu.
- **Desvios:** cada `SPEC_DEVIATION` justificado e listado.

No relatório, só itens com ressalva ou não atendidos ganham observação. Item não atendido vira gap.

## Qualidade de código

Para cada arquivo do diff, verifique:

- nada além do pedido;
- nenhuma abstração de uso único;
- nenhuma flexibilidade não solicitada;
- código adjacente não "melhorado";
- estilo existente seguido;
- guias de teste do projeto seguidos.

Todo teste no escopo mapeia para um requisito, um edge case ou um critério de `Pronto quando`. Teste órfão, sem esse mapeamento, é escopo escondido.

## Relatório no chat

O relatório segue esta ordem:

1. **Cobertura**, na primeira linha: N/N requisitos com evidência.
2. **Gate:** comando, contagens e exit code.
3. **Aderência ao design:** só as ressalvas.
4. **Gaps**, ordenados por severidade: requisito sem evidência, depois lacuna de precisão, depois desvio de design.
5. **Próximo passo.**

Verificação bloqueada por ambiente diz o que faltou e não fecha a mudança.

### Forma da comunicação

Comece pela cobertura e mantenha a ordem definida para o relatório. Distinga achado, hipótese e verificação não executada. Cada ressalva identifica requisito ou arquivo, resultado esperado e evidência disponível. Se uma regra impediu a conclusão, cite o arquivo e a seção que a estabelecem. O relatório deve permitir decidir o próximo passo sem consultar elogios ou conclusões genéricas.

## Gaps e tasks de correção

Cada gap vira uma task de correção com ID `TCn`, registrada em `## Tasks de correção` do `tasks.md` (ou no plano inline, quando não há `tasks.md`). A task `TCn` tem os mesmos campos de uma task (tasks.md, Campos) e entra na Rastreabilidade; repita a checagem de forma do `tasks.md` (validation.md, Checagem de forma); com commit autorizado e conteúdo aprovado, o `tasks.md` alterado entra no commit da primeira `TC` (workflow.md, Aprovação e autorizações). A task de correção volta ao ciclo do Execute e é seguida de nova verificação. Depois de duas rodadas de correção com gap remanescente, escale ao usuário em vez de girar; a re-derivação por desvio de comportamento (Desvios, abaixo) conta nessas duas rodadas.

## Desvios

- **Desvio que muda comportamento** não sobrevive à verificação. O caminho é voltar ao artefato de origem (PRD, spec ou design), corrigi-lo, obter o commit dele (workflow.md, Aprovação e autorizações), re-derivar a implementação e verificar de novo.
- **Desvio sem mudança de comportamento** (estrutura, nome interno) fica registrado em `## Desvios` do `tasks.md` (ou do plano inline) com justificativa e é julgado no eixo 2. Arquivo indispensável descoberto durante a task tem rota própria, e não é esta (execute.md, Ciclo por task).

## Mutação

Teste de mutação roda quando o comando de mutação está declarado nesta mudança, e só então. A declaração tem um lugar, e ele depende só de a mudança ter ou não `tasks.md`: com `tasks.md`, é a linha `Mutação` da tabela Comandos de Gate (tasks.md, Comandos de Gate); sem ele, é o slot `; mutação: <comando>` da linha `Gate` do plano inline (execute.md, Plano inline). Vale igual nas quatro configurações: com design e sem design, com `tasks.md` e sem ele.

Declarar o comando é obrigatório em dois casos: quando a tabela Riscos e técnicas do design tem linha de um destes três riscos, e só deles — dinheiro e cálculo financeiro; segurança e dado regulado; concorrência, duplicata e retry (design.md, Do risco à técnica) —, e quando o usuário pede mutação nesta mudança. Design com um desses três riscos e sem o comando declarado é gap do eixo 2: o risco não foi mitigado como o design prometeu. Fora dessas duas obrigações, declarar é opção do usuário.

A obrigação vinda do design não espera o Verify quando há `tasks.md`: a checagem de forma do `tasks.md` lê a tabela Riscos e técnicas do design e acusa a tabela Comandos de Gate sem a linha `Mutação` (tasks.md, Registro no `tasks.md`). Sem `tasks.md`, quem confere é você, no plano inline, antes de apresentá-lo.

Use a ferramenta de mutação da linguagem (Stryker.NET, mutmut, cargo-mutants) sobre o código novo e trate mutante sobrevivente como gap; ferramenta ausente é bloqueio com motivo, como o gate. Esta skill não descreve procedimento próprio de mutação.

### Exemplo didático parcial de reescrita

Fragmento de escrita; não é um artefato completo nem evidência de uma execução real.

```text
Antes: Os testes passaram, mas há uma pequena pendência de cobertura.

Depois: Cobertura: 2/3 requisitos com evidência. RSV-03 está sem assertion
localizada para POSITION_ABOVE_MAXIMUM. O gate executou 20 testes, com
20 aprovados, nenhum pulado e exit 0. O gap de RSV-03 impede concluir
a verificação da mudança.

Números ilustrativos. Em uma execução real, usar a saída do gate e
as buscas efetivamente realizadas. O relatório completo mantém todos
os itens e a evidência exigidos pela referência.
```
