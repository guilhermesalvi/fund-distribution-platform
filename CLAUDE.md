# Convenções do repositório

Plataforma demonstrativa em .NET 10 e Aspire. O [README](README.md) descreve o estado técnico, e as specs das capabilities em `docs/specs` definem o contrato do produto.

O projeto é pessoal e não recebe contribuições externas. O README apresenta a solução, seu estado técnico, setup e execução; não inclua convites para contribuir nem instruções de fork ou clonagem como fluxo de contribuição.

## Leitura por tarefa

- Código de produção, inclusive revisão sem edição: leia [src/CLAUDE.md](src/CLAUDE.md) antes de atuar em `src/`.
- Código de testes: leia [tests/CLAUDE.md](tests/CLAUDE.md) antes de atuar em `tests/`.
- Requisitos e comportamento: a spec da capability afetada, conforme a skill `sdd`.
- Setup e execução local: [README](README.md).
- Mudança de comportamento, nome ou fronteira: consulte os requisitos, decisões e histórico pertinentes. Uma edição localizada não exige ler todos os documentos.

Execute os comandos do repositório a partir da raiz, mesmo quando a tarefa começar em um subdiretório. O Claude Code carrega ao iniciar o `CLAUDE.md` do diretório de trabalho e dos ancestrais; o de um subdiretório abaixo dele entra no contexto só quando Claude lê, escreve ou edita um arquivo ali. Para tratar de uma área sem tocar seus arquivos, ou ao passar a atuar em outra área durante a sessão, leia primeiro o `CLAUDE.md` dela.

## Instruções e skills do Claude Code

Cada regra tem uma única fonte, escolhida pelo objeto que governa: convenções gerais neste arquivo, código de produção em `src/CLAUDE.md`, testes em `tests/CLAUDE.md` e documentos gerados por uma skill na própria skill. Git, commits e publicação ficam só neste arquivo. Outras áreas seguem o mesmo critério de responsabilidade. Ao mover uma regra, retire a definição anterior.

Não repita nem cite regra já carregada. Cite outra fonte só quando o leitor precisar lê-la para agir, e prefira o nome estável (skill, arquivo, ID, rótulo de contrato ou evento) a caminhos com âncora de seção.

A skill `sdd` vem do plugin `ai-skills`, instalado na conta; invoque-a com `/ai-skills:sdd` ou pela descrição. O repositório não versiona cópias dessa skill. Correções mecânicas de documentação não usam esse fluxo. Se a skill necessária não estiver disponível, informe a lacuna e siga o setup do [README](README.md); não invente seu contrato.

## Escopo e decisões

Conclua o trabalho pedido: um pedido de planejamento termina no plano; uma implementação termina com a mudança verificada. Corrija o que a sua mudança quebrar e os problemas preexistentes do trecho alterado que tenham o mesmo motivo da mudança; os demais entram como sugestão no fim, sem alteração. Decida escolhas técnicas reversíveis dentro do escopo. Pergunte quando faltar uma decisão indispensável de produto ou informação que o contexto não resolve; continue o trabalho independente.

As instruções da sessão prevalecem sobre os defaults das skills, respeitadas as restrições do ambiente. Não altere convenções nem desative proteções para contornar essas restrições; se uma regra local parecer impedir o trabalho, confira sua precedência e informe o arquivo, a regra e a ação afetada.

Em decisões de contrato, fronteira ou localização de regra, defina a necessidade concreta, compare as alternativas pelos mesmos critérios e explicite o custo da escolha; nas demais, decida e siga. Uma escolha simples não exige um novo documento. Não acrescente complexidade sem necessidade concreta. Build e testes aprovados não decidem uma questão de produto.

## Idioma e commits

Prosa e instruções em português. Código, identificadores, comentários, logs, erros, nomes de arquivos e commits em inglês. Preserve títulos e rótulos que sejam contratos de artefatos e IDs existentes.

Mensagens de commit usam `<type>: <description_in_english>`, com no máximo 60 caracteres, descrição no imperativo e inicial minúscula. Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`, `style`, `revert`. Sem escopo, ponto final, `!`, corpo ou trailers; breaking changes são explicados na PR.

Agrupe por motivo: código, testes e documentação da mesma mudança ficam juntos; motivos independentes ficam separados. Cada commit deve ser consistente e verificável. Use a identidade Git do usuário. Se faltar identidade, informe a lacuna; uma identidade fornecida para a tarefa pode ser passada com `git -c user.name=... -c user.email=... commit`, sem alterar a configuração global.

Trabalhe na `main`. Não crie branches auxiliares nem recrie branches ou tags removidas para arquivar histórico. Ao concluir uma alteração pedida, faça commit na `main`; arquivos de trabalho podem ser lidos, testados e revisados antes do commit. Push, deploy e reescrita de histórico exigem pedido explícito na tarefa; sem reescrita pedida, use push normal. Preserve alterações alheias.

## Estrutura e inventário

- `src/AppHost`: entrada de execução local e topologia do Aspire.
- `src/ServiceDefaults`: defaults transversais dos hosts e das APIs.
- `src/Offering`, `src/BookBuilding`: serviços dos contextos de domínio.
- `src/DataMigration`: worker sem HTTP nem Native AOT.
- `tests/UnitTests`: xUnit, lógica sem host; domínio futuro organizado por contexto.
- `tests/IntegrationTests`: xUnit e `Aspire.Hosting.Testing`; exige Aspire CLI porque o AppHost usa `AspireUseCliBundle`.
- `docs/adr`: decisões que valem para mais de uma capability.
- `docs/specs`: uma spec por capability, fonte canônica do produto.

Planos, specs e demais artefatos técnicos ficam onde a skill `sdd` define. A numeração dos requisitos recomeçou no commit `37442173`: ao conferir que um ID novo nunca existiu, busque só a partir dele, com `git log -S "<ID>" 37442173..`.

Todo arquivo versionado aparece no Solution Explorer. Arquivos internos a projetos são exibidos pelo projeto; os demais entram no `FundDistributionPlatform.slnx`, exceto o próprio `.slnx`. Arquivos na raiz ficam em `/SolutionItems/`. Cada diretório documental vira `<Folder Name="/caminho/completo/">`, inclusive pais vazios. Cada arquivo usa `<File Path="caminho/relativo" />`; os projetos ficam em `/src/` e `/tests/`, sem pasta própria por projeto. Ordene pastas e itens alfabeticamente, sem distinção de caixa.

Ao criar, mover ou remover arquivos, atualize o `.slnx` na mesma mudança. Confira arquivos rastreados e novos contra o inventário; nenhuma entrada pode apontar para caminho ausente ou ignorado. Não inclua `bin`, `obj`, caches nem artefatos temporários.

## Verificação

Para mudanças em produção ou testes .NET, execute o build e os testes da solução como a CI em `.github/workflows/ci.yml`. Ao mudar comandos da CI, atualize o README.

Em mudanças documentais, confira links, âncoras e o `.slnx`; não execute .NET quando código, configuração e dependências não mudam. Reutilize evidência válida para a mesma versão e repita só os checks afetados por uma mudança ou falha. Informe as verificações não executadas e o motivo.

Antes de citar branches ou tags na documentação, confira sua existência no repositório local e no remoto pertinente. Ao remover ou renomear arquivos ou referências Git, corrija os links e as instruções que dependem deles.
