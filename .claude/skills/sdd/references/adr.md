# ADR

**Objetivo:** registrar uma decisão de projeto com o contexto, as alternativas consideradas e as consequências, para que o porquê sobreviva ao código, ao diagrama e ao turnover.

## Quando a decisão é de projeto

Uma decisão é **de projeto** quando fixa convenção, restrição ou padrão que features futuras devem seguir. Exemplos:

- estilo arquitetural;
- transporte de eventos;
- forma de persistência compartilhada;
- política de versionamento.

Decisão local à feature não vira ADR; quem fixa o destino dela é o design (design.md, Decisões técnicas).

Gatilhos explícitos do usuário que pedem uma ADR: "registre essa decisão", "isso é decisão de projeto", "daqui em diante sempre…".

## O que a ADR guarda

- **O porquê.** A ADR guarda o que código e diagrama não guardam: a razão da decisão.
- **Alternativas consideradas e consequências.** Sem elas, a IA re-propõe caminhos já descartados e o time re-litiga o que já foi pago.
- **Participantes.** Decisão de arquitetura raramente é de uma pessoa; o nome de quem decidiu e de quem foi consultado é o que responde "por que fizemos assim?" depois do turnover. É conteúdo da decisão, não campo de autoria do arquivo (specify.md, Versionamento).

## Arquivo

Grave em `docs/adr/NNNN-<slug>.md`. Obtenha `NNNN` com `seq.py next docs/adr --slug <slug>`, nunca lendo a pasta; `seq.py check docs/adr` acusa duplicata (SKILL.md, Scripts).

Projeto que já tem formato ou diretório de ADR mantém o seu; esta entrada não cria formato paralelo. O formato do projeto é convenção quando aparece em três ou mais ADRs commitadas — conte com `git ls-files 'docs/adr/*.md'`, ou o glob do diretório que o projeto usa (SKILL.md, Scripts) — e então os HARD de `lint_adr.py` que decorrem dele não se corrigem nem contam rodada. Com uma ou duas ADRs em formato próprio não há convenção: pergunte qual formato vale antes de gravar, e sem resposta grave no formato desta entrada. Pedido da sessão que nomeia literalmente a seção, o campo ou a forma isenta do mesmo modo, sem contagem (SKILL.md, Scripts).

### Template

```markdown
# ADR 0007: Eventos de domínio saem por outbox transacional

Participantes: [quem decidiu]; [quem foi consultado].

## Contexto
[Situação e restrições que forçaram a decisão; o que estava em jogo.]

## Decisão
[Uma frase: o que faremos.]

## Alternativas consideradas
| Alternativa | Por que rejeitada |
|---|---|
| [alternativa avaliada] | [o que a derrubou, contra os mesmos critérios] |

## Consequências
- Positivas: [o que a decisão compra]
- Negativas: [o custo aceito; ADR sem consequência negativa é decisão não examinada]

## Regras derivadas
- [regra que existe por causa desta ADR] — `CLAUDE.md`
```

As seções da ADR são as do template, e a lista é fechada: `lint_adr.py` acusa como HARD a seção `##` fora dela. Em inglês (SKILL.md, Idioma) os headings são `Context`, `Decision`, `Alternatives considered`, `Consequences` e `Derived rules`.

## Antes de apresentar

Rode `lint_adr.py <adr.md>` e siga o ciclo de correção de SKILL.md, Scripts; depois percorra a lista fechada da entrada ADR (SKILL.md, Revisão por entrada) e apresente.

## Conformar e superseder

- **Ler antes de projetar.** Todo Design lê as ADRs ativas antes de projetar; decisão ativa é restrição. Quando o melhor para a feature conflita com uma ADR ativa, a saída é conformar ou superseder, nunca ignorar.
- **Como superseder.** Crie uma ADR nova com a linha `Substitui: NNNN` abaixo do título. Na ADR antiga, adicione `Substituída por: NNNN` no mesmo lugar (abaixo do título) e não altere mais nada nela. Nunca apague uma ADR.
- **Regra derivada cita a ADR.** Regra de projeto que a mudança cria ou altera (em CLAUDE.md, rules ou linter) cita a ADR ou o princípio que a justifica. Regra sem porquê é seguida cegamente ou ignorada.
- **Regra derivada tem path.** Cada regra da seção `## Regras derivadas` é um bullet e traz, entre crases, o path do arquivo onde a regra vive — `CLAUDE.md`, `.claude/rules/tracing.md`, o linter. Regra sem path não é localizável e não é seguida; `lint_adr.py` acusa como HARD a seção sem bullet e o bullet sem path. A seção existe só quando a decisão cria ou altera regra.
