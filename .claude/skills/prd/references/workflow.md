# Escrita e revisão do PRD

## Fluxo

1. Entenda o pedido conforme [intake.md](intake.md).
2. Escreva ou altere o documento conforme [writing.md](writing.md) e [conventions.md](conventions.md).
3. Valide a forma e revise o significado.
4. Entregue o arquivo, as verificações e as pendências pertinentes.

O resultado solicitado define a conclusão. Um PRD revisado pode ser entregue e usado antes do commit. Respeite as autorizações de Git e o agrupamento de commits do repositório.

## Verificação de forma

Execute, a partir da raiz:

```text
python .claude/skills/prd/scripts/check_prd.py docs/prd
```

Em outro repositório, adapte os caminhos à localização desta skill e dos PRDs. O script exige Python 3.10 ou superior e retorna um achado por linha, saída 1 para achados e 2 para diretório inválido.

Ele verifica numeração, cabeçalho, seções, IDs, alguns formatos por seção, links locais, PRD 0000, tags, duplicações e aspectos sintáticos de Mermaid. Não prova correção de negócio, síntese das fontes nem renderização dos diagramas.

Corrija os achados solucionáveis dentro do escopo. Repita a checagem após alterações que possam afetá-la. Continue enquanto houver uma correção fundamentada ou nova evidência; se uma dependência impedir a solução, informe o achado, a causa e o que falta. Não declare validação completa com pendências.

Uma forma exigida pelo usuário ou por convenção escrita pode prevalecer sobre o padrão da skill: registre o achado como mantido por pedido ou convenção, citando a origem. Isso não resolve defeitos de significado.

## Revisão de conteúdo

Revise o documento novo por inteiro. Em alteração localizada, examine os trechos alterados e seus dependentes; amplie quando mudar uma regra ou fronteira. Verifique:

- **Capacidade:** comportamento observável nas seções pertinentes, com as exceções de [writing.md](writing.md).
- **Fonte única:** cada regra tem um FR; outras seções citam seu ID.
- **Evidência:** fatos, hipóteses e lacunas permanecem distintos.
- **Utilidade:** cada seção acrescenta informação; métricas, alternativas e fragilidades não foram inventadas para preencher formato.
- **Prosa:** linguagem, condições, responsáveis e resultado são claros, conforme [prose.md](prose.md).

Relate problemas concretos, com localização, impacto e correção. Não atribua notas numéricas à clareza. Uma alteração editorial preserva modalidade, limites e regras.

## Iteração e entrega

Altere as seções afetadas e as dependências identificadas. Regenerar o documento inteiro só se justifica quando a mudança de objetivo, fronteira ou modelo tornar a estrutura atual inadequada; a quantidade de seções editadas não decide isso.

Antes de mudar ou remover um requisito, localize os consumidores de seu ID com `rg -n` e atualize os que estiverem no escopo. Preserve decisões de negócio pendentes como lacunas.

Entregue o caminho, o resultado da validação e os achados restantes. Apresente `Weakest Point` e `Open Questions` apenas quando existirem. Quando perguntas forem vedadas, relate as lacunas como pendências, sem solicitar resposta para concluir a revisão autorizada.
