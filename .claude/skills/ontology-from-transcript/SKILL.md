---
name: ontology-from-transcript
description: 'Extrai a ontologia de um domínio a partir de transcrições de reunião com especialistas, em oito passadas separadas (correção, conceitos, relações, termos, instâncias, atributos, motivos de mudança, restrições), uma tabela por passada, tudo como hipótese até o especialista validar. TRIGGER: "transcrição da reunião com o especialista", "extraia os conceitos/termos/relações da transcrição", "ontologia do domínio", "glossário a partir da gravação", "linguagem ubíqua a partir da conversa" e equivalentes. NÃO acionar para escrever o documento final (PRD, spec, glossário publicado), para ata ou resumo de reunião, nem quando não há transcrição ou texto de especialista como matéria-prima.'
---

# Ontologia a partir de transcrições

Reunião com especialista de domínio se grava e se transcreve; a transcrição é a matéria-prima da linguagem do domínio. Não pule da transcrição para regras ou classes: o salto é grande demais e esconde o erro de entendimento. Extraia em passadas separadas, uma por prompt, porque cada passada recebe o orçamento inteiro de atenção e o resultado de uma alimenta a seguinte. Tudo que sai daqui é hipótese derivada da transcrição até o especialista validar; quem consome as tabelas marca isso na convenção do artefato de destino.

## Passadas

| Passada | Tabela | Alimenta |
|---|---|---|
| 1. Correção | Termos e nomes mal transcritos, com a leitura provável | As demais passadas |
| 2. Conceitos | Conceito, significado no contexto do texto | Glossário |
| 3. Relações | Conceito A, conceito B, relação (um verbo) | Modelo do domínio, eventos, mapa de contextos. Vale mais que a passada 2: é a relação que dá sentido ao conceito |
| 4. Termos | Conceito, termos usados por cada especialista, significado | Glossário; conflito de vocabulário entre especialistas é indício de fronteira entre contextos, não de erro |
| 5. Instâncias | Classe (conceito), instâncias citadas | Atores, exemplos e cenários de aceitação |
| 6. Atributos | Classe, atributos citados na transcrição; segunda rodada: atributos usuais do domínio que não apareceram | Os ausentes viram perguntas ao especialista, não atributos do modelo |
| 7. Motivos de mudança | Atributo; em que cenário muda; quem dispara; quem precisa saber | Máquina de estados, regras de transição, eventos candidatos |
| 8. Restrições | Atributo ou relação; valores válidos; cardinalidade | Regras de validação |

## Regras

- Termos e exemplos que não estão na transcrição não entram nas tabelas; a segunda rodada da passada 6 é o único lugar onde o conhecimento geral do domínio entra, e entra como pergunta.
- Cada passada é validável com o especialista antes da seguinte; não avance sobre tabela contestada.
- Sinônimos: quando especialistas usam termos diferentes para o mesmo conceito, escolha um canônico e registre os demais na passada 4. Mesmo termo para conceitos diferentes é fronteira entre contextos: não unifique.
- A saída de cada passada é a tabela, sem prosa em volta; a interpretação é do especialista e de quem escreve o artefato de destino.
