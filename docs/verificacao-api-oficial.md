# Auditoria operacional do IC em relação à Bot API atual

**Fonte de regras:** páginas Markdown recuperadas em tempo de execução do domínio oficial `core.telegram.org`. O workflow registra URL e SHA-256 de cada documento lido. O código anterior, o arquivo local de contratos e os resultados históricos não são referências normativas.

**Escopo descoberto:** o auditor encontra referências candidatas a métodos Bot API em `scripts/` e `tgcloud/`. O inventário é estático e pode conter nomes internos, omitir chamadas dinâmicas ou não representar efetivamente todos os caminhos. Métodos presentes no índice oficial têm a documentação individual consultada; ausência de página fica como *não comprovado*, sem concluir que o método é inválido.

**Execução observada:** um fixture HTTP local responde a seis operações realmente emitidas por `BotClient`: `getMe`, `getChat`, `sendMessage`, `sendPhoto`, `sendDocument` e `getFile`. Os contratos de parâmetros e respostas vêm das tabelas oficiais atuais. Nomes e tipos sem validador, regras condicionais, limites, restrições de sessão e comportamento de Telegram real **não** recebem aprovação por omissão. O teste tem casos negativos para uma chave inexistente e para um campo requerido omitido.

**Códigos de saída e evidências:**
- `0`: reservado para conformidade integral efetivamente demonstrável; o auditor atual não declara esse estado.
- `1`: divergência detectada nas regras verificadas.
- `2`: incompleto ou inconclusivo (documentação ausente, interpretação insuficiente, fluxos não exercitados ou execução não realizada).

A **falha do job por saída 2 é intencional** e não significa que todos os métodos estejam incorretos. Significa que não há base suficiente para classificar o escopo completo como comprovado. Uma eventual redução das lacunas exige ampliar a execução e as verificações e registrar as evidências, não diminuir a lista de obrigações arbitrariamente.

A documentação não executa nem aprova código: o auditor compara interpretações implementadas localmente com documentos oficiais consultados no momento do job. Nenhum token real do Telegram é necessário; portanto, este workflow **não prova** autenticação, permissões, entrega nem funcionamento em produção. Dados de terceiros não fazem parte do teste.

**Referência do workflow:** `.github/workflows/official-api-conformance.yml`. A execução está no Pull Request #36, ainda sem merge e sem publicação.
