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
2. Abaixo, uma tabela de duas colunas com um único campo, `Contexto Originário` (`Originating Context` em PRD em inglês). O valor é o contexto primário, seguido de `; afeta <contextos>` quando houver; o impacto em cada contexto afetado vai a Dependências e Riscos. Se DDD não se aplica, o rótulo é `Módulo` (`Module`) ou `Área` (`Area`); a lista é fechada nesses três, e no PRD 0000 só `Escopo` (`Scope`).
3. Depois, a linha de prefixo dos requisitos (writing.md, IDs). O rótulo é `Prefixo dos requisitos:` em PRD em português e `Requirement prefix:` em PRD em inglês — são essas as duas formas aceitas.
4. Na mesma linha do prefixo, a frase que aponta o PRD 0000, quando ele existe.

O PRD 0000 difere em três pontos: usa `Escopo` no lugar de `Contexto Originário`, não tem linha de prefixo e carrega `<!-- prd: overview -->` na primeira linha, por ser o único PRD com forma própria. Nenhum outro comentário de máquina entra em PRD algum.

O rótulo do campo segue o idioma do PRD; o nome do contexto preserva o termo do domínio.

```markdown
# Verificação Assíncrona de Documentos

| | |
|---|---|
| **Contexto Originário** | Customer Onboarding; afeta Account Activation |

Prefixo dos requisitos: `ONB`. Propósito da plataforma, mapa de contextos, catálogo de eventos e fluxos: [PRD 0000](0000-platform-overview.md).
```

## Idioma

- **O PRD é escrito em português ou em inglês.** São os dois idiomas que o ferramental cobre: `--lang` aceita `pt` ou `en`, e a tabela de seções dá o nome de cada seção nos dois, o em português e, entre parênteses, o em inglês (writing.md, Seções). A precedência escolhe entre esses dois e não abre um terceiro.
- Entre os dois, o idioma do artefato segue a precedência. Quando ninguém o fixou, é o idioma do material recebido (com material em mais de um idioma, o do documento que o pedido cita primeiro ou, sem citação, o do primeiro anexo); sem material, o idioma do pedido. Uma vez fixado, pedido explícito de idioma na sessão é precedência e o muda; mensagem em outro idioma sem esse pedido não muda.
- Material, pedido ou pedido explícito de idioma fora desses dois: o PRD sai em inglês, e a apresentação abre com uma linha dizendo que ele está em inglês porque a skill escreve em português ou inglês. O termo de domínio continua no original nos dois casos (writing.md, Ubiquitous Language).
- Termo canônico em inglês se traduz quando existe tradução de mesma força e reconhecimento:

| Inglês | Português |
|---|---|
| Given/When/Then | Dado/Quando/Então |
| Functional Requirements | Requisitos Funcionais |
| Non-functional Requirements | Requisitos Não Funcionais |
| Open Questions | Perguntas em Aberto |

- Sem tradução de mesma força, o termo fica em inglês: Factory Pattern, Entity Service Antipattern, Bounded Context, Domain Event, Ubiquitous Language, JTBD, MoSCoW, guardrail, leading/lagging, trade-off.
- Identificadores de domínio (`Offering`, `ReservationBook`), IDs e tags não se traduzem.
- Fora das duas listas, traduza o termo só quando a tradução já aparece no material recebido ou no PRD 0000; caso contrário, mantenha o original em inglês.
- O par PT/EN de cada heading é alias; qual dos dois vale neste PRD é o idioma fixado, e heading do outro idioma é ocorrência da revisão (workflow.md, Revisão antes de apresentar).
