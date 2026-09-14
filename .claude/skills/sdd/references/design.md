# Design da solução

Defina componentes, interfaces e reuso com profundidade proporcional ao risco. Use a spec atual; se faltar comportamento, resolva-o na spec antes de escolher o mecanismo. Pré-requisitos e autonomia estão em [workflow.md](workflow.md); destino e comentário em [specify.md](specify.md).

## Contexto necessário

Leia os requisitos em escopo, os ADRs pertinentes e os custos, dependências e NFRs do PRD. Em PRD 0000, consulte as fronteiras e os contratos que a mudança toca.

Na base de código, comece pelos módulos envolvidos, contratos, entidades, serviços e infraestrutura relevante. Abra implementações completas quando assinatura e contexto não forem suficientes. Registre o alcance da leitura e limitações que afetem a decisão.

Uma convenção escrita é autoridade; exemplos são evidência de padrão, com alcance e exceções conhecidos. Não transforme quantidade de arquivos em prova de convenção. Antes de condenar uma decisão existente, busque a justificativa pertinente no histórico ou ADR.

## Critérios, alternativas e riscos

Defina critérios antes das alternativas. Cada critério tem origem em requisito, ADR, restrição de custo ou contexto operacional. Critique lacunas e escolha entre alternativas reais, comparáveis pelo mesmo escopo e critérios.

Decisões técnicas dentro da autonomia concedida não exigem confirmação intermediária. Registre escolha, razão e custo. Sem alternativa real, omita `Approaches` e encerre `Evaluation Criteria` com `No real alternative: <razão>`. Não invente opções para preencher uma tabela.

Em cada decisão, avalie objetivos de negócio, atributos de qualidade, restrições e se existe solução mais barata ou menos arriscada. Risco sem mitigação exige aceitação explícita dentro da autonomia disponível.

| Risco pertinente | Técnica a considerar |
|---|---|
| Perda de evento ou inconsistência entre contextos | Garantia de entrega, outbox ou mecanismo equivalente |
| Concorrência, duplicação e reprocessamento | Idempotência, unicidade, ordenação e controle de concorrência |
| Integração instável | Timeout, política de repetição, circuit breaker, contingência |
| Cálculo financeiro | Precisão decimal, invariantes e regras isoladas para teste |
| Migração e compatibilidade | Transição de dados, compatibilidade e reversão |
| Desempenho | Orçamento mensurável, índices e limites de consulta |
| Segurança e dados regulados | Autorização, retenção, mascaramento e auditoria |

A tabela sugere técnicas; não obriga a adotar todas. Para dinheiro, segurança ou concorrência, avalie testes de limites e mutation testing conforme [verify.md](verify.md).

## Componentes, contratos e dados

Cada componente declara propósito coeso, caminho, interfaces com tipos, dependências e reuso. Justifique a criação quando não houver componente apropriado. Evite abstrações sem necessidade demonstrada; uma interface com um único implementador pode ser necessária por contrato ou isolamento.

Eventos declaram produtor, consumidores, significado do payload, chave de ordenação quando necessária, entrega, idempotência e versão. Não presuma consumidores nem transporte.

Quando houver persistência, descreva entidades, relações, invariantes e migração. Em `Error Handling`, cada requisito `IF ... THEN` em escopo tem cenário, ID, tratamento e impacto.

## Módulo, pacote e implantação

Diferencie módulo de código, pacote versionado e unidade que sobe ou desce em conjunto. Prefira alteração no serviço existente, depois módulo no mesmo serviço, e por fim outra unidade de implantação.

Outra unidade exige uma necessidade concreta de implantação independente ou isolamento que a solução existente não atenda. Registre contrato, compatibilidade, proprietário e custo operacional. Uma biblioteca compartilhada exige responsável, estabilidade de interface avaliada pelo histórico e ausência de alternativa adequada; regras de negócio permanecem no contexto dono.

Respeite interfaces públicas e evite ciclos entre módulos. Decisões que estabelecem convenção para futuras capacidades seguem [adr.md](adr.md).

## Seções do artefato

Use os títulos em inglês abaixo, nesta ordem, omitindo seções sem conteúdo:

1. `Design Context` — fontes, restrições e alcance da leitura.
2. `Evaluation Criteria` — critérios e origem.
3. `Risks and Techniques` — riscos, mitigação ou custo aceito.
4. `Approaches` — apenas alternativas reais.
5. `Architecture Overview` — estrutura; diagrama quando esclarecer interações.
6. `Deployment Unit` — unidade afetada e motivo.
7. `Components` — componentes e contratos.
8. `Domain Events` — contratos de eventos.
9. `Data Model` — persistência.
10. `Error Handling` — cobertura dos cenários indesejados.
11. `Technical Decisions` — decisão, escolha, justificativa e tipo: contrato público ou decisão interna.
12. `Files to Create or Modify` — caminhos de entrada para tarefas.

A extensão de uma seção depende da explicação necessária ao risco, sem quota de linhas. Revise conforme [validation.md](validation.md) e continue até a entrega autorizada.

## Exemplo didático

Exemplo correspondente à spec de quantidade em [specify.md](specify.md). Paths e contratos pertencem somente ao exemplo.

```markdown
<!-- sdd: design | spec: ../spec.md | scope: QTY-01, QTY-02 -->
# Validação de quantidade — design

## Design Context

QTY-01 e QTY-02 definem aceitação e erro. A mudança fica no módulo existente do exemplo.

## Evaluation Criteria

A resposta deve preservar o valor aceito e distinguir o erro definido na spec.
No real alternative: uma função pura atende ao contrato sem dependência externa.

## Components

### QuantityValidator

- **Purpose:** validar uma quantidade inteira.
- **Location:** `src/Examples/QuantityValidator.cs`
- **Interfaces:** `Validate(int quantity): QuantityResult`
- **Dependencies:** nenhuma.
- **Reuses:** convenção de resultado do módulo do exemplo.

## Error Handling

| Cenário (ID) | Tratamento | Impacto |
|---|---|---|
| Quantidade não positiva (QTY-02) | `QuantityResult.Failure("INVALID_QUANTITY")` | Consumidor recebe o erro |

## Files to Create or Modify

- Criar `src/Examples/QuantityValidator.cs`.
- Criar `tests/UnitTests/QuantityValidatorTests.cs`.
```
