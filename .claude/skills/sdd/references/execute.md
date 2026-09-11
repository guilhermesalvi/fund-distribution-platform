# Execute

**Objetivo:** implementar uma task por vez. Cada task é uma mudança cirúrgica, com teste derivado da spec, gate rodado e commit atômico quando o commit está autorizado. Cada task carrega a própria verificação (testes, gate e revisão pós-gate).

## Antes da primeira task

1. **Pré-requisito.** O da tabela de SKILL.md, Abrir uma mudança. O pedido "implementa" autoriza editar os arquivos da mudança; commit é uma autorização própria, dada uma vez por mudança e válida para todos os commits dela (SKILL.md, Aprovação e autorizações).
2. **Contexto.** Leia a task, o trecho do design que ela referencia e os requisitos da spec que ela atende. Não carregue outras mudanças no contexto.
3. **Base da verificação.** Se a mudança não tem branch próprio nem pasta `NNNN-<change-slug>` (as regras 2 e 3 de verify.md, Escopo, não devolvem hash), registre a base antes da primeira edição de código: `git rev-parse HEAD`, gravado como a linha `Base: <hash>` do parágrafo "Como este repositório testa" do `tasks.md` ou como o slot `; base: <hash>` da linha `Gate` do plano inline. Com branch próprio ou pasta da mudança, não registre nada: o Verify resolve a base sozinho, e um hash a mais seria uma segunda fonte da mesma informação.
4. **`[LACUNA]` no caminho.** Vale a regra de SKILL.md, Tags e dúvidas; numa task, as três saídas tomam esta forma:
   - decida e registre a decisão, quando ela cabe na autonomia concedida;
   - marque `[PREMISSA]` na spec, com default e racional; a spec alterada entra no commit da task, e o Verify lê a spec commitada;
   - pergunte ao usuário ("O design tem uma lacuna: […]. Opções: […]. Recomendo […].") e execute só o que não depende da resposta.

### Plano inline

Quando a entrada Tasks foi dispensada, o Execute começa por um plano inline, apresentado no chat antes de qualquer código:

```markdown
## Plano
Requisitos: [IDs da spec.md que o plano cobre]
Estrutura: [uma ou duas linhas: onde entra, o que reusa]
Gate: [comando de build e teste do repositório]; [total de testes que ele executa antes da mudança][; base: hash, quando a mudança registra a base][; mutação: comando, quando a mudança declara mutação]
1. [passo] → arquivos: […] → verifica: [como]
2. …
```

A linha `Gate` é onde o comando de mutação fica declarado quando a mudança não tem `tasks.md`: acrescente `; mutação: <comando>` a ela quando o usuário pede mutação nesta mudança ou quando a tabela Riscos e técnicas do design a obriga (verify.md, Mutação). Sem a declaração, a linha termina no total de testes e a mudança não roda mutação. O slot `; base: <hash>` da mesma linha é onde a base fica quando a mudança não tem `tasks.md`, e entra só nas condições de Base da verificação, acima.

Cada passo do plano é um entregável coeso, pelo mesmo critério de uma task (tasks.md, Task atômica). Se a lista disparar qualquer gatilho de `design.md` ou de `tasks.md` (SKILL.md, Abrir uma mudança), pare e crie o artefato que faltou: é a catraca subindo (SKILL.md, Abrir uma mudança), e complexidade descoberta no meio promove a mudança ao artefato que ela pede.

## Ciclo por task

1. **Escolher.** Execute a task que o usuário indicou ("faz a T3") ou, sem indicação, a próxima disponível na ordem do plano. Se a task depende de outra ainda não concluída, pergunte antes de começar.
2. **Declarar o plano da task** em três linhas: os arquivos que vai tocar (só os da task), a abordagem e como vai verificar. Se enxerga uma abordagem mais simples que a do design, ou discorda dele, diga antes de implementar, não depois.
3. **Escrever os testes derivados da spec.**
   - Cada requisito da task tem ao menos uma assertion cujo valor esperado é o resultado que a spec define (status, mensagem, estado, evento).
   - Se a spec não define um resultado preciso, isso é lacuna de precisão: volte à spec e corrija lá; não escreva assertion vaga.
   - Os cenários herdados listados na Rastreabilidade da spec (specify.md, Seções) são a suíte mínima: cada um vira ao menos um teste.
   - Teste de comportamento novo falha antes de o código existir. Teste de caracterização (comportamento que a mudança preserva) passa antes e depois.
   - Se um teste parece errado quando confrontado com a spec, pare e confirme o que está certo antes de seguir: os testes são a spec executável.
4. **Implementar** o mínimo que satisfaz a task.
   - Nada além do pedido: sem abstração de uso único, sem flexibilidade não solicitada, sem tratamento de cenário impossível.
   - Não "melhore" código adjacente nem formatação; siga o estilo existente mesmo discordando dele.
   - Problema vizinho (bug, dívida, dead code) é reportado ao usuário, não corrigido na task.
   - Arquivo indispensável descoberto durante a implementação (registro, config) entra no campo `Onde` da task, com uma nota dizendo por que entrou. A nota é o registro completo e a única rota: o arquivo não vira `SPEC_DEVIATION` nem linha em `## Desvios`, e no eixo 2 do Verify conta como conformidade ao design, não como gap nem como desvio (verify.md, Eixo 2: aderência ao design). Arquivo que muda comportamento não cabe aqui: é desvio, pelo caminho de Refine o contexto, não o erro.
5. **Rodar o gate.** Rode o comando do nível da task, lido da tabela Comandos de Gate do `tasks.md` da mudança (descrita em tasks.md, Comandos de Gate) ou da linha `Gate` do plano inline. Exit diferente de zero: corrija e rode de novo, no máximo duas vezes; se a terceira execução ainda não sair com exit 0, pare e relate a falha como ela é, sem enfraquecer o teste. Gate que não pode rodar (SDK ausente, dependência indisponível) não é gate verde: a task fica bloqueada, com o motivo registrado.
6. **Revisar depois do gate.** Com o gate verde, confira:
   - todo item de `Pronto quando` está atendido, inclusive os critérios de comportamento;
   - nenhum `SPEC_DEVIATION` ficou sem registro em `## Desvios`;
   - nenhum dos três sinais de complexidade está presente: abstração usada uma vez só, parâmetro ou opção sem chamador, camada que o design não pede. Se algum estiver, simplifique uma vez e rode o gate de novo, uma única vez: se ficar vermelho, desfaça a simplificação, porque o gate verde do passo 5 é o que a task entrega e insistir na simplificação abriria um ciclo de correção sem teto; diga no chat qual simplificação foi desfeita e o que o gate acusou;
   - a tabela de evidência: para cada critério, o `file:line` e a assertion que o provam; e, no sentido inverso, todo teste novo mapeia para um critério, requisito ou edge case. A tabela vai no chat ao fechar a task e não é persistida em arquivo.
7. **Fechar.** Marque a task como concluída: todos os itens `- [ ]` de `Pronto quando` passam a `- [x]` no `tasks.md` (ou no plano inline). Com commit autorizado, faça um commit contendo só os arquivos da task, o `tasks.md` e a spec quando a task a alterou (passo 3), com mensagem no formato que o repositório convenciona; se o repositório tem validação de mensagem de commit, rode-a antes de commitar. Sem commit autorizado, a task fecha com o gate verde e os arquivos na árvore de trabalho.

## Refine o contexto, não o erro

O princípio geral está em SKILL.md, Tags e dúvidas. Durante uma task, ele se aplica assim:

- **Spec ou design errados** (regra impossível, contrato inconsistente, restrição da base não prevista) param a task. Reporte no chat: "Encontrei uma restrição não prevista: […]. Isso invalida [spec/design] em […]. Recomendo corrigir lá e re-derivar [tasks afetadas]."
- **Regra de negócio errada** volta ao PRD primeiro; a spec só é corrigida depois dele.
- **Desvio local** que não invalida o artefato recebe um marcador no código e uma linha em `## Desvios` do `tasks.md` (ou do plano inline, no chat, quando não há `tasks.md`); a seção é criada no primeiro desvio. O marcador:

```text
// SPEC_DEVIATION: [o que divergiu]
// Reason: [por quê]
```

## Segurança

- **Pacote novo** é sugestão até que a procedência seja validada no registro oficial: "Sugiro `[nome]`; antes de instalar, confirme em […]". Pacote com nome inventado pode existir no registro, publicado por alguém mal-intencionado.
- **Segredo**, connection string ou dado de produção encontrado na base nunca entra no output; sinalize a ocorrência como risco.

## Depois da última task

- **Verify.** Fechada a última task, passe ao Verify com olhos frescos (verify.md, Olhos frescos).
- **Handoff.** Um branch aberto e o `git log` são o handoff da mudança.
- **Retomar.** Retomar uma mudança é ler o `tasks.md` e o `git status`. Uma task só conta como concluída quando todos os itens de `Pronto quando` estão marcados `[x]`, o que só acontece com gate verde; `git status` é indício de progresso, não prova.
