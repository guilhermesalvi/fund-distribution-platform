# ADR

Uma decisão é **de projeto** quando fixa convenção, restrição ou padrão que features futuras devem seguir (estilo arquitetural, transporte de eventos, forma de persistência compartilhada, política de versionamento). Decisão local à feature fica na tabela de Decisões técnicas do design. Gatilhos explícitos: "registre essa decisão", "isso é decisão de projeto", "daqui em diante sempre…".

A ADR guarda o porquê que código e diagrama não guardam. Sem alternativas consideradas e consequências, a IA re-propõe caminhos já descartados e o time re-litiga o que já foi pago. Os participantes entram porque decisão de arquitetura raramente é de uma pessoa, e o nome é o que responde "por que fizemos assim?" depois do turnover.

## Arquivo

`docs/adr/NNNN-<slug>.md`, com `NNNN` = max+1 lendo a pasta. Projeto que já tem formato ou diretório de ADR mantém o seu; esta skill não cria formato paralelo.

```markdown
# ADR 0007: Eventos de domínio saem por outbox transacional

Participantes: quem decidiu; quem foi consultado.

## Contexto
[Situação e restrições que forçaram a decisão; o que estava em jogo.]

## Decisão
[Uma frase: o que faremos.]

## Alternativas consideradas
| Alternativa | Por que rejeitada |
|---|---|

## Consequências
- Positivas: …
- Negativas: … (o custo aceito; ADR sem consequência negativa é decisão não examinada)

## Regras derivadas
[Regra em CLAUDE.md, rules ou linter que existe por causa desta ADR, com o path. Presente quando há regra.]
```

## Conformar e superseder

- Todo Design lê as ADRs ativas antes de projetar; decisão ativa é restrição. Conflito é conformar ou superseder, nunca ignorar.
- Superseder: ADR nova com a linha `Substitui: NNNN` abaixo do título; a antiga ganha `Substituída por: NNNN` no mesmo lugar e nada mais muda. Nunca apague uma ADR.
- Regra de projeto que a mudança cria ou altera (CLAUDE.md, rules, linter) cita a ADR ou o princípio que a justifica; regra sem porquê é seguida cegamente ou ignorada.
