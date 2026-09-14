# Convenções do PRD

## Destino e numeração

Salve em `/docs/prd/NNNN-<domain-slug>-<feature-slug>.md`, salvo convenção explícita do repositório. Use nomes em inglês kebab-case, sem prefixo `prd-`.

O contador de quatro dígitos é global na pasta. Liste os arquivos, escolha o maior número mais um e comece em 0001 quando a pasta estiver vazia. O número 0000 é reservado à visão geral. Em colisão entre branches, renumere o documento incorporado depois e atualize suas referências.

Edite o documento no mesmo arquivo. O diff registra a alteração e o histórico Git registra autoria e datas; campos de status, aprovação e confiança não entram no PRD. Sem repositório, use o mesmo layout sob o diretório de trabalho e informe o destino.

## Cabeçalho

Um PRD regular contém, nesta ordem:

1. Título `#`, com texto em português.
2. Tabela de duas colunas com um único campo: `Originating Context`, ou `Module`/`Area` quando DDD não se aplicar.
3. Linha `Requirement prefix:` com o prefixo entre crases e ponto final.
4. Na mesma linha, link para PRD 0000, quando existir.

O contexto dono da decisão aparece no cabeçalho. Contextos afetados entram após `; affects`, separados por vírgulas, e cada um recebe uma linha em `Dependencies and Risks`.

```markdown
# Verificação assíncrona de documentos

| | |
|---|---|
| **Originating Context** | Customer Onboarding; affects Account Activation |

Requirement prefix: `ONB`. Mapa de contextos e eventos: [PRD 0000](0000-platform-overview.md).
```

PRD 0000 usa `0000-<slug>-overview.md`, começa com `<!-- prd: overview -->` antes do título, usa o campo `Scope` e não declara prefixo nem requisitos. Esse é o único comentário de máquina dos PRDs.

## Idioma e contratos

A prosa, os títulos livres, as explicações e os exemplos narrativos são em português do Brasil. Preserve o vocabulário canônico do domínio e explique termos técnicos quando necessário.

Os seguintes elementos são contratos em inglês, reconhecidos pelo verificador ou usados na rastreabilidade:

- Títulos `##` listados em [writing.md](writing.md).
- Campos do cabeçalho, `Requirement prefix:` e `; affects`.
- Tags `[ASSUMPTION]` e `[GAP]`.
- Prioridades `Must`, `Should`, `Could`, `Won't`.
- Rótulos `*Cost:*`, `*Reason:*`, `Guardrail`, `**Given**`, `**when**`, `**then**`, `if false` e coluna `Identifier`.
- IDs, identificadores de domínio, nomes de arquivos, comandos e sintaxe Mermaid.

Uma instrução explícita de idioma prevalece para a prosa. Traduzir um contrato de formato exige tratar seus consumidores; não o altere como simples revisão editorial.
