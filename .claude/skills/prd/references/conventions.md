# Convenções do PRD

## Gravar

### Caminho e numeração

- O path é `/docs/prd/NNNN-<domain-slug>-<feature-slug>.md`, com slug em kebab-case em inglês e sem prefixo `prd-`.
- `NNNN` é um contador de 4 dígitos, global na pasta, porque dá referência curta ("PRD 0007") e registra a ordem de chegada. Obtenha o número listando os `NNNN-*.md` da pasta e somando 1 ao maior; pasta sem PRD começa em 0001. A exceção é o PRD 0000, cujo número é fixo e não passa pelo contador.
- `0000-<slug>-overview.md` é o PRD 0000 (writing.md, PRD 0000); visão geral gravada em qualquer outro número é achado da checagem de forma (workflow.md, Checar).
- O contador colide quando dois PRs paralelos alocam o mesmo número; a checagem de forma acusa a duplicata (workflow.md, Checar). Renumere o PRD do branch cujo merge acontece depois: mova o arquivo para o próximo número livre da pasta, atualize quem o cita e confira a numeração de novo.
- Sem repositório, use o mesmo layout sob o diretório de trabalho atual e diga no chat o caminho gravado.

### Edição no lugar

- O PRD se edita no lugar: o diff é a mudança, e o `git log` é autor, data e histórico.
- O PRD não tem campo de status, autor, data, confiança ou aprovação, e não é substituído por um arquivo com número novo.

### Header

O header tem estes elementos, nesta ordem:

1. A primeira linha é `# Título`.
2. Abaixo, uma tabela de duas colunas com um único campo, `Originating Context`. O valor é o contexto primário, seguido de `; affects <contextos>` quando houver, com os contextos separados por vírgula; o impacto em cada contexto afetado vai a Dependencies and Risks. Se DDD não se aplica, o rótulo é `Module` ou `Area`; a lista é fechada nesses três, e no PRD 0000 só `Scope`.
3. Depois, a linha de prefixo dos requisitos (writing.md, IDs), com o rótulo fixo `Requirement prefix:`.
4. Na mesma linha do prefixo, a frase que aponta o PRD 0000, quando ele existe.

O PRD 0000 difere em três pontos: usa `Scope` no lugar de `Originating Context`, não tem linha de prefixo e carrega `<!-- prd: overview -->` na primeira linha, por ser o único PRD com forma própria. Nenhum outro comentário de máquina entra em PRD algum.

O rótulo do campo é fixo em inglês (Idioma); o nome do contexto preserva o termo do domínio.

```markdown
# Verificação Assíncrona de Documentos

| | |
|---|---|
| **Originating Context** | Customer Onboarding; affects Account Activation |

Requirement prefix: `ONB`. Propósito da plataforma, mapa de contextos, catálogo de eventos e fluxos: [PRD 0000](0000-platform-overview.md).
```

## Idioma

- **Estrutura em inglês, prosa no idioma do PRD.** A estrutura é o que a checagem de forma lê, e tem uma única forma, em inglês: os headings `##` (writing.md, Seções e PRD 0000), os rótulos do header e a linha de prefixo (Header), as tags `[ASSUMPTION]` e `[GAP]` (writing.md, Tags), os rótulos de forma `*Cost:*` e `*Reason:*`, `Guardrail`, `**Given**`/`**when**`/`**then**`, `if false`, `; affects` e a coluna `Identifier` (writing.md, Seções). Heading ou rótulo traduzido é achado da checagem de forma (workflow.md, Checar), mesmo em PRD escrito em português.
- **O idioma da prosa** segue a precedência (SKILL.md, Limites). Quando ninguém o fixou, é o idioma do material recebido (com material em mais de um idioma, o do documento que o pedido cita primeiro ou, sem citação, o do primeiro anexo); sem material, o idioma do pedido. Uma vez fixado, pedido explícito de idioma na sessão é precedência e o muda; mensagem em outro idioma sem esse pedido não muda. Qualquer idioma serve para a prosa, porque a checagem de forma não a lê.
- Termo canônico em inglês sem tradução de mesma força fica em inglês na prosa: Factory Pattern, Entity Service Antipattern, Bounded Context, Domain Event, Ubiquitous Language, JTBD, MoSCoW, guardrail, leading/lagging, trade-off. Fora dessa lista, traduza o termo só quando a tradução já aparece no material recebido ou no PRD 0000; caso contrário, mantenha o original em inglês.
- Identificadores de domínio (`Offering`, `ReservationBook`), IDs e tags não se traduzem. O termo de domínio continua no original (writing.md, Ubiquitous Language).
