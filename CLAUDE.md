# Convenções do repositório

Plataforma demonstrativa em .NET 10 e Aspire. O [README](README.md) descreve o estado técnico e o [PRD 0000](docs/prd/0000-platform-overview.md) apresenta o contrato do produto.

O projeto é pessoal e não recebe contribuições externas. O README apresenta a solução, seu estado técnico, setup e execução; não inclua convites para contribuir nem instruções de fork ou clonagem como fluxo de contribuição.

## Leitura por tarefa

- Código de produção, inclusive revisão sem edição: [src/CLAUDE.md](src/CLAUDE.md).
- Código de testes: [tests/CLAUDE.md](tests/CLAUDE.md).
- Requisitos de produto: [docs/prd/CLAUDE.md](docs/prd/CLAUDE.md) e o PRD da capability afetada.
- Setup e execução local: [README](README.md).
- Mudança de comportamento, nome ou fronteira: consulte os requisitos, decisões e histórico pertinentes. Uma edição localizada não exige ler todos os documentos.

Execute os comandos do repositório a partir da raiz, mesmo quando a tarefa começar em um subdiretório. O Claude Code carrega ao iniciar o `CLAUDE.md` do diretório de trabalho e dos ancestrais, e o de um subdiretório quando lê um arquivo ali. Antes de atuar em outra área, inclusive em revisão sem edição, leia o `CLAUDE.md` dela. Em cada diretório, o `CLAUDE.local.md` entra depois do `CLAUDE.md` e fica fora do Git.

## Instruções e skills do Claude Code

Cada regra tem uma única fonte, escolhida pelo objeto que governa: convenções gerais neste arquivo, código de produção em `src/CLAUDE.md`, testes em `tests/CLAUDE.md` e documentos gerados por uma skill na própria skill. Git, commits e publicação ficam só neste arquivo. Outras áreas seguem o mesmo critério de responsabilidade. Ao mover uma regra, retire a definição anterior.

Não repita nem cite regra já carregada, como as deste arquivo, sempre em contexto, e as do `CLAUDE.md` da área em que Claude trabalha. Cite outra fonte só quando o leitor precisar lê-la para agir, e prefira o nome estável (skill, arquivo, ID, rótulo de contrato ou evento) a caminhos com âncora de seção.

As skills `ai-skills:prd` (produto) e `ai-skills:sdd` (trabalho técnico) vêm do plugin `ai-skills`, instalado no ambiente do usuário. Invoque `/ai-skills:prd` e `/ai-skills:sdd`; Claude também pode selecioná-las pela descrição. Correções mecânicas de documentação não usam esses fluxos. A instalação está no README; o repositório não mantém cópias das skills.

Se uma instrução ou skill não aparecer, confira o diretório de início, os Memory files listados por `/context`, os `CLAUDE.local.md` aplicáveis, as instruções globais em `~/.claude`, o menu `/` e `/plugin`. Verifique cópias duplicadas em `.claude/skills` e `~/.claude/skills`. Após mudar instruções, skills ou agentes, inicie uma nova sessão para verificar o carregamento. Permissões, credenciais, hooks e servidores MCP pertencem ao ambiente do usuário; não copie configurações pessoais para o projeto.

## Subagentes e modelos

Delegue subtarefas independentes quando houver trabalho útil para executar em paralelo. Use `planner` para planejamento, decisões com incerteza e revisão de mudanças complexas; use `worker` para execução delimitada com critérios de conclusão claros. Delegue pelo nome do papel, com `@agent-planner` e `@agent-worker` ou pela descrição; os modelos e esforços estão em `.claude/agents/`. Tarefas simples podem ser concluídas pelo agente principal.

Ao delegar, informe objetivo, arquivos sob responsabilidade, instruções aplicáveis e verificações esperadas. Evite dois agentes editando o mesmo arquivo. O agente principal integra e revisa os resultados e concentra operações Git. Se o executor encontrar uma decisão não resolvida ou não conseguir cumprir os critérios, devolva o ponto ao planejador antes de repetir tentativas. Se o cliente não permitir selecionar papéis, escolha explicitamente os modelos dos respectivos arquivos; se não oferecer esses modelos ou subagentes, informe a limitação e prossiga com a capacidade disponível.

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
- `docs/prd`: visão geral e um PRD por capability.

Planos, specs e demais artefatos técnicos ficam onde a skill `sdd` define.

Todo arquivo versionado aparece no Solution Explorer. Arquivos internos a projetos são exibidos pelo projeto; os demais entram no `FundDistributionPlatform.slnx`, exceto o próprio `.slnx`. Arquivos na raiz ficam em `/SolutionItems/`. Cada diretório documental vira `<Folder Name="/caminho/completo/">`, inclusive pais vazios. Cada arquivo usa `<File Path="caminho/relativo" />`; os projetos ficam em `/src/` e `/tests/`, sem pasta própria por projeto. Ordene pastas e itens alfabeticamente, sem distinção de caixa.

Ao criar, mover ou remover arquivos, atualize o `.slnx` na mesma mudança. Confira arquivos rastreados e novos contra o inventário; nenhuma entrada pode apontar para caminho ausente ou ignorado. Não inclua `bin`, `obj`, caches nem artefatos temporários.

## Verificação

Para mudanças em produção ou testes .NET, execute o build e os testes da solução como a CI em `.github/workflows/ci.yml`. Ao mudar comandos da CI, atualize o README.

Em mudanças documentais, confira links, âncoras e o `.slnx`; não execute .NET quando código, configuração e dependências não mudam. Reutilize evidência válida para a mesma versão e repita só os checks afetados por uma mudança ou falha. Informe as verificações não executadas e o motivo.

Antes de citar branches ou tags na documentação, confira sua existência no repositório local e no remoto pertinente. Ao remover ou renomear arquivos ou referências Git, corrija os links e as instruções que dependem deles.
