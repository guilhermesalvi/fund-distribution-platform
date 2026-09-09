# Execute

**Objetivo:** implementar uma task por vez: mudança cirúrgica, teste derivado da spec, gate, commit atômico quando autorizado. Verificação está dentro de cada task.

## Antes da primeira task

1. **Pré-requisito:** `tasks.md` commitado, ou o plano inline apresentado e aprovado quando Tasks foi dispensada. "Implementa" autoriza editar os arquivos da mudança; commit é autorização própria, dada uma vez por mudança (SKILL.md, Autorizações).
2. **Contexto:** leia a task, o trecho do design que ela referencia e os requisitos da spec que ela atende. Não carregue outras mudanças.
3. **`[LACUNA]` no caminho:** decida e registre dentro da autonomia concedida; ou `[PREMISSA]` com default e racional na spec; ou pergunte ("O design tem uma lacuna: […]. Opções: […]. Recomendo […].") e execute só o que não depende dela. Nunca em silêncio, nunca por silêncio.

**Plano inline** (quando Tasks foi dispensada), antes de qualquer código:

```
## Plano
Requisitos (só sem spec.md): - **XYZ-01** — WHEN … THEN the system SHALL …
Estrutura: [uma ou duas linhas: onde entra, o que reusa]
Gate: [comando de build e teste do repositório]
1. [passo] → arquivos: […] → verifica: [como]
2. …
```

Cada passo é um entregável coeso (tasks.md, Task atômica). Se a lista passar de cinco passos ou revelar dependência não trivial ou risco nomeado, pare e crie o artefato que faltou; é a catraca subindo.

## Ciclo por task

1. **Escolher.** A task indicada ("faz a T3") ou a próxima disponível. Dependência não concluída: pergunte antes.
2. **Declarar o plano** em três linhas: arquivos (só os da task), abordagem, como vai verificar. Se enxerga abordagem mais simples que a do design ou discorda dele, diga antes, não depois.
3. **Testes derivados da spec.** Cada requisito da task tem ao menos uma assertion cujo valor é o resultado que a spec define (status, mensagem, estado, evento). Spec sem resultado preciso é lacuna de precisão: volte à spec, não escreva assertion vaga. Teste de comportamento novo falha antes do código; teste de caracterização (comportamento preservado) passa antes e depois. Teste que parece errado contra a spec: pare e confirme; os testes são a spec executável.
4. **Implementar** o mínimo que satisfaz a task. Nada além do pedido; sem abstração de uso único; sem flexibilidade não solicitada; sem tratar cenário impossível. Não "melhore" código adjacente nem formatação; siga o estilo existente mesmo discordando. Problema vizinho (bug, dívida, dead code) é reportado, não corrigido. Arquivo indispensável descoberto (registro, config) entra em `Onde` com nota.
5. **Gate.** Rode o comando do nível da task (Comandos de Gate, ou o gate do plano inline). Exit diferente de zero: corrija e rode de novo. Gate que não pode rodar (SDK ausente, dependência indisponível) não é gate verde: a task fica bloqueada com o motivo.
6. **Revisão pós-gate.** `Pronto quando` atendido, inclusive os critérios de comportamento; nenhum `SPEC_DEVIATION` sem registro; "um sênior chamaria isso de complicado demais?" (se sim, simplifique e rode o gate de novo); tabela critério → `file:line` + assertion, e o inverso: todo teste novo mapeia para um critério, requisito ou edge case.
7. **Fechar.** Marque a task no `tasks.md` (ou no plano). Com commit autorizado, um commit só com os arquivos da task e o `tasks.md`, no formato que o repositório convenciona; se o repositório tem validação de mensagem, rode-a antes. Sem commit autorizado, a task fecha com gate verde e arquivos na árvore de trabalho.

## Refine o contexto, não o erro

Spec ou design errados (regra impossível, contrato inconsistente, restrição da base não prevista) param a task: "Encontrei uma restrição não prevista: […]. Isso invalida [spec/design] em […]. Recomendo corrigir lá e re-derivar [tasks afetadas]." Regra de negócio errada volta ao PRD antes da spec. Desvio local que não invalida o artefato recebe marcador no código e linha em `## Desvios` do `tasks.md` (seção criada no primeiro desvio):

```
// SPEC_DEVIATION: [o que divergiu]
// Reason: [por quê]
```

## Segurança

Pacote novo é sugestão até validar a procedência no registro oficial: "Sugiro `[nome]`; antes de instalar, confirme em […]". Pacotes inventados existem e são publicados maliciosamente. Segredo, connection string ou dado de produção encontrado na base nunca entra no output; sinalize como risco.

## Depois da última task

Verify (verify.md), com olhos frescos. Um branch aberto e o `git log` são o handoff; retomar é ler o `tasks.md` e o `git status`: task só conta como concluída com gate verde registrado, e `git status` é indício de progresso, não prova.
