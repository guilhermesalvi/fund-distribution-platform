# Registro de decisão arquitetural

Registre o contexto, a escolha, as alternativas e os custos de uma decisão que estabelece uma convenção para futuras mudanças. Decisão local à capacidade pertence ao design.

## Destino e conteúdo

Use o formato e diretório já estabelecidos no projeto. Na ausência, salve em `docs/adr/NNNN-<slug>.md`, com o próximo número da pasta e slug em inglês kebab-case.

Consulte os ADRs pertinentes e a convenção escrita. Exemplos existentes ajudam a manter consistência, mesmo quando há poucos; não exija uma quantidade mínima para adotar seu formato.

Registre participantes reais, incluindo quem decidiu e quem foi consultado. Quando desconhecidos, use `[GAP]`; não atribua autoria ou consulta fictícia. A decisão pode ser tomada dentro da autonomia técnica da tarefa, conforme [workflow.md](workflow.md).

## Modelo

Substitua os campos explicativos pelos fatos da decisão. Os títulos e rótulos técnicos ficam em inglês.

```markdown
# ADR 0007: Publicação de eventos por outbox transacional

Participants: [GAP] Participantes ainda não informados.

## Context

Descreva o problema e as restrições que justificam a decisão.

## Decision

Declare a escolha e seu alcance.

## Alternatives considered

| Alternativa | Motivo de rejeição |
|---|---|
| Alternativa realmente avaliada | Critério que favoreceu a escolha |

## Consequences

- Positive: benefício concreto.
- Negative: custo aceito.

## Derived rules

- Regra estabelecida pela decisão — `CLAUDE.md` ou `.claude/rules`
```

O título e a escolha do exemplo não indicam adoção pelo projeto. No artefato real, não invente alternativa ou custo para preencher a forma. Se não houver alternativa viável, explique o motivo em `Alternatives considered`, sem tabela artificial.

`Context`, `Decision`, `Alternatives considered` e `Consequences` são obrigatórias, nessa ordem. `Derived rules` entra por último apenas quando a decisão criar ou mudar regras; cada item indica o caminho onde a regra vive.

## Conformidade e substituição

Um ADR ativo é restrição para o design pertinente. Se conflitar com a solução escolhida, siga-o ou registre sua substituição dentro da autorização disponível.

Para substituir, crie outro ADR com `Supersedes: NNNN` abaixo do título. No anterior, acrescente `Superseded by: NNNN` no mesmo local e preserve o restante. As referências são recíprocas; não apague o histórico.

Regras derivadas em `CLAUDE.md` ou em `.claude/rules` citam o ADR ou princípio que as justifica. Revise conforme [validation.md](validation.md).
