# Modos condicionais

Este arquivo é carregado só quando o pedido dispara um dos dois modos abaixo. As regras gerais de intake.md e de writing.md continuam valendo nos dois modos; aqui está só o que muda em relação a elas.

## Modo reverse PRD

Dispara quando o pedido é documentar o que já foi construído: "PRD do módulo X", "documente o que construímos". Neste modo o autor olha para código e telas, então a atração para descrever mecanismo em vez de comportamento é a máxima possível; por isso o capability test (writing.md, Capability test) se aplica aqui a todas as seções do PRD, e não só à Solução Proposta, à frase de solução do Resumo Executivo e aos requisitos funcionais.

- **O que pedir.** Peça comportamento observável, regras aplicadas e decisões que o sistema toma. Aceite o material em qualquer forma: código, docs, bullets, descrição livre.
- **De onde derivar a intenção.** Derive a intenção a partir dos resultados, isto é, do que o usuário ou o negócio ganha, e não das operações que o sistema executa.
- **Intenção inferida.** Toda intenção inferida é `[PREMISSA]`: intenção que não está escrita no material recebido (código comentado, doc, ticket, commit) leva a tag, porque intenção engenheirada em reverso é frágil.
- **Comportamento sem justificativa.** Comportamento sem justificativa de negócio identificável é `[LACUNA]`. A tag expõe a feature órfã, que pode ser peso morto ou valor escondido.
- **Intenções concorrentes.** Quando há múltiplas intenções plausíveis para o mesmo comportamento, elas vão para Perguntas em Aberto (writing.md, Seções). Não fabrique coerência que não existe.

## Modo plataforma, infra, SDK ou API como produto

Dispara quando o produto do PRD é uma plataforma, infra, SDK ou API, isto é, algo consumido por outro time ou sistema.

- **Usuário-alvo.** O usuário é o time ou o sistema consumidor. JTBD continua funcionando para ele; exemplo: "integrar auth sem gerenciar estado de sessão".
- **Métricas.** As métricas primárias são operacionais: percentis de latência, taxa de erro, adoção por consumidores, time-to-integration. Resultado de negócio é de segunda ordem, porque pertence aos consumidores.
- **Critérios de Aceitação.** Incluem o contrato: estabilidade da forma da API, SLA, janela de backward compatibility.
- **Deprecação.** Quando o PRD substitui interface já publicada, deprecação entra em Não-objetivos ou em Trade-offs Declarados (writing.md, Seções), dizendo qual interface antiga não é coberta, o que não será migrado e que o cronograma não está comprometido.
