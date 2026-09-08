# Execute

**Objetivo:** implementar **uma task por vez**. Mudança cirúrgica, teste derivado da spec, gate, commit atômico. Repetir. Verificação está dentro de cada task, não é fase separada.

Leia até o fim antes de agir. As invariantes estão no Contrato de execução (SKILL.md); este arquivo é o procedimento e cita os itens do contrato.

---

## Antes da primeira task

1. **Pré-requisitos.** `tasks.md` aprovado, ou o plano inline aprovado (seção 0; com a spec quando ela existe, com os requisitos inline em Small) quando Tasks foi pulado, e Analyze sem CRITICAL nem HIGH sem aceite ([verify.md](verify.md), seção 1; modes.md, Estados). Sem isso, pare e diga o que falta. Autorizações conforme SKILL.md, Aprovações e autorizações: o pedido de implementar já autoriza implementar; commit é autorização própria, confirmada uma vez para a mudança e não perguntada de novo por task.
2. **Contexto.** Leia `tasks.md` (Matriz, Comandos de Gate, a task) ou o plano inline, o trecho do `design.md` que a task referencia quando ele existe, e os requisitos da spec que ela atende. Não carregue specs de outras mudanças.
3. **Lacunas do design.** Para cada `[LACUNA]` que sobreviveu ao design no caminho desta mudança, aplique SKILL.md, Decisão, premissa ou bloqueio: (a) dentro da autonomia concedida, decida e registre em `project-memory.md`; (b) cabe premissa, registre `[PREMISSA]` com default e racional na spec e siga; (c) é decisão material, apresente "O design tem uma lacuna: [descrição]. Opções: […]. Recomendo […]." e execute só as tasks que não dependem dela até a resposta. Nunca implemente a lacuna em silêncio nem adote uma opção porque ninguém respondeu.
4. **Sub-agentes** (tier Complex, harness com sub-agente, >8 tasks): ofereça dispatch por fase inteira, nunca auto-dispare. Cada worker executa suas tasks em ordem seguindo este arquivo e reporta resumo compacto (tasks, hashes, contagem de testes, desvios). Sem harness com sub-agente ou usuário recusa: execute inline.

---

## 0. Passos inline (obrigatório quando Tasks foi pulado)

Sem `tasks.md`, liste antes de qualquer código:

```
## Plano de execução
Requisitos (Small, sem spec.md): - **XYZ-01** — WHEN … THEN the system SHALL …
Estrutura (Design pulado): [uma ou duas linhas: onde entra, o que reusa]
Gate: [comando de build e teste do repositório]
1. [passo] → arquivos: [lista] → verifica: [como] → commit: [mensagem, se autorizado]
2. …
```

Cada passo é um entregável coeso, verificável e integrável sozinho (tasks.md, Task atômica). Sem `tasks.md`, o plano é o artefato que passa pelo gate de aprovação e é o que Analyze e Verify leem (verify.md). Se a lista passar de 5 passos, revelar dependência não trivial ou risco nomeado, **pare, declare o tier novo e crie o artefato que faltou** — Tasks ou Design foram pulados errado. Isso é a catraca subindo, não um desvio.

---

## Ciclo por task

### 1. Escolher e verificar dependências

Task indicada pelo usuário ("faz a T3") ou a próxima disponível. Se uma dependência não está concluída, pergunte: "T3 depende de T2, que não está feita. Faço T2 antes?"

### 2. Declarar o plano

Antes de escrever código, em 3 linhas: **arquivos** (só os que a task lista), **abordagem**, **como vou verificar**. Se há premissa ou incerteza, diga. Se enxerga abordagem mais simples que a do design, diga antes; se discorda do design, discorde — não seja sicofanta.

### 3. Testes derivados da spec

Quando o campo `Tests` da task é diferente de none:

- Contrato item 1: os testes vêm do "Pronto quando" e dos requisitos da spec. Cada requisito da task tem no mínimo uma assertion cujo valor afirmado é o **resultado que a spec define** (status, mensagem, estado, evento). Se a spec não define resultado preciso, registre como *lacuna de precisão da spec* e volte à spec; não escreva assertion vaga que passa em silêncio.
- Edge cases da spec que tocam a task ganham teste.
- Rode os testes antes de implementar. Teste de comportamento **novo** deve falhar antes do código: se passa, não está testando o que a task entrega. Teste de caracterização (refactor `no-behavior-change`, comportamento existente que a task preserva) deve passar antes e depois; sua função é proteger, não falhar.

**Integridade de teste** (contrato item 3): se um teste parece errado contra a spec, **pare e confirme com o usuário** antes de tocá-lo. Os testes são a spec executável; o código conforma a eles, não o contrário.

### 4. Implementar

O mínimo que satisfaz a task: passa os testes; atende gate quando não há teste direto.

- **Simplicidade.** Nada além do pedido; sem abstração para uso único; sem flexibilidade não solicitada; sem tratamento de erro para cenário impossível. Se 200 linhas poderiam ser 50, reescreva.
- **Cirúrgico.** Não "melhore" código adjacente, comentário ou formatação. Não refatore o que não está quebrado. Siga o estilo existente mesmo discordando. Problema adjacente (bug vizinho, dívida, dead code) se reporta, não se corrige (modes.md, Desvios). Remova só o que a sua mudança orfanou. Arquivo indispensável descoberto durante a task (registro, config) entra em `Onde` com nota, sem aumento material de escopo (SKILL.md, Contrato, item 5).
- **Refine o contexto, não o erro** (SKILL.md, Posicionamento). Spec ou design errados (regra impossível, contrato inconsistente, restrição da base não prevista)? Pare: "Encontrei uma restrição não prevista: [descrição]. Isso invalida [spec/design] em [ponto]. Recomendo corrigir lá e re-derivar [tasks afetadas]." Regra de negócio errada volta ao PRD antes da spec (specify.md, Origem e modo). Desvio local que não invalida o artefato recebe marcador no código:

  ```
  // SPEC_DEVIATION: [o que divergiu]
  // Reason: [por quê]
  ```
  e linha em `## Desvios` no `tasks.md` (ou no substituto de modes.md: delta em Medium sem tasks, nota no plano em Small). Todo desvio é resolvido antes do PASS final (modes.md, Desvios).

- **Segurança** (contrato item 6). Forma da sugestão de pacote: "Sugiro `[nome]`. Antes de instalar, confirme procedência em [registro oficial]"; pacotes inventados existem e são publicados maliciosamente.

### 5. Gate

Rode o comando do nível de gate da task (`Comandos de Gate` em `tasks.md`, ou do plano inline). Se o exit for diferente de 0, pare, corrija e rode de novo (contrato item 2). Gate que não pode ser executado (SDK ausente, dependência indisponível) não é gate verde: a task fica bloqueada com o motivo. Contagem de testes igual ou maior que a anterior é sinal auxiliar: diminuição só é legítima com requisito REMOVED e a razão registrada.

| Task tem | Gate |
|---|---|
| Só unit | Quick |
| Integration/e2e | Full |
| Última da fase, ou sem teste | Build (build + lint + todos) |

### 6. Revisão pós-gate

1. Critérios do `Pronto quando` atendidos, inclusive os de comportamento; gate verde sozinho não fecha a task.
2. Nenhum `SPEC_DEVIATION` sem registro.
3. "Um sênior chamaria isso de complicado demais?" Se sim, simplifique e rode o gate de novo.
4. **Adequação dos testes** — tabela obrigatória antes de commitar:

   | Critério ("Pronto quando" / requisito / edge case) | `file:line` + assertion | Resultado da spec | Coberto? |
   |---|---|---|---|

   Regra de evidência: verify.md, Eixo 1 (evidência ou zero); sem `file:line` a task não fecha.
   Depois, o inverso: todo teste novo mapeia para um critério, requisito ou edge case? Teste sem dono é escopo escondido.

### 7. Fechar a task, com commit quando autorizado

Antes de fechar: marque a task concluída em `tasks.md` (ou no plano inline) e, quando há delta, atualize `Status` na Rastreabilidade da spec (de `Implementing` para `Verified` só depois do Verifier). Com commit autorizado, essas atualizações entram **no mesmo commit** da task:

```
git add <apenas os arquivos da task>
git commit -m "<msg>"
```

Formato da mensagem: o que o repositório convenciona (CLAUDE.md, CONTRIBUTING); se o repositório tem validação de mensagem, rode-a antes do commit. Sem commit autorizado, a task fecha com gate verde e artefatos atualizados na árvore de trabalho; o registro (`tasks.md`, Handoff) diz "sem commit" onde pediria hash. Um commit por task e blast radius: contrato itens 3 e 5.

---

## Depois da última task

Contrato item 4: siga [verify.md](verify.md), Verifier, e declare o grau de independência obtido. O Verifier devolve o relatório; você (orquestrador) persiste `validation.md`, roda `lint_validation.py` e só então atualiza Rastreabilidade e tasks. Tier Small: passada *fresh-eyes* própria com a mesma tabela de evidência, no chat (modes.md).

---

## Critérios de qualidade

Cada item cita a seção que contém a regra.

- Cada task segue a sequência: plano declarado, testes da spec falhando, implementação mínima, gate verde, tabela de evidência e fechamento, com commit quando autorizado (ciclo, passos 2–7).
- Nenhuma lacuna do design resolvida em silêncio nem por silêncio; nenhuma restrição descoberta improvisada (Antes da primeira task; passo 4).
- Só os arquivos da task tocados; nada além do pedido (passo 4).
- `tasks.md` e rastreabilidade atualizados no fechamento da task (passo 7).
- Contrato de execução (SKILL.md) respeitado item a item.
