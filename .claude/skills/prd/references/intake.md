# Avaliação do input e pesquisa

Este arquivo cobre o passo Entender do workflow descrito em SKILL.md: avaliar o escopo do pedido, extrair o que o material de discovery contém, classificar a riqueza do contexto e decidir quando pesquisar. As tags `[PREMISSA]` e `[LACUNA]` usadas aqui são as definidas em writing.md (writing.md, Tags). Quando o pedido é um reverse PRD, ou trata plataforma, infra, SDK e API como produto, aplique também o que muda em modes.md.

## Escopo problemático

Antes de gerar, verifique se o escopo do pedido comporta um PRD. Três sintomas pedem intervenção antes de qualquer geração:

| Sintoma | Ação |
|---|---|
| Muito amplo: domínio inteiro ou duas ou mais iniciativas sem corte (ex.: "plataforma de crédito") | Não gere. Peça um corte específico ou proponha um corte para o usuário validar |
| Enquadrado como implementação (ex.: "PRD para o microserviço X", "PRD para a tela Y") | Redirecione: o PRD começa do problema, não da implementação |
| CRUD ou entidade-cêntrico (ex.: "CRUD para X", "tela de cadastro para Y") | Redirecione com duas perguntas: que capability ou JTBD isso serve? Que decisão de negócio acontece ali? Problemas são vividos por pessoas, não por tabelas precisando de telas |

Em qualquer um dos três casos, faça ao usuário a pergunta de base: que problema de usuário ou de negócio essa implementação resolve?

## Material de discovery

Documentos recebidos como input (PDF, docx, decks, atas, briefs e PRDs antigos) são ricos em sinais, mas não são fonte autoritativa. Trate-os assim:

- **Extraia antes de perguntar.** Levante do material os sinais que o PRD precisa (problema, evidência, usuário-alvo, direção, métricas, restrições) antes de fazer qualquer pergunta ao usuário.
- **Inferência do discovery é `[PREMISSA]`.** O que você deduz do documento entra como `[PREMISSA]` derivada dele. Texto sem tag (fato) só cabe quando a fonte é autoritativa: regulação oficial, política formalizada, decisão registrada.
- **Sintetize, não reformate.** Reorganizar o material cosmeticamente produz um PRD bonito e falso. Teste: nenhuma frase de 12 ou mais palavras do PRD é encontrável por busca literal no material de origem.
- **PRD antigo pede classificação.** Diante de um PRD antigo, determine qual é o caso: (a) ele serve de reverse PRD para um incremento, (b) ele é o documento a atualizar no lugar, ou (c) ele é só inspiração. Se o material não permitir escolher entre os três, pergunte antes de gerar.
- **Fontes conflitantes viram `[LACUNA]`.** Quando duas fontes se contradizem, registre a `[LACUNA]` com pedido de reconciliação. Não escolha um lado em silêncio.

## Riqueza do contexto

Conte quais dos seis sinais (problema, evidência, usuário-alvo, direção, métricas, restrições) o contexto recebido traz, classifique-o em um dos três níveis e siga a ação correspondente:

| Nível | Definição | Ação |
|---|---|---|
| Rico | Usuário-alvo identificado + (problema ou direção de solução) | Gere o PRD e refine com o usuário |
| Sinais parciais | Pelo menos um sinal presente, sem o par que define Rico | Gere com `[PREMISSA]` e `[LACUNA]`; não force discovery |
| Vago | Nenhum sinal: só nome de feature, palavra única ou ideia genérica | Faça no máximo 3 perguntas: que problema real resolve? quem é o usuário-alvo? como saberemos que funcionou? |

### Casos de borda

- **Solução sem usuário-alvo não é contexto rico.** "Problema + solução" sem usuário-alvo identificado é solution-first desancorado. Trate como sinais parciais e peça o usuário-alvo antes de qualquer outra pergunta.
- **Recusa de discovery não bloqueia a geração.** Quando o usuário recusa as perguntas ("só escreve"), gere marcando `[LACUNA]` em cada um dos seis sinais que faltam e siga. Ao fim, liste o que precisa ser preenchido antes de qualquer próximo passo.

## Pesquisa

Faça busca web quando o pedido exige: benchmarks e concorrentes, comportamento de usuário, tendências, padrões técnicos, norma vigente. Cite cada fonte em uma linha: link, trecho relevante e data de leitura.

### Regulação

Em domínio regulado (financeiro, saúde, dados pessoais, pagamentos, segurança, KYC/AML, telecom, energia, ou outro sob autoridade setorial), a seção Considerações Regulatórias entra só quando a norma foi identificada e lida; a forma da seção está em writing.md (writing.md, Seções). Verifique por busca qual é a norma vigente antes de incluí-la. Artigo cuja redação não foi conferida no texto da norma é `[PREMISSA]`, e hipótese regulatória nunca é vinculante.
