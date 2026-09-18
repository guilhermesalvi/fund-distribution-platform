# Código de testes

Vale para criação e revisão de testes.

## Casos e nomes

Nomeie testes em snake_case, descrevendo o comportamento, por exemplo `Failing_operation_records_error_and_exception_then_rethrows`. Teste lógica de domínio; getters e setters triviais não precisam de testes próprios.

Derive testes dos requisitos e cenários pertinentes. Um teste novo de comportamento deve falhar sem a implementação; um teste de caracterização fixa o comportamento existente. Não escreva testes que apenas reproduzam a implementação ou verifiquem uma edição trivial de texto.

Não afrouxe uma asserção para ocultar falha; se o teste estiver incorreto, corrija-o a partir da fonte do comportamento. Se a regra de negócio não estiver definida, registre a lacuna em vez de deduzi-la do resultado que faz o teste passar.

## Processamento do livro

A tabela de [Acceptance Criteria do PRD 0003](../docs/prd/0003-book-building-book-processing.md#acceptance-criteria) é a fonte dos casos de processamento: cada linha corresponde a um teste com as mesmas entradas e o mesmo resultado, e o teste cita o nome do caso para ser encontrado por busca. Ao implementar o processamento, crie esses testes; depois, altere-os junto com a tabela.
