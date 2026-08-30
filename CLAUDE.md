# CLAUDE.md

Instruções para agentes trabalhando neste repositório.

## Idioma

- Código, identificadores, nomes de arquivos e diretórios, comentários, logs, mensagens de erro e mensagens de commit: **inglês**.
- Texto de documentação (`.md`, ADRs, notas): **português**.

## Convenção de commits

Conventional Commits, com o template:

```
<type>: <description_in_english>
```

Regras:

- Máximo de **60 caracteres** na linha inteira, incluindo `<type>: `. O GitHub trunca o título do commit a partir de 72 caracteres; 60 mantém folga sem afrouxar a disciplina.
- Sem escopo — nada de `feat(api):`.
- Sem ponto final.
- Sem corpo (header) e sem rodapé (footer). A mensagem é uma única linha.
- Sem `!` para breaking changes — breaking changes são comunicados na descrição do pull request.
- `<type>` em minúsculas; `<description>` em inglês, imperativo, minúscula inicial.

Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`, `style`, `revert`.

Exemplos:

```
feat: add user endpoint
fix: handle null distribution amount
refactor: extract fund allocation service
test: cover partial distribution scenario
chore: bump target framework to net10
```

## Granularidade dos commits

O critério de agrupamento é o **motivo da mudança**, não o tipo de arquivo.

- Arquivos alterados pelo mesmo motivo vão no mesmo commit, mesmo que cruzem camadas. Um refactor que toca código de produção, testes e documentação é um único `refactor: anything`.
- Arquivos alterados por motivos diferentes vão em commits diferentes, mesmo que estejam no mesmo diretório ou tenham sido tocados na mesma sessão de trabalho.
- Cada commit deve deixar o repositório em estado consistente: compilando e com os testes passando.
- Na dúvida sobre o `<type>` de um commit que mistura camadas, use o tipo do motivo da mudança — o refactor que também ajustou testes é `refactor`, não `test`.
