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

### Forma de escrita

No Contexto, indique o problema e as restrições. Na Decisão, declare a escolha em ordem direta. Nas alternativas, explique por que cada opção realmente avaliada foi descartada usando os critérios da decisão. Nas consequências, descreva benefícios e custos concretos. Preserve participantes, referências de substituição e paths das regras derivadas. Não acrescente alternativa fictícia nem custo genérico para completar o formato.

## Arquivo

Grave em `docs/adr/NNNN-<slug>.md`. Obtenha `NNNN` listando `docs/adr` e somando 1 ao maior número (validation.md, Numeração).

Projeto que já tem formato ou diretório de ADR mantém o seu; esta entrada não cria formato paralelo. O formato do projeto é convenção quando aparece em pelo menos três ADRs commitadas ou está escrito no guia do repositório (validation.md, Forma mantida por pedido ou convenção). Os achados de forma que decorrem dela se mantêm e são relatados.

Para reconhecer uma convenção por exemplos, use a versão dos arquivos presente em HEAD. Liste os arquivos com `git ls-tree -r --name-only HEAD -- docs/adr` (ou o diretório efetivamente convencionado) e filtre os Markdown que são ADRs. Leia cada exemplo com `git show "HEAD:<caminho>"`. A convenção precisa aparecer em pelo menos três desses exemplos. Um arquivo apenas staged ou untracked não conta. Uma alteração local em arquivo já commitado também não altera a convenção de HEAD. Se HEAD não existir, não há convenção comprovada por exemplos; a convenção escrita no guia do repositório continua sendo uma fonte válida.

Com uma ou duas ADRs em formato próprio e sem convenção escrita, pergunte qual formato vale antes de gravar; sem resposta, grave no formato desta entrada. Pedido da sessão que nomeia literalmente a seção, o campo ou a forma isenta do mesmo modo, sem contagem (validation.md, Forma mantida por pedido ou convenção).

Template completo com campos substituíveis: preencha-os com a decisão real. Participantes, alternativas e custos desconhecidos não devem ser inventados; um campo instrucional deste template não é um placeholder permitido no artefato entregue.

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
- [regra que existe por causa desta ADR] — `AGENTS.md`
```

As seções da ADR são as do template, e a lista é fechada: a checagem de forma acusa a seção `##` fora dela (validation.md, Checagem de forma). Em inglês (workflow.md, Idioma) os headings são `Context`, `Decision`, `Alternatives considered`, `Consequences` e `Derived rules`.

## Antes de apresentar

Faça a checagem de forma (validation.md, Checagem de forma); depois percorra a lista fechada da entrada ADR (validation.md, Revisão por entrada) e apresente.

## Conformar e superseder

- **Ler antes de projetar.** Todo Design lê as ADRs ativas antes de projetar; decisão ativa é restrição. Quando o melhor para a feature conflita com uma ADR ativa, a saída é conformar ou superseder, nunca ignorar.
- **Como superseder.** Crie uma ADR nova com a linha `Substitui: NNNN` abaixo do título. Na ADR antiga, adicione `Substituída por: NNNN` no mesmo lugar (abaixo do título) e não altere mais nada nela. Nunca apague uma ADR.
- **Regra derivada cita a ADR.** Regra de projeto que a mudança cria ou altera (em AGENTS.md ou docs/development) cita a ADR ou o princípio que a justifica. Regra sem porquê é seguida cegamente ou ignorada.
- **Regra derivada tem path.** Cada regra da seção `## Regras derivadas` é um bullet e traz, entre crases, o path do arquivo onde a regra vive — `AGENTS.md`, `docs/development/tracing.md`. Regra sem path não é localizável e não é seguida; a checagem de forma acusa a seção sem bullet e o bullet sem path. A seção existe só quando a decisão cria ou altera regra.

### Exemplo didático parcial de reescrita

Fragmento de escrita; não é um artefato completo nem evidência de uma execução real.

```text
Antes: Foi tomada a decisão de que a publicação dos eventos de domínio
será realizada por meio de outbox transacional.

Depois: Os eventos de domínio serão publicados por outbox transacional.

Preservado: a escolha demonstrada no título do template existente.
O par não afirma que essa ADR foi adotada pelo projeto.
```
