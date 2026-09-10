# Execute

**Objetivo:** implementar uma task por vez. Cada task é uma mudança cirúrgica, com teste derivado da spec, gate rodado e commit atômico quando o commit está autorizado. Cada task carrega a própria verificação (testes, gate e revisão pós-gate).

## Antes da primeira task

1. **Pré-requisito.** O `tasks.md` está commitado ou, quando a entrada Tasks foi dispensada, o plano inline foi apresentado e aprovado. O pedido "implementa" autoriza editar os arquivos da mudança; commit é uma autorização própria, dada uma vez por mudança (SKILL.md, Aprovação e autorizações).
2. **Contexto.** Leia a task, o trecho do design que ela referencia e os requisitos da spec que ela atende. Não carregue outras mudanças no contexto.
3. **`[LACUNA]` no caminho.** Uma lacuna encontrada em artefato que a task usa se resolve de uma destas três formas, e de nenhuma outra:
   - decida e registre a decisão, quando ela cabe na autonomia concedida;
   - marque `[PREMISSA]` na spec, com default e racional;
   - pergunte ao usuário ("O design tem uma lacuna: […]. Opções: […]. Recomendo […].") e execute só o que não depende da resposta.

   Nunca resolva a lacuna em silêncio, e nunca trate o silêncio do usuário como resposta.

### Plano inline

Quando a entrada Tasks foi dispensada, o Execute começa por um plano inline, apresentado no chat antes de qualquer código:

```markdown
## Plano
Requisitos (só sem spec.md): - **XYZ-01** — WHEN … THEN the system SHALL …
Estrutura: [uma ou duas linhas: onde entra, o que reusa]
Gate: [comando de build e teste do repositório]
1. [passo] → arquivos: […] → verifica: [como]
2. …
```

Cada passo do plano é um entregável coeso, pelo mesmo critério de uma task (tasks.md, Task atômica). Se a lista passar de cinco passos, ou algum passo depender de outro que não é o imediatamente anterior, ou houver risco nomeado, pare e crie o artefato que faltou: é a catraca subindo (SKILL.md, Abrir uma mudança), e complexidade descoberta no meio promove a mudança ao artefato que ela pede.

## Ciclo por task

1. **Escolher.** Execute a task que o usuário indicou ("faz a T3") ou, sem indicação, a próxima disponível na ordem do plano. Se a task depende de outra ainda não concluída, pergunte antes de começar.
2. **Declarar o plano da task** em três linhas: os arquivos que vai tocar (só os da task), a abordagem e como vai verificar. Se enxerga uma abordagem mais simples que a do design, ou discorda dele, diga antes de implementar, não depois.
3. **Escrever os testes derivados da spec.**
   - Cada requisito da task tem ao menos uma assertion cujo valor esperado é o resultado que a spec define (status, mensagem, estado, evento).
   - Se a spec não define um resultado preciso, isso é lacuna de precisão: volte à spec e corrija lá; não escreva assertion vaga.
   - Teste de comportamento novo falha antes de o código existir. Teste de caracterização (comportamento que a mudança preserva) passa antes e depois.
   - Se um teste parece errado quando confrontado com a spec, pare e confirme o que está certo antes de seguir: os testes são a spec executável.
4. **Implementar** o mínimo que satisfaz a task.
   - Nada além do pedido: sem abstração de uso único, sem flexibilidade não solicitada, sem tratamento de cenário impossível.
   - Não "melhore" código adjacente nem formatação; siga o estilo existente mesmo discordando dele.
   - Problema vizinho (bug, dívida, dead code) é reportado ao usuário, não corrigido na task.
   - Arquivo indispensável descoberto durante a implementação (registro, config) entra no campo `Onde` da task, com uma nota dizendo por que entrou.
5. **Rodar o gate.** Rode o comando do nível da task, lido da tabela Comandos de Gate do `tasks.md` da mudança (descrita em tasks.md, Comandos de Gate) ou da linha `Gate` do plano inline. Exit diferente de zero: corrija e rode de novo, no máximo duas vezes; se a terceira execução ainda não sair com exit 0, pare e relate a falha como ela é, sem enfraquecer o teste. Gate que não pode rodar (SDK ausente, dependência indisponível) não é gate verde: a task fica bloqueada, com o motivo registrado.
6. **Revisar depois do gate.** Com o gate verde, confira:
   - todo item de `Pronto quando` está atendido, inclusive os critérios de comportamento;
   - nenhum `SPEC_DEVIATION` ficou sem registro em `## Desvios`;
   - nenhum dos três sinais de complexidade está presente: abstração usada uma vez só, parâmetro ou opção sem chamador, camada que o design não pede. Se algum estiver, simplifique uma vez e rode o gate de novo;
   - a tabela de evidência: para cada critério, o `file:line` e a assertion que o provam; e, no sentido inverso, todo teste novo mapeia para um critério, requisito ou edge case.
7. **Fechar.** Marque a task como concluída no `tasks.md` (ou no plano inline). Com commit autorizado, faça um commit contendo só os arquivos da task e o `tasks.md`, com mensagem no formato que o repositório convenciona; se o repositório tem validação de mensagem de commit, rode-a antes de commitar. Sem commit autorizado, a task fecha com o gate verde e os arquivos na árvore de trabalho.

## Refine o contexto, não o erro

O princípio geral está em SKILL.md, Tags e dúvidas. Durante uma task, ele se aplica assim:

- **Spec ou design errados** (regra impossível, contrato inconsistente, restrição da base não prevista) param a task. Reporte no chat: "Encontrei uma restrição não prevista: […]. Isso invalida [spec/design] em […]. Recomendo corrigir lá e re-derivar [tasks afetadas]."
- **Regra de negócio errada** volta ao PRD primeiro; a spec só é corrigida depois dele.
- **Desvio local** que não invalida o artefato recebe um marcador no código e uma linha em `## Desvios` do `tasks.md`; a seção é criada no primeiro desvio. O marcador:

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
- **Retomar.** Retomar uma mudança é ler o `tasks.md` e o `git status`. Uma task só conta como concluída quando tem gate verde registrado; `git status` é indício de progresso, não prova.
