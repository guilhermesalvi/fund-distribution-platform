# Gate das skills

Toda mudança em `.claude/skills/**` passa por este gate antes do commit. Ele tem duas etapas: a determinística, que
um script roda, e a revisão cética, que um agente LLM roda com nota mínima. A primeira é obrigatória sempre; a segunda,
quando a mudança toca regra (critério abaixo). O gate nasceu do ciclo de endurecimento das skills `prd` e `sdd`
(setembro de 2026) e carrega o que aquele ciclo aprendeu: nota por fórmula fechada, defeito só com reprodução,
regressão dirigida sobre o diff e alinhamento de todas as ocorrências de uma regra antes de editar.

## Etapa 1: determinística

Fonte: `.github/scripts/skills_gate.py`. Roda a partir da raiz, em qualquer sistema; a CI roda o mesmo comando em todo
push e pull request:

```bash
python3 .github/scripts/skills_gate.py
```

Cada check imprime `PASS` ou `FAIL` com o valor medido e o limite. Um `FAIL` bloqueia o commit. `WARN` dos linters não
tem limite: é heurística para julgamento humano e o gate só o reporta. Parser Mermaid ausente (exit 3) é `FAIL`, não
skip: instale com `lint_mermaid.py --setup` de cada skill.

| Check | O que mede | Limite |
| --- | --- | --- |
| `mermaid-selftest` | parser Mermaid de cada skill passa no `--self-test` | exit 0 nos 2 |
| `suite-prd` | suíte da prd: falhas, erros e skips | 0 / 0 / 0 |
| `suite-sdd` | suíte da sdd: falhas, erros e skips | 0 / 0 / 0 |
| `suite-github` | suíte de `.github/scripts`: falhas, erros e skips | 0 / 0 / 0 |
| `lint-prd` | `seq check` + `lint_prd` + `lint_mermaid` em `docs/prd` | 0 HARD |
| `lint-specs` | `seq check` + `lint_spec` em cada `docs/specs/*/*/spec.md` | 0 HARD |
| `lint-changes` | `lint_design` e `lint_tasks` (`--spec`) em `docs/specs/*/*/*` | 0 HARD |
| `lint-adr` | `seq check` + `lint_adr` em `docs/adr`, quando existe | 0 HARD |
| `mermaid-specs` | `lint_mermaid` em `docs/specs` | 0 HARD |
| `independence` | skill citando a outra, a si mesma por path ou a palavra "commit" nos scripts da sdd | 0 ocorrencias |
| `entities` | entidades HTML no lugar de `<`, `>` e `&` nos `.md` e `.py` das skills | 0 arquivos |
| `eol` | fim de linha CRLF ou misto no índice das skills | 0 arquivos |
| `slnx` | arquivo versionado fora do `FundDistributionPlatform.slnx` | 0 arquivos |
| `readme-scripts` | script de skill sem comando no `README.md` | 0 scripts |

A tabela e a lista `CHECKS` do script são mantidas iguais por teste (`.github/scripts/tests/test_skills_gate.py`):
mudou uma, muda a outra no mesmo commit. As suítes já carregam as checagens de forma das skills: citação
`(arquivo.md, Título)` resolve para heading real, template de cada referência linta com 0 HARD, tabela de seções de
cada referência bate com a lista do linter correspondente.

## Etapa 2: revisão cética com nota mínima

**Quando é obrigatória.** O `git diff --name-only` da mudança inclui `SKILL.md`, `references/*.md` ou `scripts/*.py`
fora de `tests/` de alguma skill. Mudança só em `tests/`, `README.md`, CI ou `.slnx` passa com a Etapa 1.

**Limite.** Nota mínima 90 em cada skill alterada, por esta fórmula e nada além dela:

```
nota = max(0, 100 - 10 x defeitos materiais - 3 x defeitos menores)
```

Contam só defeitos abertos, parciais ou novos. A nota se confirma quando duas rodadas seguidas, com revisores
distintos, ficam em 90 ou mais; uma rodada só não basta, porque instâncias diferentes variam e cada busca livre abre
uma camada nova.

**Materialidade (definição fechada).** Material quando pelo menos um vale, com a reprodução anexada (saída de comando
ou fixture): seguir o texto como está leva a ação errada, parada sem necessidade ou loop; duas regras dizem coisas
incompatíveis sobre o mesmo caso (as duas linhas citadas); a prosa exige uma verificação que nenhum script faz e ao
mesmo tempo proíbe fazê-la a olho. Menor em todo outro caso: redação, duplicação concordante, racional errado com
regra certa, checagem automatizável que a prosa ainda faz a olho sem proibir, mensagem de script imprecisa. Não é
defeito: decisão fixada (abaixo), preferência por outro design, o que só melhoraria com regra nova sem defeito apontado,
cenário que exige que o agente ignore uma instrução escrita.

**Dimensões (onde procurar; cada defeito pertence a uma).** Condição observável (contagem, limite, padrão de texto,
lista fechada, comando com saída esperada; "quando fizer sentido" é defeito). Critério de parada (todo ciclo tem
threshold, teto ou saída definida). Coerência interna (nenhuma regra contradiz outra na mesma skill). Determinismo (o
que pode ser verificado por script é, e a prosa aponta para o script). Regra em um lugar e legibilidade humana (uma
fonte, o resto cita; um humano ajusta um ponto sem reler tudo).

### Rodada

1. **Corretor**, um por skill alterada, em instância separada do revisor. Antes de tocar um item, `grep -rn` de todos
   os termos da regra na skill inteira (markdown e scripts), lista as ocorrências; depois de editar, todas dizem a mesma
   coisa ou citam a fonte única com `(arquivo.md, Título)`. Concretiza a regra existente; não remove regra nem cria regra
   sem defeito apontado. Checagem nova que falha em artefato real de `docs/` vira WARN e a prosa diz WARN; `docs/` não se
   edita. Teste positivo e negativo por checagem. Arquivo novo entra no `.slnx`, no `README.md` e, se a CI o chama
   diretamente, em `.github/workflows/skills.yml`. Grava `changes-round-N-<skill>.md` fora do repositório: item, `arquivo:linha`,
   o que mudou em uma frase, ocorrências alinhadas.
2. **Etapa 1 verde** antes de chamar o revisor.
3. **Revisor**, instância nova a cada rodada, sem editar nada. Lê `prior-findings.md` e classifica cada item como
   resolvido, parcial ou aberto, com o trecho atual. Lê os `changes-round-N-*.md` e procura regressão em cada edição:
   contradição nova com quem cita o trecho, citação quebrada, teto ou condição que deixou de valer. Busca livre pelo
   resto. Reproduz cada defeito antes de contá-lo. Aplica a fórmula. Grava `review-round-N.md` e sobrescreve
   `prior-findings.md` com o que continua aberto ou parcial mais os novos.
4. **Parada.** Nota confirmada nas duas skills: encerra. Máximo de cinco rodadas por pedido. Se a nota de uma skill cair
   em relação à rodada anterior, a rodada seguinte não começa antes de reavaliar o critério passado ao revisor e o
   briefing passado ao corretor, e registrar o que mudou.

### Decisões fixadas (não se reabrem sem defeito apontado)

- Cada skill é um pacote autocontido e não cita a outra; o acoplamento é só pelo artefato PRD. Código que as duas
  precisam é copiado, não compartilhado.
- A rubrica de auto-revisão das skills fica mesmo que um modelo específico dispense verificação: a skill é independente
  de modelo.
- Artefatos em português ou inglês; material em terceiro idioma produz artefato em inglês com aviso.
- Regras se concretizam; não se removem nem se adicionam sem defeito que as justifique.
