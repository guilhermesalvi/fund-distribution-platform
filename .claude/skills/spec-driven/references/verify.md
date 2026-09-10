# Verify

**Objetivo:** depois da última task, provar com evidência que a implementação atende à spec (eixo 1) e ao design (eixo 2). O relatório vai no chat; nenhum relatório é persistido em arquivo.

## Olhos frescos

Re-derive a cobertura sem consultar a tabela de evidência que você produziu no Execute, e declare no relatório qual foi o grau de independência da verificação:

- **Sub-agente fresco:** verificação independente, feita por quem não escreveu o código.
- **Passada do próprio autor:** independência parcial; diga isso explicitamente.

O grau de independência não muda o resto: cada requisito tem evidência ou conta como zero, e os dois eixos são verificados.

## Escopo

O objeto da verificação é o diff da mudança: `git diff <base>`, mais os arquivos staged, unstaged e untracked pertinentes à mudança. Alterações do usuário fora da mudança ficam fora da verificação e intocadas: o Verify não faz `add`, `stash`, `checkout` nem "restaura" arquivo algum.

## Eixo 1: conformidade à spec

Para cada requisito em escopo, preencha uma linha da tabela de evidência. A coluna Resultado recebe um destes valores: `coberto`, `gap` ou `lacuna de precisão`.

| Requisito | Resultado definido pela spec | `file:line` + assertion | Resultado |
|---|---|---|---|
| RSV-07 | rejeita com `MIN_INVESTMENT_NOT_MET`, livro inalterado | `tests/…/PartialReservationTests.cs:41` — `result.Error.Should().Be(ReservationError.MinInvestmentNotMet)` | coberto / gap / lacuna de precisão |

- A assertion precisa mirar exatamente o resultado que a spec define; a existência de uma assertion qualquer não basta.
- Requisito sem `file:line` conta como não coberto. Antes de declarar ausência, procure a evidência e mostre no relatório a busca que fez.
- Requisito cuja spec não define um resultado preciso é lacuna de precisão: entra no relatório como tal e nunca é aprovado em silêncio.
- Requisito aposentado na spec (specify.md, Spec viva) exige confirmar que o comportamento não existe mais: o teste foi removido com a razão registrada e nenhum caminho de código vivo ainda o implementa.

## Gate Build

Rode o gate Build: o comando da tabela Comandos de Gate (tasks.md, Comandos de Gate) ou, quando a mudança usa plano inline, o gate declarado no plano. Registre no relatório o comando, o total de testes, os passados, os falhos, os pulados e o exit code.

Compare a contagem de testes com a de antes da mudança e investigue qualquer queda: só a aposentadoria de requisito com razão registrada justifica menos testes.

- Teste pulado não é evidência.
- Zero testes executados não é gate verde.
- Gate que não pode rodar é bloqueio com motivo declarado, não falha.

## Eixo 2: aderência ao design

Compare com o `design.md`, com a estrutura declarada no `tasks.md` ou com o plano inline, conforme o que a mudança tem. Verifique:

- **Estrutura:** arquivos, componentes e localização batem com o design.
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
4. **Gaps**, ordenados por severidade.
5. **Próximo passo.**

Verificação bloqueada por ambiente diz o que faltou e não fecha a mudança.

## Gaps e tasks de correção

Cada gap vira uma task de correção com ID `TCn`, registrada em `## Tasks de correção` do `tasks.md` (ou no plano inline, quando não há `tasks.md`). A task de correção volta ao ciclo do Execute e é seguida de nova verificação. Se o ciclo não converge, escale ao usuário em vez de girar.

## Desvios

- **Desvio que muda comportamento** não sobrevive à verificação. O caminho é voltar ao artefato de origem (PRD, spec ou design), corrigir e commitar esse artefato, re-derivar a implementação e verificar de novo.
- **Desvio sem mudança de comportamento** (estrutura, nome interno) fica registrado em `## Desvios` do `tasks.md` com justificativa e é julgado no eixo 2.

## Mutação

Teste de mutação é opcional e cabe em caminho crítico (dinheiro, liquidação, auth, integridade). Use a ferramenta de mutação da linguagem (Stryker.NET, mutmut, cargo-mutants) sobre o código novo e trate mutante sobrevivente como gap. Esta skill não descreve procedimento próprio de mutação.
