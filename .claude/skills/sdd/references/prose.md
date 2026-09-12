# Escrita dos artefatos SDD

## Convenções de escrita

Comece pelo comportamento, decisão, entregável ou resultado que o leitor precisa compreender. Acrescente a justificativa e a evidência pertinentes. Evite introduções que apenas anunciem o assunto e conclusões que repitam o parágrafo anterior.

Desenvolva uma ideia por parágrafo. Agrupe as frases que explicam a mesma decisão e separe decisões independentes. Preserve o contexto necessário para entender uma restrição, um custo ou um risco.

Identifique a ação e seu responsável quando conhecidos. Use termos do projeto e resultados definidos nas fontes. Um adjetivo como “robusto” não substitui um mecanismo, uma condição de falha ou um critério de teste. Informação ausente segue as regras de premissas e lacunas; a edição não pode inventar comportamento.

Mantenha nomes de APIs, tipos, erros, eventos, paths e IDs exatamente como nas fontes. Preserve keywords EARS, modalidade, negações, comparadores, unidades, prazos e exceções. Simplificar a frase não autoriza mudar o contrato.

Use prosa para contexto e justificativas, listas para requisitos e passos, e tabelas para decisões comparáveis, interfaces e evidências. Mantenha os campos e headings exigidos pelo artefato. Formatação adicional só é útil quando ajuda a distinguir informações diferentes.

Evite frases prontas, rótulos inventados e contraposições sem alternativa real. Limites de autorização, segurança e escopo continuam explícitos. Remova o excesso retórico sem apagar a restrição.

## Texto de instruções

Declare a condição, a ação e a saída quando o procedimento depender de uma decisão. Coloque a exceção junto da regra ou cite seu arquivo e heading. Use passos para sequências e tabelas para alternativas de execução. Não imponha esse formato a toda explicação.

Referências vagas devem ser substituídas pelo objeto concreto. A task define as interfaces de que precisa; a spec e o design continuam sendo fontes do comportamento e das decisões. Referencie a seção necessária, sem mandar ler documentos não relacionados à entrada.

## Texto do artefato

Aplique a forma própria de cada entrada: `specify.md`, `design.md`, `tasks.md` e `adr.md`. Para comunicações de execução e evidência, use execute.md e verify.md. Idioma, aprovações e pré-requisitos seguem workflow.md. A validação segue validation.md.

As convenções editoriais não substituem campos, requisitos EARS, rastreabilidade ou evidência. Exemplos ilustram a escrita; seus dados e resultados não se tornam fatos de uma mudança real.

## Checklist editorial

Na revisão já prevista, confira: ponto principal identificável; unidade do parágrafo; ação e responsável claros; resultado verificável quando exigido; vocabulário e modalidade preservados; incerteza visível; referência resolvível; formatação funcional; ausência de repetição sem valor.

Não criar nota, seção ou rodada exclusiva para esta lista. Se a revisão revelar uma decisão de comportamento pendente, seguir o retorno ao artefato de origem definido no workflow. O texto não pode resolver essa decisão por conta própria.
