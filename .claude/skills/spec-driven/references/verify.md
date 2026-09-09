# Verify

**Objetivo:** depois da última task, provar com evidência que a implementação atende à spec (eixo 1) e ao design (eixo 2). O relatório vai no chat; nada de relatório persistido.

**Olhos frescos.** Re-derive a cobertura sem consultar a tabela que você produziu no Execute, e diga isso no relatório: sub-agente fresco (independente) ou passada do próprio autor (independência parcial). O que não muda: evidência ou zero, dois eixos.

**Escopo:** o diff da mudança (`git diff <base>`, staged, unstaged e untracked pertinentes). Alterações do usuário fora da mudança ficam fora e intocadas; o Verify não faz `add`, `stash`, `checkout` nem "restaura" nada.

## Eixo 1: conformidade à spec

Para cada requisito em escopo:

| Requisito | Resultado definido pela spec | `file:line` + assertion | Resultado |
|---|---|---|---|
| RSV-07 | rejeita com `MIN_INVESTMENT_NOT_MET`, livro inalterado | `tests/…/PartialReservationTests.cs:41` — `result.Error.Should().Be(ReservationError.MinInvestmentNotMet)` | coberto / gap / lacuna de precisão |

- A assertion mira exatamente o resultado que a spec define; existir assertion não basta.
- Sem `file:line`, o requisito conta como não coberto. Procure antes de declarar ausência; mostre a busca.
- Spec sem resultado preciso é lacuna de precisão: reportada, nunca aprovada em silêncio.
- Requisito aposentado na spec: confirme que o comportamento não existe mais (teste removido com a razão; nenhum caminho vivo).

## Gate Build

Rode o gate Build (Comandos de Gate, ou o gate do plano inline). Registre comando, total, passados, falhos, pulados e exit; compare a contagem de testes com a de antes da mudança e investigue queda (só aposentadoria com razão justifica). Teste pulado não é evidência; zero testes executados não é gate verde. Gate que não pode rodar é bloqueio com motivo, não falha.

## Eixo 2: aderência ao design

Compare com o `design.md`, ou com a estrutura declarada no `tasks.md`, ou com o plano inline: estrutura (arquivos, componentes, localização); responsabilidades (componente faz o que o design diz, e só isso); interfaces com as assinaturas do design; dependências fora do planejado (pacote, módulo, serviço); ciclos entre módulos e classe interna de outro módulo instanciada; domain events com o contrato do design; riscos mitigados como prometido; desvios (`SPEC_DEVIATION`) justificados e listados. Só itens com ressalva ou não atendidos ganham observação; item não atendido vira gap.

## Qualidade de código

Por arquivo do diff: nada além do pedido; sem abstração de uso único; sem flexibilidade não solicitada; código adjacente não "melhorado"; estilo existente seguido; guias de teste do projeto seguidos. Todo teste no escopo mapeia para requisito, edge case ou `Pronto quando`: teste órfão é escopo escondido.

## Relatório no chat

Primeira linha: cobertura N/N requisitos com evidência. Depois: gate (comando, contagens, exit); aderência (só ressalvas); gaps ordenados por severidade; próximo passo. Verificação bloqueada por ambiente diz o que faltou e não fecha a mudança.

Gap vira task de correção `TCn` em `## Tasks de correção` do `tasks.md` (ou no plano inline) e volta ao ciclo do Execute, seguida de nova verificação. Se não converge, escale ao usuário em vez de girar.

## Desvios

Desvio que muda comportamento não sobrevive: volta ao artefato de origem (PRD, spec, design), o artefato é corrigido e commitado, a implementação é re-derivada e reverificada. Desvio sem mudança de comportamento (estrutura, nome interno) fica em `## Desvios` com justificativa e é julgado no eixo 2.

## Mutação

Opcional, em caminho crítico (dinheiro, liquidação, auth, integridade): use a ferramenta de mutação da linguagem (Stryker.NET, mutmut, cargo-mutants) sobre o código novo e trate mutante sobrevivente como gap. Esta skill não descreve procedimento próprio.
