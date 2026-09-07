# Tasks

**Objetivo:** decompor o design em tasks atômicas, com dependências claras, teste co-locado e rastreabilidade até o requisito — um plano que um executor **sem contexto** consegue seguir sem adivinhar.

Leia até o fim antes de agir.

**Pule** conforme SKILL.md, Tiers. As tasks ficam implícitas nos passos inline do Execute, e a válvula de segurança reabre esta fase se a lista crescer.

---

## 1. Ler o design e a spec

Tasks derivam do `design.md` (estrutura, arquivos, interfaces) e apontam para a `spec.md` (IDs). Sem design (tier Medium sem risco), derive da spec e da base e registre a estrutura mínima em `## Estrutura` no próprio `tasks.md`: arquivos, componentes e o que reusa, em até dez linhas (modes.md). O Verify compara o eixo 2 com essa seção.

---

## 2. Matriz de cobertura de testes (sempre)

Antes de qualquer task, descubra como este repositório testa. Não invente comandos nem presuma ecossistema.

**Passo 0 — guias do projeto.** Procure padrões documentados: `AGENTS.md`, `CLAUDE.md` ou equivalente; `CONTRIBUTING.md`; `docs/` sobre testes; thresholds de cobertura em config de runner ou CI. Se encontrar guia, a expectativa de cobertura obedece a ele; cite os arquivos. Se não encontrar nenhum, aplique o **default forte** abaixo.

**Passo 1 — amostra de testes existentes.** Localize 5–10 arquivos de teste; mapeie camada exercitada e nível (unit, integration, e2e); extraia estilo, localização, framework. Use como **piso** (nunca menos rigoroso que o existente na mesma camada), nunca como teto — o teto vem da spec.

**Passo 2 — comandos do repositório.** Extraia de manifests, config e CI (`*.csproj`/`*.sln` + `dotnet test`, `package.json`, `Makefile`, `pyproject.toml`, workflows). Capture também lint/format/typecheck: o gate Build roda tudo.

Se o repositório não tem teste algum, pergunte ao usuário os tipos de teste e os comandos.

**Default forte** (sem guia):

| Camada | Expectativa |
|---|---|
| Domínio / regra de negócio (aggregate, use case, serviço de domínio) | Todas as ramificações; 1:1 com requisitos da spec; todo edge case listado tem teste |
| Adapter de entrada (controller, consumer, handler) / e2e | Happy path + cada edge case + caminhos de erro, por rota/mensagem em escopo |
| Repositório / acesso a dados | Caminhos de consulta principais + erro; espelhe testes existentes |
| Entidade / config / schema | Só gate Build quando não carrega regra; entidade ou value object com invariante (validação, cálculo) é domínio e tem unit test |

Build prova que o entregável compila e integra; não prova regra de negócio. Evidência de comportamento é assertion contra o resultado que a spec define; validação estrutural (build, lint, contagem) é complemento.

Renderize **exatamente** estas duas seções em `tasks.md` (o Execute e o Verify as referenciam pelo nome), com linhas de dados; tabela vazia ou célula de Comando vazia é `HARD`:

```markdown
## Matriz de Cobertura de Testes
> Gerada do repositório, guias e spec — confirmar antes de Execute. Guias encontrados: [arquivos ou "nenhum — default forte"].

| Camada | Tipo de teste | Expectativa de cobertura | Padrão de localização | Comando |
|---|---|---|---|---|

## Comandos de Gate
> Gerados do repositório — confirmar antes de Execute.

| Gate | Quando | Comando |
|---|---|---|
| Quick | Task com unit test | … |
| Full | Task com integration/e2e | … |
| Build | Última task da fase; task sem teste | build + lint + todos os testes |
```

**Teste co-locado.** Task que cria ou modifica camada com tipo de teste exigido **inclui** escrever os testes na mesma task, satisfazendo a expectativa da camada — não "existir". "Testado na task N" não é justificativa para `Tests: none`; é adiamento, o anti-padrão que esta regra impede. Se o código de uma task só é testável depois de outra (controller antes do wiring), reestruture: mova os testes para a task onde ficam executáveis (merge forward) ou absorva a dependência na task atual (merge backward). Nenhuma task produz código não verificado.

---

## 3. Task atômica

**Uma task = um entregável coeso, verificável e integrável:** um componente, uma função, um endpoint, um handler, com o que ele precisa para ser verificado e integrado na mesma task: implementação, teste co-locado (seção 2), configuração ou registro indispensável (DI, rota, migration) e a atualização de `tasks.md` e da rastreabilidade. "Implementar autenticação" não é task; "criar `ReservationService.Confirm` com idempotência, testes e registro no módulo" é.

Granularidade: um entregável com seus arquivos é aprovado. Dois entregáveis independentes na mesma task é reprovado: divida, porque gate, evidência e commit deixam de apontar para uma coisa só. Número de arquivos não decide: implementação, teste e registro moram em arquivos diferentes por convenção do repositório. `Onde` lista todos os arquivos que a task cria ou modifica; o linter avisa quando não reconhece nenhum path.

Cada task carrega:

| Campo | Conteúdo |
|---|---|
| **O quê** | Uma frase: o entregável exato |
| **Onde** | Paths reais de todos os arquivos que a task cria ou modifica (`src/…`, `tests/…`) |
| **Depende de** | IDs de task ou `nenhuma`; só para trás ou dentro da mesma fase, sem ciclo (o linter reporta o ciclo com os IDs); `T` nunca depende de `TC` |
| **Requisito** | IDs da spec que esta task atende (`RSV-07, RSV-10`) |
| **Reusa** | Código existente que segue |
| **Interfaces** | *Consome:* o que usa de tasks anteriores — assinaturas exatas. *Produz:* o que tasks posteriores vão usar — nomes, parâmetros, tipos de retorno. O executor de uma task só vê a própria task; este bloco é como ele aprende os nomes que os vizinhos usam |
| **Pronto quando** | Critérios binários e testáveis: pelo menos um de comportamento (o resultado que a spec define), mais o comando de gate; contagem esperada de testes é sinal auxiliar, não prova de cobertura. Task pronta = critérios atendidos, validação significativa e nenhum bloqueador; exit 0 sozinho não basta |
| **Tests** | Lista dos tipos realmente necessários, separados por vírgula (`unit`, `unit, integration`, `e2e`), ou `none` sozinho — da matriz; integration/e2e não substituem unit exigido pela camada |
| **Gate** | `quick` / `full` / `build` — dos comandos; todo valor usado tem linha em Comandos de Gate; integration/e2e exige `full`; `none` exige `build` |
| **Commit** | Mensagem planejada no formato do repositório (Conventional Commits por default); pode ficar vazia quando commits não estão autorizados (WARN); presente, é validada na forma pelo `check_commit.py` (`--max-len N`, `--no-scope`, `--no-bang`, `--single-line`, `--lowercase`), que o `lint_tasks.py` chama com as mesmas opções prefixadas por `commit-` (`--commit-max-len N`, `--commit-no-scope`, `--commit-no-bang`, `--commit-single-line`, `--commit-lowercase`) para aplicar a política do repositório. Mensagem planejada, commit autorizado e commit executado são estados distintos (SKILL.md, Contrato, item 3) |

**Sem placeholders** (SKILL.md, Redação). Específicos de tasks: "escrever testes para o acima" sem dizer quais; "similar à T3" (repita, porque o executor pode ler fora de ordem); referência a tipo ou método não definido em nenhuma task nem no design.

**Tasks de correção** (verify.md, 2.8) usam o mesmo formato com IDs `TC1`, `TC2`, …, sob `## Tasks de correção`; podem depender de `Tn` ou `TCn` e não precisam constar do plano de execução aprovado, porque nascem depois dele.

---

## 4. Fases e dependências

Agrupe tasks em fases ordenadas; fases executam em sequência, tasks em ordem dentro da fase. Fase é unidade de coesão e dependência (fundação, depois domínio, depois adapters, depois integração), não de tamanho. Fase muito grande (mais de 10 tasks) se divide numa costura real de dependência, não num índice arbitrário — exceto quando é uma cadeia única que não se separa.

Dependência aponta só para trás ou para a mesma fase; dentro da fase, a ordem do plano é a ordem executável. São `HARD` no linter: dependência para fase posterior, ciclo, task fora do Plano de execução, task citada no plano sem corpo e Mapa de execução divergente do plano. Plano, mapa e lista citam o mesmo conjunto de tasks.

---

## 5. Validar antes de apresentar

Rode `lint_tasks.py <tasks.md> --spec <spec.md>` (SKILL.md, Gates), com as opções de prefixo `commit-` (`--commit-max-len`, `--commit-no-scope`, `--commit-no-bang`, `--commit-single-line`, `--commit-lowercase`) que a política de commit do repositório exigir além de Conventional Commits. Requisito da spec sem task é código que não vai existir.

Depois, as três checagens de julgamento, com as tabelas incluídas no output:

**Granularidade** — cada task é um entregável só, com seus arquivos? Tabela com as colunas Task, Entregável, Arquivos e Status.

**Co-localização de teste** — para cada task, a camada criada/modificada tem tipo exigido na matriz? O campo `Tests` bate? Task que cria múltiplas camadas usa o tipo mais alto. Tabela com as colunas Task, Camada, Matriz exige, Task diz e Status.

**Consistência de tipos** — nomes, assinaturas e tipos usados no `Consome` de uma task batem com o `Produz` da task anterior e com o design? `ConfirmReservation` na T3 e `ConfirmReserve` na T7 é bug de plano.

Qualquer item reprovado exige reestruturar antes de apresentar. Não mostre tasks falhando e peça aprovação.

Matriz e comandos são provisórios até o usuário aprovar as tasks; então viram autoritativos. Apresente e pare (SKILL.md, Aprovações e autorizações).

---

## Template: `changes/NNNN-<feature-slug>/tasks.md`

````markdown
<!-- sdd: tasks | tier: large | design: ./design.md -->
# Reserva Parcial no Bookbuilding — Tasks

| | |
|---|---|
| **Status** | Rascunho / Aprovado / Em andamento / Concluído |
| **Design** | ./design.md |
| **Spec** | ./spec.md |

## Protocolo de execução

Implemente com a skill `spec-driven` (entrada Execute) e seu contrato de execução. Se a skill não puder ser ativada, pare e avise — não prossiga sem ela.

## Estrutura
<!-- só quando Design foi pulado: arquivos, componentes, o que reusa, em até dez linhas -->

## Matriz de Cobertura de Testes
[gerada na seção 2]

## Comandos de Gate
[gerados na seção 2]

## Plano de execução

### Fase 1: Domínio
T1 → T2

### Fase 2: Adapters
T3 → T4

### Fase 3: Integração
T5

## Tasks

### T1: Criar `PartialReservation` value object
- **O quê:** value object com a quantidade reservada, validação `MIN_INVESTMENT_NOT_MET` contra o investimento mínimo (RSV-07) e seus testes unitários
- **Onde:** `src/Bookbuilding.Domain/Reservations/PartialReservation.cs`; `tests/Bookbuilding.Domain.Tests/Reservations/PartialReservationTests.cs`
- **Depende de:** nenhuma
- **Requisito:** RSV-07, RSV-08
- **Reusa:** `src/Bookbuilding.Domain/Shared/Quantity.cs`
- **Interfaces:**
  - Consome: `Quantity`, `InvestmentLimits`
  - Produz: `PartialReservation.Create(Quantity amount, InvestmentLimits limits): Result<PartialReservation, ReservationError>`
- **Pronto quando:**
  - [ ] `Create` rejeita quantidade abaixo do investimento mínimo com `ReservationError.MinInvestmentNotMet` (RSV-07)
  - [ ] `Create` aceita quantidade dentro dos limites e preserva o valor (RSV-08)
  - [ ] Gate passa: `dotnet test tests/Bookbuilding.Domain.Tests`
  - [ ] Contagem de testes: +4, sinal auxiliar
- **Tests:** unit
- **Gate:** quick
- **Commit:** `feat(bookbuilding): add PartialReservation value object`

### T2: …
<!-- o template elide T2–T5; num tasks.md real, plano, mapa e lista citam o mesmo conjunto -->

## Mapa de execução

```
Fase 1: T1 → T2
Fase 2: T3 → T4
Fase 3: T5
```

## Desvios

[Vazio até o Execute; cada `SPEC_DEVIATION` do código ganha uma linha aqui.]

## Validação pré-aprovação

### Granularidade
| Task | Entregável | Arquivos | Status |
|---|---|---|---|

### Co-localização de teste
| Task | Camada | Matriz exige | Task diz | Status |
|---|---|---|---|---|

### Rastreabilidade
| Requisito | Tasks |
|---|---|
| RSV-07 | T1, T3 |
````

---

## Critérios de qualidade (passada Tier 2)

Cada item cita a seção que contém a regra.

- Um entregável por task, com todos os seus arquivos em `Onde` (seção 3).
- Todo requisito da spec tem task; toda task tem requisito, porque task sem requisito é escopo escondido ou refactor não pedido (seção 5).
- `Interfaces` com assinaturas literais, consistentes entre tasks e com o design (seções 3 e 5).
- Teste co-locado satisfazendo a matriz; `Tests: none` só onde a matriz diz none (seção 2).
- `Pronto quando` binário, com critério de comportamento e gate; contagem de testes só como sinal auxiliar; sem placeholder (seção 3).
- Fases por coesão, dependências só para trás (seção 4).
- O plano é legível por um executor que nunca viu o repositório.
