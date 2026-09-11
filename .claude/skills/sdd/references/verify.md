# Verify

**Objetivo:** depois da última task, provar com evidência que a implementação atende à spec (eixo 1) e ao design (eixo 2). O relatório vai no chat; nenhum relatório é persistido em arquivo.

## Olhos frescos

Re-derive a cobertura a partir dos testes do diff, sem partir da tabela de evidência do Execute (na passada do próprio autor, a tabela só é aberta no fim, para comparar), e declare no relatório qual foi o grau de independência da verificação:

- **Sub-agente fresco:** verificação independente, feita por quem não escreveu o código. É o modo obrigatório quando a ferramenta de sub-agente existe no ambiente.
- **Passada do próprio autor:** independência parcial, só quando não há ferramenta de sub-agente; diga isso explicitamente.

O grau de independência não muda o resto: cada requisito tem evidência ou conta como zero, e os dois eixos são verificados.

## Escopo

O objeto da verificação é o diff da mudança, `git diff <base>`, mais os arquivos staged, unstaged e untracked listados nos campos `Onde` das tasks (ou no plano inline).

`<base>` é o resultado da primeira destas regras que devolve um hash, nesta ordem:

1. a base registrada antes da primeira task: o hash da linha `Base: <hash>` do parágrafo "Como este repositório testa" do `tasks.md`, ou do slot `; base: <hash>` da linha `Gate` do plano inline (execute.md, Antes da primeira task);
2. com branch próprio: `git merge-base HEAD <branch principal>`;
3. `git log --diff-filter=A --format=%H -1 -- <capability-dir>/NNNN-<change-slug>`, o commit que criou a pasta da mudança; a base é `<hash>^`.

O commit que tocou a `spec.md` nunca serve de base: a spec é viva e o último commit dela pode ser de outra mudança, ou do meio desta. Nenhuma das três devolve hash: a verificação está bloqueada por falta de base. Diga qual regra falhou e pergunte qual commit é a base; não adivinhe.

Alterações do usuário fora da mudança ficam fora da verificação e intocadas: o Verify não faz `add`, `stash`, `checkout` nem "restaura" arquivo algum.

## Eixo 1: conformidade à spec

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
- **Gate vermelho não fecha a mudança.** Cada teste falho entra em Gaps com o nome do teste e vira uma task de correção `TCn` (Gaps e tasks de correção); a asserção não se afrouxa, não se pula e não se mocka. Teste que já falhava na base — confirmado rodando o mesmo comando em `<base>` (Escopo) — é reportado como pré-existente, fica fora dos gaps desta mudança e não vira `TCn`.

## Eixo 2: aderência ao design

Compare com o `design.md`, com a estrutura declarada no `tasks.md` ou com o plano inline, conforme o que a mudança tem. Verifique:

- **Estrutura:** arquivos, componentes e localização batem com o design. Arquivo que o design não listava e que uma task registrou no campo `Onde` com a nota de descoberta conta como conformidade, não como gap: a regra está em execute.md (execute.md, Ciclo por task) e é ela que vale aqui. Arquivo no diff que nem o design lista nem nota alguma explica é gap.
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

## Gaps e tasks de correção

Cada gap vira uma task de correção com ID `TCn`, registrada em `## Tasks de correção` do `tasks.md` (ou no plano inline, quando não há `tasks.md`). A task `TCn` tem os mesmos campos de uma task (tasks.md, Campos) e entra na Rastreabilidade; rode `lint_tasks.py` de novo; com commit autorizado, o `tasks.md` alterado entra no commit da primeira `TC` (SKILL.md, Aprovação e autorizações). A task de correção volta ao ciclo do Execute e é seguida de nova verificação. Depois de duas rodadas de correção com gap remanescente, escale ao usuário em vez de girar; a re-derivação por desvio de comportamento (Desvios, abaixo) conta nessas duas rodadas.

## Desvios

- **Desvio que muda comportamento** não sobrevive à verificação. O caminho é voltar ao artefato de origem (PRD, spec ou design), corrigi-lo, obter o commit dele (SKILL.md, Aprovação e autorizações), re-derivar a implementação e verificar de novo.
- **Desvio sem mudança de comportamento** (estrutura, nome interno) fica registrado em `## Desvios` do `tasks.md` (ou do plano inline) com justificativa e é julgado no eixo 2. Arquivo indispensável descoberto durante a task tem rota própria, e não é esta (execute.md, Ciclo por task).

## Mutação

Teste de mutação roda quando o comando de mutação está declarado nesta mudança, e só então. A declaração tem um lugar, e ele depende só de a mudança ter ou não `tasks.md`: com `tasks.md`, é a linha `Mutação` da tabela Comandos de Gate (tasks.md, Comandos de Gate); sem ele, é o slot `; mutação: <comando>` da linha `Gate` do plano inline (execute.md, Plano inline). Vale igual nas quatro configurações: com design e sem design, com `tasks.md` e sem ele.

Declarar o comando é obrigatório em dois casos: quando a tabela Riscos e técnicas do design tem linha de um destes três riscos, e só deles — dinheiro e cálculo financeiro; segurança e dado regulado; concorrência, duplicata e retry (design.md, Do risco à técnica) —, e quando o usuário pede mutação nesta mudança. Design com um desses três riscos e sem o comando declarado é gap do eixo 2: o risco não foi mitigado como o design prometeu. Fora dessas duas obrigações, declarar é opção do usuário.

A obrigação vinda do design não espera o Verify quando há `tasks.md`: `lint_tasks.py` lê a tabela Riscos e técnicas do design e acusa como HARD a tabela Comandos de Gate sem a linha `Mutação` (tasks.md, Registro no `tasks.md`). Sem `tasks.md`, quem confere é você, no plano inline, antes de apresentá-lo.

Use a ferramenta de mutação da linguagem (Stryker.NET, mutmut, cargo-mutants) sobre o código novo e trate mutante sobrevivente como gap; ferramenta ausente é bloqueio com motivo, como o gate. Esta skill não descreve procedimento próprio de mutação.
