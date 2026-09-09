# Modos condicionais

Carregado só quando o pedido dispara um dos modos. As regras gerais de intake.md e de writing.md continuam valendo; aqui está só o que muda.

## Modo reverse PRD

Documentar o que já foi construído ("PRD do módulo X", "documente o que construímos"). O autor olha para código e telas, então o gradiente para descrever mecanismo é máximo; o capability test (writing.md, Capability test) tem peso extra.

- Peça comportamento observável, regras aplicadas e decisões que o sistema toma. Aceite código, docs, bullets, descrição livre.
- Derive intenção a partir de resultados (o que usuário ou negócio ganha), não de operações.
- Intenção inferida é `[PREMISSA]`, marcada pesadamente: intenção engenheirada em reverso é frágil.
- Comportamento sem justificativa de negócio identificável é `[LACUNA]`: expõe feature órfã (peso morto ou valor escondido).
- Múltiplas intenções plausíveis para o mesmo comportamento vão para Perguntas em Aberto. Não fabrique coerência inexistente.

## Modo plataforma, infra, SDK ou API como produto

- Usuário é o time ou sistema consumidor; JTBD funciona ("integrar auth sem gerenciar estado de sessão").
- Métricas primárias são operacionais: percentis de latência, taxa de erro, adoção por consumidores, time-to-integration. Resultado de negócio é de segunda ordem, pertence aos consumidores.
- Critérios de Aceitação incluem o contrato: estabilidade da forma da API, SLA, janela de backward compatibility.
- Deprecação entra como não-objetivo ou trade-off quando relevante: interface antiga não coberta, o que não será migrado, cronograma não comprometido.
