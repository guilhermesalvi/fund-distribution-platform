# Especificação técnica

Defina comportamento testável e rastreável. A spec é o contrato que o design realiza e os testes verificam. Regras de negócio ficam no PRD.

## Layout e versão

```text
/docs/specs/<domain-slug>/<capability-slug>/
    spec.md
    NNNN-<change-slug>/
        design.md
        tasks.md
/docs/adr/NNNN-<slug>.md
```

Use slugs em inglês kebab-case. O contador de mudança é local à capacidade: maior número existente mais um, começando em 0001. Crie uma pasta de mudança apenas quando houver design ou tarefas. Uma convenção explícita de destino prevalece.

Edite `spec.md` no mesmo arquivo. Git registra o histórico; o documento não recebe campos de status, autoria, data ou aprovação. A versão de trabalho é válida para derivação e verificação, conforme [workflow.md](workflow.md).

A primeira linha é o comentário de máquina:

```text
<!-- sdd: spec | capability: offering/offer-lifecycle -->
<!-- sdd: design | spec: ../spec.md -->
<!-- sdd: tasks | spec: ../spec.md | design: ./design.md -->
```

Campos condicionais:

- Na spec com PRD, acrescente `| prd: /docs/prd/<arquivo>.md | prd-rev: git:<hash>`. Calcule o hash com `git hash-object <caminho-do-prd>` sobre o arquivo usado, mesmo sem commit.
- Se o PRD mudar, examine os requisitos e cenários afetados antes de atualizar o hash. Igualdade de hash não prova interpretação correta.
- Em design e tarefas parciais, acrescente `| scope: RSV-01, RSV-02` com os IDs abrangidos.
- Inclua `design:` nas tarefas apenas quando o design existir.

Após o título, use `Requirement prefix: ` seguido do prefixo entre crases e ponto final.

## Origem e rastreabilidade

| Origem | Tratamento |
|---|---|
| PRD | Preserve regras, IDs, glossário, decisões e tags; descreva a realização técnica |
| Ideia com usuário e resultado | Registre os fatos recebidos e as lacunas; não invente negócio |
| Pedido apresentado como tela ou CRUD | Extraia o comportamento pelo contexto; sinalize a necessidade de definição de produto se ela for indispensável |
| Código existente | Descreva o que faz; intenção inferida é `[ASSUMPTION]`; divergências têm `arquivo:linha` |

Leia a spec existente, o PRD pertinente e os ADRs que restringem a capacidade. Consulte o módulo afetado e exemplos relevantes de contratos e testes.

Quando houver PRD:

- Cite o ID de negócio no requisito EARS que o realiza, sem copiar a regra em outra definição normativa.
- Preserve hipóteses herdadas e sua origem. Uma nova escolha técnica não resolve uma lacuna de negócio.
- Use prefixo técnico distinto dos prefixos de PRD e de suas duas primeiras letras para reduzir confusão, como `RSV` em vez de `OFR` ao lado de `OFF`.
- Consulte PRD 0000 para contexto, eventos e decisões delegadas a ADR.
- NFR com resultado observável vira requisito. Qualidade sem teste direto entra na rastreabilidade com `Design criterion:`.
- Liste os cenários de aceitação em escopo por nome, com os IDs técnicos correspondentes. Eles são casos mínimos da implementação. Itens de outra capacidade usam `Outside this capability:` e indicam o dono.

## Precisão e dúvidas

Resolva escolhas técnicas conforme a autonomia em [workflow.md](workflow.md). Perguntas devem tratar de informação indispensável; não repita o que o PRD, o código ou o usuário já decidiu.

Examine dimensões pertinentes: limites de entrada, falha parcial, idempotência, autorização, concorrência, ciclo de vida dos dados, observabilidade, dependências externas, transições e consistência entre contextos. Escreva somente as que gerarem requisitos ou lacunas reais.

## Requisitos EARS

As palavras-chave são fixas; condição e resposta ficam em português.

| Padrão | Forma |
|---|---|
| Geral | `The system SHALL <resposta>` |
| Evento | `WHEN <gatilho> THEN the system SHALL <resposta>` |
| Estado | `WHILE <estado> the system SHALL <resposta>` |
| Funcionalidade opcional | `WHERE <funcionalidade presente> the system SHALL <resposta>` |
| Comportamento indesejado | `IF <condição indesejada> THEN the system SHALL <resposta>` |
| Composto | `WHILE <estado>, WHEN <gatilho> the system SHALL <resposta>` |

Cada requisito tem um ID `<PREFIX>-nn`, um `SHALL` e uma resposta observável. Medidas, estados, erros e prazos vêm das fontes ou de decisão técnica autorizada; não acrescente números só para preencher a forma.

Separe obrigações que podem falhar independentemente. Mantenha condição conjunta e efeito indivisível na mesma unidade. Aceitar entrada válida e tratar entrada inválida são cenários distintos.

## Evolução e seções

Mantenha o ID ao ajustar seu significado dentro do mesmo conceito. Ao substituir um conceito ou remover requisito, aposente o ID e liste-o ao fim: `Retired: RSV-05, RSV-09`. Não recicle IDs; saltos de numeração correspondem a IDs aposentados. Refatoração sem mudança de comportamento cita os requisitos preservados.

Títulos `##` permitidos, nesta ordem; seções opcionais exigem conteúdo:

| Título | Conteúdo |
|---|---|
| Context | Obrigatório: origem, contexto lido, comportamento e integrações pertinentes |
| Scope / Out of Scope ou Scope | Escopo e exclusões justificadas |
| Assumptions | Hipótese, padrão e justificativa, com tag |
| Open Questions | Lacuna, responsável e dependência; maior bloqueio primeiro |
| Requirements | Obrigatório: lista EARS; subtítulos por tema quando facilitarem a leitura |
| Domain Events | Produtor, consumidores, significado, gatilho |
| Glossary | Termos técnicos; termos de negócio apontam para o PRD |
| Traceability | Obrigatório com PRD: FRs, NFRs e cenários pertinentes mapeados aos IDs técnicos |
| Divergences | Na origem por código: comportamento divergente, com evidência |

Uma seção herdada do PRD ou exigida pela convenção pode ser preservada com justificativa. Valide a forma e o conteúdo conforme [validation.md](validation.md).

## Exemplo didático

Fragmento completo de spec sem PRD, com comportamento fornecido para o exemplo; não define decisão deste projeto.

```markdown
<!-- sdd: spec | capability: examples/quantity-validation -->
# Validação de quantidade

Requirement prefix: `QTY`.

## Context

O consumidor precisa distinguir quantidades positivas de entradas inválidas.
Neste exemplo, a quantidade é um número inteiro.

## Requirements

- **QTY-01** — WHEN o consumidor informa quantidade maior que zero THEN the system SHALL retornar a quantidade informada
- **QTY-02** — IF a quantidade for menor ou igual a zero THEN the system SHALL retornar o erro `INVALID_QUANTITY`
```
