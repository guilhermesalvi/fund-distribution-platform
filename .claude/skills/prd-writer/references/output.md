# Output de arquivo e header

Passo 5 do workflow: onde o PRD é gravado e como é o cabeçalho. O conteúdo é writing.md.

## Path

`/docs/prd/` marca o tipo; o nome carrega o contador `NNNN`, o contexto originário (`<domain-slug>`) e a feature (`<feature-slug>`), tudo kebab-case em inglês, sem prefixo `prd-`. Dois layouts, um por repositório:

| Layout | Path | Quando |
|---|---|---|
| flat | `/docs/prd/NNNN-<domain-slug>-<feature-slug>` | Poucos contextos e PRDs; pasta por contexto é complexidade sem retorno. Default |
| nested | `/docs/prd/<domain-slug>/NNNN-<feature-slug>` | Muitos PRDs por contexto; navegar por pasta compensa |

O layout é estado do filesystem, não configuração: `seq.py` o infere e acusa WARN se os dois coexistem. No primeiro PRD do repositório pergunte o layout e passe `--layout` ao `seq.py next`; nos seguintes, siga o detectado. Migrar é mover arquivos e reescrever links relativos; o número não muda.

`NNNN` é contador de 4 dígitos global em `/docs/prd/`, porque dá referência curta ("PRD 0007") e ordem de chegada. Obtenha o path com `seq.py next` (SKILL.md, Scripts); nunca escolha o número lendo o diretório: o script deriva do maior existente e se recusa a alocar sobre sequência inválida. `0000` é reservado ao PRD de visão geral (writing.md, PRD 0000): `0000-<domain-slug>-overview.md` em flat, `0000-overview.md` em nested. Contador global colide em PR paralelo; renumere o branch que entra depois e `seq.py check` acusa a duplicata.

Slug repetido em número novo é substituição: declare `| **Substitui** | NNNN |` no header do novo e mude o Status do antigo para `Substituído por NNNN`. O número é índice; a precedência é o que o header declara.

## PRD plano ou em pasta

- Plano: `<path>.md`. Default.
- Em pasta: `<path>/` com `prd.md`, `assets/` (mockups, diagramas, planilhas, imagens referenciadas) e, opcional, `decisions.md` (alternativas avaliadas e descartadas que não cabem em Trade-offs nem viram ADR).

Comece plano; migre para pasta no primeiro anexo ou decisão a persistir, porque migrar quebra links externos (Linear, Slack, e-mail). Se o usuário já mencionou mockup, diagrama, planilha ou histórico de decisão, comece em pasta.

Índice opcional `/docs/prd/README.md` com status e link, útil a partir de ~5 PRDs. Não crie no primeiro.

Só `NNNN-*.md` e `NNNN-*/prd.md` são PRDs para o linter e para o índice cruzado; `decisions.md`, `assets/` e `README.md` são anexos e não entram.

Sem repositório, use o mesmo layout sob o diretório de saída que o ambiente indica (pergunte ou anuncie; não presuma um path fixo). O contador parte de `0001`, ou de `0000` quando há visão geral.

## Header

O comentário de tier vai na primeira linha, antes do `#`, em ASCII minúsculo independente do idioma, porque é tag de máquina consumida pelo linter: `<!-- prd-tier: simples | media | complexa | overview -->`. O valor segue writing.md, Tier; `overview` é o PRD 0000. Quando a convenção do projeto dispensa uma seção esperada do tier, declare-a no comentário: `<!-- prd-tier: complexa | omit: aceitacao,dependencias -->` silencia só o WARN daquelas seções (chaves na docstring do `lint_prd.py`). HARD nunca é silenciado.

A metadata vai em tabela de duas colunas logo abaixo do `#`, sem linha de cabeçalho semântica. Hard break por dois espaços é frágil (editores aparam trailing whitespace) e lista é enumeração de itens peer; metadata é par chave-valor, e a tabela transmite isso.

```
<!-- prd-tier: complexa -->
# [Nome da Feature]

| | |
|---|---|
| **Status** | Rascunho / Em Revisão / Aprovado |
| **Autor** | [nome] |
| **Data** | AAAA-MM-DD |
| **Contexto Originário** | [contexto primário; afetados → Dependências e Riscos; rótulo equivalente (módulo, área) se DDD não se aplica] |
| **Confiança** | Média / Baixa |

Prefixo dos requisitos: `OFF`. Propósito da plataforma, mapa de contextos, catálogo de eventos e fluxos: [PRD 0000](0000-platform-overview.md).
```

A linha de prefixo vem logo após a tabela em todo PRD com requisitos (writing.md, IDs); a segunda frase existe quando há PRD 0000. O PRD 0000 troca `Contexto Originário` por `Escopo` e não tem linha de prefixo.

| Campo (PT) | Campo (EN) | Valores (PT) | Valores (EN) |
|---|---|---|---|
| Status | Status | Rascunho / Em Revisão / Aprovado / Substituído por NNNN | Draft / In Review / Approved / Superseded by NNNN |
| Autor | Author | nome | name |
| Data | Date | AAAA-MM-DD | YYYY-MM-DD |
| Contexto Originário | Originating Bounded Context | contexto | context |
| Confiança | Confidence | Média / Baixa; omitida quando Alta (writing.md, Convenção de confiança) | Medium / Low |
| Substitui | Supersedes | NNNN, só quando substitui | NNNN |

Status diz a maturidade do documento, e a skill `spec-driven` o lê antes de abrir uma spec (specify.md, Origem e modo):

| Status | Significa | Exige |
|---|---|---|
| Rascunho | Em elaboração; admite `[LACUNA]` material, `[PREMISSA-CRÍTICA]` sem plano e pergunta sem dono | Perguntas em Aberto lista o que falta |
| Em Revisão | Pronto para o usuário aprovar | Nenhuma `[LACUNA]` bloqueando escopo, métrica ou viabilidade; toda `[PREMISSA-CRÍTICA]` com plano de validação; toda pergunta com dono e critério; Confiança Média ou omitida (writing.md, Convenção de confiança) |
| Aprovado | Decisão do usuário, nunca da skill; pré-requisito de Specify na `spec-driven` | O mesmo de Em Revisão |
| Substituído por NNNN | Outro PRD assumiu o escopo | Campo Substitui no novo |

Rótulos e valores seguem o idioma do PRD (SKILL.md, Princípios); o nome do contexto preserva o termo do domínio (`Customer Onboarding` não se traduz).

## `.docx`

Só quando o usuário pede Word explicitamente. Gere o Markdown primeiro; a conversão usa a capacidade de Word disponível no ambiente (skill `docx` ou equivalente listado), mesmo path com extensão `.docx`. Sem capacidade disponível, entregue o Markdown e diga que a conversão não foi feita. Não reimplemente orquestração de docx aqui.
