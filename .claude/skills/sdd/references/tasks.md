# Planejamento das tarefas

Decomponha a mudança em entregas coesas, verificáveis e rastreáveis. Use spec e design atuais; salve em `<capability>/NNNN-<change-slug>/tasks.md`, conforme [specify.md](specify.md). Sem design separado, explique a estrutura no início.

## Descoberta de testes

Leia as instruções aplicáveis, configuração de projetos e comandos de CI pertinentes. Examine testes representativos das camadas alteradas, ampliando a amostra se houver padrões diferentes. Exemplos orientam estilo; não obrigam toda tarefa a executar os mesmos níveis de teste.

Sem testes existentes, escolha uma verificação adequada ao comportamento e ao ambiente dentro da autonomia da tarefa. Pergunte apenas se faltar decisão indispensável. Não invente framework, pacote ou comando.

Regras de domínio e caminhos de erro exigem evidência de comportamento. Configuração e documentação podem ser verificadas por build, analisador, renderização ou script apropriado. Build não prova regra de negócio.

Registre antes de `Gate Commands` como o repositório testa, as fontes dos comandos e a linha de base observada, quando disponível. Uma contagem de testes ausente deve ser declarada como não medida.

## Comandos de verificação

O nome do gate é um contrato, com capitalização exata:

| Gate | Finalidade |
|---|---|
| quick | Verificação focada no comportamento alterado |
| full | Suíte abrangente pertinente à integração ou ao risco |
| build | Build, analisadores e verificações finais exigidos pelo projeto |
| Mutation | Mutation testing com escopo justificado; não é valor do campo Gate de tarefa |

No artefato, use tabela `Gate | When | Command`, com comandos reais e completos. Inclua somente os gates necessários, mas todo `Gate` usado por uma tarefa precisa de linha correspondente.

O campo `Tests` descreve testes escritos ou alterados; `Gate` descreve o comando executado. Escolha o gate pelo risco, pelos critérios de conclusão e pela convenção do projeto. A última tarefa de uma fase não exige repetição automática da suíte inteira. Na conclusão, execute as verificações finais ainda não comprovadas para a versão atual.

Mutation testing solicitado ou escolhido como mitigação tem comando e escopo explícitos, conforme [verify.md](verify.md).

## Campos e coesão

Cada tarefa `Tn` inclui implementação, testes pertinentes e registro necessário para integrar a mesma entrega. Separe resultados independentes; mantenha juntas partes que precisam umas das outras para serem verificáveis.

| Campo fixo | Conteúdo |
|---|---|
| What | Entrega concreta |
| Where | Caminhos reais, distinguindo criação e alteração |
| Depends on | IDs de tarefas anteriores no plano, ou `none` |
| Requirement | IDs da spec satisfeitos ou preservados |
| Interfaces | `Consumes` e `Produces`: contratos, tipos, erros e parâmetros pertinentes |
| Done when | Critérios observáveis e comando do gate em item separado |
| Tests | `unit`, `integration`, `e2e`, em lista, ou `none` com justificativa |
| Gate | `quick`, `full` ou `build` |

Em `Done when`, copie o comando da linha do gate entre crases, sem substituir por outro comando. Critérios de comportamento citam o requisito e seus valores esperados; alterações sem comportamento têm critério estrutural apropriado.

Uma tarefa não delega vagamente seus testes para “depois”. Se depender de integração futura para ser verificável, reorganize a entrega. Interfaces devem ser compreensíveis sem ler outras tarefas; spec e design continuam fontes do contrato.

## Seções e dependências

Use estes títulos `##`:

- `Gate Commands`: tabela de comandos.
- `Execution Plan`: fases coesas e tarefas em ordem de dependência.
- `Tasks`: corpo das tarefas.
- `Traceability`: requisitos mapeados às tarefas; correspondência nos dois sentidos.
- `Deviations`: criada apenas quando houver desvio.
- `Correction Tasks`: correções `TCn` identificadas na verificação, fora do plano original.

Dependências apontam para trás, sem ciclos. Tarefa original não depende de correção posterior; correções podem depender das originais ou de correções anteriores. Todo requisito em escopo tem tarefa, e toda tarefa cita um requisito pertinente.

## Exemplo didático

Este fragmento completo de formato usa QTY-01 e QTY-02 de [specify.md](specify.md). Os caminhos e comandos pressupõem o repositório fictício do exemplo; não são evidência de execução.

```markdown
<!-- sdd: tasks | spec: ../spec.md | design: ./design.md | scope: QTY-01, QTY-02 -->
# Validação de quantidade — tarefas

O exemplo usa xUnit em `tests/UnitTests`. A contagem inicial não foi medida.
A conclusão da implementação inclui os checks finais exigidos pelo repositório.

## Gate Commands

| Gate | When | Command |
|---|---|---|
| quick | T1 | `dotnet test tests/UnitTests` |

## Execution Plan

T1

## Tasks

### T1: Criar a validação de quantidade
- **What:** validar quantidade inteira com testes de aceitação e erro.
- **Where:** criar `src/Examples/QuantityValidator.cs` e `tests/UnitTests/QuantityValidatorTests.cs`.
- **Depends on:** none
- **Requirement:** QTY-01, QTY-02
- **Interfaces:**
  - Consumes: `int quantity`
  - Produces: `Validate(int quantity): QuantityResult`, que contém o valor aceito ou o erro.
- **Done when:**
  - [ ] Quantidade 1 retorna 1 (QTY-01).
  - [ ] Quantidades 0 e -1 retornam `INVALID_QUANTITY` (QTY-02).
  - [ ] Verificação aprovada: `dotnet test tests/UnitTests`.
- **Tests:** unit
- **Gate:** quick

## Traceability

| Requirement | Tasks |
|---|---|
| QTY-01 | T1 |
| QTY-02 | T1 |
```

Revise a consistência com [validation.md](validation.md) e entregue conforme o escopo e a autorização em [workflow.md](workflow.md).
