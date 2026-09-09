# Avaliação do input e pesquisa

Passos 1 e 2 do workflow. Tags usadas aqui: writing.md, Tags. Quando o pedido é reverse PRD ou plataforma, infra, SDK e API como produto: modes.md.

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
- Inferência do discovery é `[PREMISSA]` derivada do documento. Sem tag (fato) só para fonte autoritativa: regulação oficial, política formalizada, decisão registrada.
- Sintetize, não reformate: reorganização cosmética produz PRD bonito e falso.
- Diante de PRD antigo, determine se ele é (a) reverse PRD para incremento, (b) update a fazer no lugar ou (c) inspiração. Pergunte se ambíguo.
- Fontes conflitantes viram `[LACUNA]` com pedido de reconciliação. Não escolha um lado em silêncio.

## Riqueza do contexto

| Nível | Definição | Ação |
|---|---|---|
| Rico | Usuário-alvo identificado + (problema ou direção de solução) | Gere e refine |
| Sinais parciais | Bullets ou fragmentos com informação real, mesmo incompleta | Gere com `[PREMISSA]` e `[LACUNA]`; não force discovery |
| Vago | Só nome de feature, palavra única, ideia genérica | Máximo 3 perguntas: que problema real resolve? quem é o usuário-alvo? como saberemos que funcionou? |

"Problema + solução" sem usuário-alvo não é rico: é solution-first desancorado. Trate como sinais parciais e peça o usuário primeiro.

Quando o usuário recusa discovery ("só escreve"), gere com `[LACUNA]` extensivo e siga; ao fim, liste o que precisa ser preenchido antes de qualquer próximo passo.

## Pesquisa

Busca web quando o pedido a exige: benchmarks e concorrentes, comportamento de usuário, tendências, padrões técnicos, norma vigente. Cite fontes de forma concisa: link, trecho relevante e data de leitura.

Regulação (financeiro, saúde, dados pessoais, pagamentos, segurança, KYC/AML, telecom, energia, autoridade setorial) ganha a seção Considerações Regulatórias só com norma identificada e lida (writing.md, Seções). Verifique a norma vigente por busca antes de incluir; artigo não conferido no texto é `[PREMISSA]`, e hipótese regulatória nunca é vinculante.
