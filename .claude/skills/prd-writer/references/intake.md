# Avaliação do input, modos condicionais e pesquisa

Passos 1 e 2 do workflow. Tags de confiança usadas aqui: writing.md, Convenção de confiança.

## Escopo problemático

| Sintoma | Ação |
|---|---|
| Muito amplo: domínio inteiro, múltiplas iniciativas sem corte ("plataforma de crédito") | Não gere; peça um corte específico ou proponha um para validação |
| Enquadrado como implementação ("PRD para o microserviço X", "PRD para a tela Y") | Redirecione: PRD começa do problema |
| CRUD ou entidade-cêntrico ("CRUD para X", "tela de cadastro para Y") | Redirecione: que capability ou JTBD isso serve? Que decisão de negócio acontece ali? Problemas são vividos por pessoas, não por tabelas precisando de telas |

Em qualquer caso, pergunte: que problema de usuário ou de negócio essa implementação resolve?

## Material de discovery

PDF, docx, decks, atas, briefs e PRDs antigos são ricos e não autoritativos.

- Extraia sinais antes de perguntar: problema, evidência, usuário-alvo, direção, métricas, restrições.
- Inferência do discovery é `[PREMISSA]` derivada do documento. `[FATO]` só para fonte autoritativa: regulação oficial, política formalizada, decisão registrada.
- Sintetize, não reformate: reorganização cosmética produz PRD bonito e falso.
- PRD antigo: determine se é (a) reverse PRD para incremento, (b) update que substitui, (c) inspiração. Pergunte se ambíguo.
- Fontes conflitantes → `[LACUNA]` e pedido de reconciliação. Não escolha um lado em silêncio.

## Ontologia a partir de transcrições

Reunião com especialista de domínio se grava e se transcreve; a transcrição é a matéria-prima da linguagem do PRD. Não pule da transcrição para regras ou classes: o salto é grande demais e esconde o erro de entendimento. Extraia em passadas separadas, uma por prompt, porque cada passada recebe o orçamento inteiro de atenção e o resultado de uma alimenta a seguinte. Tudo que sai daqui é `[PREMISSA]` derivada da transcrição até o especialista validar.

| Passada | Tabela | Alimenta |
|---|---|---|
| 1. Correção | Termos e nomes mal transcritos, com a leitura provável | As demais passadas |
| 2. Conceitos | Conceito, significado no contexto do texto | Glossário |
| 3. Relações | Conceito A, conceito B, relação (um verbo) | Solução Proposta, Domain Events, mapa de contextos do 0000. Vale mais que a passada 2: é a relação que dá sentido ao conceito |
| 4. Termos | Conceito, termos usados por cada especialista, significado | Glossário; conflito de vocabulário → fronteira de contexto (writing.md, Lente DDD) e termos por contexto do 0000 |
| 5. Instâncias | Classe (conceito), instâncias citadas | Usuário-alvo, exemplos dos Critérios de Aceitação |
| 6. Atributos | Classe, atributos citados na transcrição; segunda rodada: atributos usuais do domínio que não apareceram | Os ausentes viram `[PREMISSA]` a validar com o especialista, não atributos do PRD |
| 7. Motivos de mudança | Atributo; em que cenário muda; quem dispara; quem precisa saber | Máquina de estados, FRs de transição, eventos candidatos (writing.md, Lente DDD) |
| 8. Restrições | Atributo ou relação; valores válidos; cardinalidade | FRs de validação |

Termos e exemplos que não estão na transcrição não entram nas tabelas; a segunda rodada da passada 6 é o único lugar onde o conhecimento geral do domínio entra, e entra como pergunta.

## Riqueza do contexto

| Nível | Definição | Ação |
|---|---|---|
| Rico | Usuário-alvo identificado + (problema ou direção de solução) | Gere e refine |
| Sinais parciais | Bullets ou fragmentos com informação real, mesmo incompleta | Gere com `[PREMISSA]` e `[LACUNA]`; não force discovery |
| Vago | Só nome de feature, palavra única, ideia genérica | Máximo 3 perguntas: que problema real resolve? quem é o usuário-alvo? como saberemos que funcionou? |

"Problema + solução" sem usuário-alvo não é rico: é solution-first desancorado. Trate como sinais parciais e peça o usuário primeiro.

Usuário recusa discovery ("só escreve") → gere com `[LACUNA]` extensivo, Confiança `Baixa` com nota "múltiplas premissas não validadas", e ao fim liste o que precisa ser preenchido antes de qualquer próximo passo.

## Modo reverse PRD

Documentar o que já foi construído ("PRD do módulo X", "documente o que construímos"). O autor olha para código e telas, então o gradiente para descrever mecanismo é máximo; o capability test (writing.md) tem peso extra.

- Peça comportamento observável, regras aplicadas e decisões que o sistema toma. Aceite código, docs, bullets, descrição livre.
- Derive intenção a partir de resultados (o que usuário ou negócio ganha), não de operações.
- Intenção inferida é `[PREMISSA]`, marcada pesadamente: intenção engenheirada em reverso é frágil.
- Comportamento sem justificativa de negócio identificável é `[LACUNA]`: expõe feature órfã (peso morto ou valor escondido).
- Múltiplas intenções plausíveis para o mesmo comportamento → Perguntas em Aberto. Não fabrique coerência inexistente.

## Modo plataforma, infra, SDK ou API como produto

- Usuário é o time ou sistema consumidor; JTBD funciona ("integrar auth sem gerenciar estado de sessão").
- Métricas primárias são operacionais: percentis de latência, taxa de erro, adoção por consumidores, time-to-integration. Resultado de negócio é de segunda ordem, pertence aos consumidores.
- Critérios de Aceitação incluem o contrato: estabilidade da forma da API, SLA, janela de backward compatibility.
- Deprecação entra como não-objetivo ou trade-off quando relevante: interface antiga não coberta, o que não será migrado, cronograma não comprometido.

## Pesquisa

Busca web proativa para as lacunas: benchmarks e concorrentes, comportamento de usuário, tendências, padrões técnicos. Cite fontes de forma concisa: link, trecho relevante e data de leitura.

Regulação (financeiro, saúde, dados pessoais, pagamentos, segurança, KYC/AML, telecom, energia, autoridade setorial) ganha a seção Considerações Regulatórias (writing.md, Seções). Verifique a norma vigente por busca antes de incluir e marque cada linha com a tag de confiança da origem; hipótese regulatória nunca é vinculante.
