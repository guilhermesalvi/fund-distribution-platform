# Convenções do repositório

Plataforma demonstrativa em .NET 10 e Aspire. O [README](README.md) descreve o estado técnico, e as specs das capabilities em `docs/specs` definem o contrato do produto.

O projeto é pessoal e não recebe contribuições externas. O README apresenta a solução, seu estado técnico, setup e execução; não inclua convites para contribuir nem instruções de fork ou clonagem como fluxo de contribuição.

## Leitura por tarefa

- Código de produção, inclusive revisão sem edição: [src/CLAUDE.md](src/CLAUDE.md).
- Código de testes: [tests/CLAUDE.md](tests/CLAUDE.md).
- Requisitos e comportamento: a spec da capability afetada, conforme a skill `sdd`.
- Setup e execução local: [README](README.md).
- Mudança de comportamento, nome ou fronteira: consulte os requisitos, decisões e histórico pertinentes. Uma edição localizada não exige ler todos os documentos.

Execute os comandos do repositório a partir da raiz, mesmo quando a tarefa começar em um subdiretório. O `CLAUDE.md` de um subdiretório entra no contexto quando a sessão começa nele ou abaixo dele, ou quando Claude lê um arquivo ali; para tratar de uma área sem ler seus arquivos, leia antes o `CLAUDE.md` dela.

## Instruções e skills do Claude Code

Cada regra tem uma única fonte, escolhida pelo objeto que governa: convenções gerais neste arquivo, código de produção em `src/CLAUDE.md`, testes em `tests/CLAUDE.md` e documentos gerados por uma skill na própria skill. Git, commits e publicação ficam só neste arquivo. Outras áreas seguem o mesmo critério de responsabilidade. Ao mover uma regra, retire a definição anterior.

Não repita nem cite regra já carregada, como as deste arquivo, sempre em contexto, e as do `CLAUDE.md` da área em que Claude trabalha. Cite outra fonte só quando o leitor precisar lê-la para agir, e prefira o nome estável (skill, arquivo, ID, rótulo de contrato ou evento) a caminhos com âncora de seção.

A skill `sdd` vem do plugin `ai-skills`, instalado na conta, e é invocada com `/ai-skills:sdd` ou pela descrição. Correções mecânicas de documentação não usam esse fluxo.

<!--
Notas de manutenção. Comentários HTML em bloco não entram no contexto do Claude Code.

- Carregamento: o Claude Code carrega ao iniciar o CLAUDE.md do diretório de trabalho e dos ancestrais, e o de um subdiretório quando lê arquivos nele (https://code.claude.com/docs/en/memory). Não recriar docs/development para essas orientações.
- Skills: sdd vem do plugin ai-skills@ai-skills, instalado no escopo do usuário; o repositório não versiona skills (https://code.claude.com/docs/en/plugins).
- Instrução ou skill ausente: conferir o diretório de início, os Memory files em /context, o menu / e o plugin ai-skills em /plugin; reiniciar a sessão.
- Duplicidade ou divergência: conferir ~/.claude/CLAUDE.md, CLAUDE.local.md, ~/.claude/skills e plugins da conta antes de editar o projeto. Skill pessoal ou de projeto de mesmo nome carrega junto com a do plugin e responde por /sdd; a do plugin continua em /ai-skills:<skill> (https://code.claude.com/docs/en/skills). Não copiar configurações pessoais para compensar falha de carregamento.
- Permissões, hooks e servidores MCP ficam nas configurações do Claude Code (https://code.claude.com/docs/en/settings e https://code.claude.com/docs/en/permissions). Um .claude/settings.json compartilhado precisa de necessidade concreta; CLAUDE.local.md e .claude/settings.local.json ficam fora do Git.
- Após mudar instruções ou skills, conferir em sessões novas, pelos Memory files de /context: revisão de produção iniciada na raiz e em src/Offering; revisão de testes em tests; revisão editorial em docs/specs; seleção de /ai-skills:sdd conforme o pedido, sem acioná-la em correções mecânicas de README. Registrar o comportamento observado, não apenas a presença dos arquivos no contexto.
-->

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

Planos, specs e demais artefatos técnicos ficam onde a skill `sdd` define.

Todo arquivo versionado aparece no Solution Explorer. Arquivos internos a projetos são exibidos pelo projeto; os demais entram no `FundDistributionPlatform.slnx`, exceto o próprio `.slnx`. Arquivos na raiz ficam em `/SolutionItems/`. Cada diretório documental vira `<Folder Name="/caminho/completo/">`, inclusive pais vazios. Cada arquivo usa `<File Path="caminho/relativo" />`; os projetos ficam em `/src/` e `/tests/`, sem pasta própria por projeto. Ordene pastas e itens alfabeticamente, sem distinção de caixa.

Ao criar, mover ou remover arquivos, atualize o `.slnx` na mesma mudança. Confira arquivos rastreados e novos contra o inventário; nenhuma entrada pode apontar para caminho ausente ou ignorado. Não inclua `bin`, `obj`, caches nem artefatos temporários.

## Verificação

Para mudanças em produção ou testes .NET, execute o build e os testes da solução como a CI em `.github/workflows/ci.yml`. Ao mudar comandos da CI, atualize o README.

Em mudanças documentais, confira links, âncoras e o `.slnx`; não execute .NET quando código, configuração e dependências não mudam. Reutilize evidência válida para a mesma versão e repita só os checks afetados por uma mudança ou falha. Informe as verificações não executadas e o motivo.

Antes de citar branches ou tags na documentação, confira sua existência no repositório local e no remoto pertinente. Ao remover ou renomear arquivos ou referências Git, corrija os links e as instruções que dependem deles.
