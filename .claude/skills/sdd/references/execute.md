# Execução

Implemente as entregas autorizadas, com evidência de conclusão. As decisões e autorizações seguem [workflow.md](workflow.md).

## Antes da implementação

Leia a tarefa, os requisitos citados e o trecho pertinente do design. Confira o estado dos arquivos e preserve alterações alheias.

Registre a base antes da primeira edição de código: `git rev-parse HEAD`. Use a linha `Base: <hash>` no texto inicial de `tasks.md` ou `; base: <hash>` no plano da conversa. Essa base identifica o começo da mudança; não é exigência de commit intermediário. Sem histórico, identifique os arquivos iniciais e informe a limitação de comparação.

Quando não houver `tasks.md`, apresente um plano concreto antes de editar. Em implementação autorizada, a apresentação é atualização de progresso:

```text
Requirements: IDs abrangidos
Structure: caminhos e componentes reutilizados
Gate: comandos de verificação; base: hash
1. Entrega → arquivos → critério de conclusão
```

Inclua `; mutation: <comando>` quando mutation testing fizer parte da verificação. Os campos são fixos; substitua valores ilustrativos antes de usar.

## Ciclo por entrega

1. Escolha a próxima tarefa cujas dependências estejam satisfeitas. Um pedido explícito por tarefa fora de ordem exige resolver as dependências dentro do escopo ou explicar a limitação.
2. Informe entrega, abordagem e verificação. Se uma alternativa técnica for melhor dentro da autonomia concedida, atualize o design e os dependentes antes de aplicá-la.
3. Escreva ou ajuste os testes pertinentes. Resultados esperados vêm da spec e dos cenários herdados do PRD. Teste de comportamento novo deve demonstrar a falha antes da correção quando viável; teste de caracterização comprova comportamento preservado.
4. Implemente a solução suficiente. Evite opções sem consumidor e abstrações sem necessidade. Inclua arquivos indispensáveis descobertos em `Where`, com motivo.
5. Execute o gate declarado e examine a saída. Corrija falhas causadas pela alteração sem enfraquecer critérios. Repita quando houver mudança, hipótese nova ou evidência que justifique a tentativa.
6. Revise os critérios de conclusão e a correspondência entre requisitos e testes. Simplifique apenas com justificativa; após mudar código, renove a evidência afetada.
7. Marque `Done when` como concluído somente para critérios demonstrados. Agrupe commits por motivo se estiverem autorizados; a ausência de commit não impede concluir a entrega local.

Continue enquanto houver progresso verificável e correção autorizada. Repetir o mesmo comando sem mudança nem hipótese não é progresso. Quando faltar recurso ou decisão indispensável, conclua as partes independentes e relate o bloqueio, sem atribuir aprovação a checks não executados.

## Correções e desvios

Uma asserção que contradiz a fonte exige examinar a causa: corrija o teste se o contrato for inequívoco; uma regra de negócio ambígua volta ao PRD. Não crie uma obrigação de pergunta quando a evidência já resolver.

Mudança de comportamento precisa aparecer no artefato que a define antes de atualizar os dependentes. Decisões técnicas delegadas não exigem nova aprovação.

Desvio local que preserve comportamento fica em `Deviations` do plano, com localização e justificativa. Quando um marcador no código for útil à manutenção, use o contrato:

```text
// SPEC_DEVIATION: description
// Reason: rationale
```

Os comentários de código seguem o inglês do projeto. Não use o marcador para legitimar divergência de negócio nem para registrar um arquivo de integração já justificado em `Where`.

Ao adicionar dependência, confirme nome, origem e compatibilidade em fonte oficial e siga a autorização da tarefa. Não exponha segredos encontrados durante a inspeção.

## Conclusão e verificação

Na conclusão da implementação, confirme que os testes usam os requisitos atuais, inclusive alterações locais. Identifique a spec por caminho e `git hash-object <spec>`; se houver PRD, confira também `prd-rev`.

Execute os checks finais exigidos pelo repositório que ainda não tenham evidência para essa versão. Uma execução anterior serve quando arquivos, configuração, comando e dependências relevantes permanecem os mesmos; registre a origem da evidência. Build e testes distintos não são intercambiáveis.

Passe à verificação de [verify.md](verify.md). Entregue resultado, evidências, verificações realizadas e limitações materiais. Não encerre uma implementação ainda verificável apenas porque produziu o código.

## Retomada

Recupere o pedido, o plano, os requisitos, decisões e autorizações; compare-os com os arquivos atuais. Checkboxes e `git status` indicam progresso, mas não provam que a versão atual foi verificada.

Sem plano disponível, reconstrua-o com fatos do repositório e continue dentro da autorização existente. Não invente contagens, comandos ou base histórica. Falta de base limita atribuição de regressão, sem impedir inspecionar e testar o estado atual.
