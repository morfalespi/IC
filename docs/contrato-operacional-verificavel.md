# Contrato operacional verificável do IC

## Premissa

O IC consulta somente alvos acessíveis pelas APIs oficiais do Telegram a partir de uma sessão autorizada. A autorização para iniciar uma consulta não amplia os direitos da sessão no Telegram; falhas de acesso e resultados incompletos devem ser informados, jamais preenchidos artificialmente.

## Escopo preservado

- Identificar usuário, bot, grupo ou canal acessível por username público ou ID canônico conhecido pela sessão.
- Conferir EXPECTED_ID antes da coleta e interromper em caso de divergência.
- Reunir metadados e categorias solicitadas dentro da visibilidade permitida, de limites de paginação e das restrições da API.
- Gerar arquivos locais Markdown/JSONL e pacotes de mídia verificados quando os dados realmente estiverem disponíveis.
- Enviar relatórios somente para destinos explicitamente autorizados, com proteção contra repetição incerta de envios.
- Validar sinteticamente formatos e integridade de anexos; testes controlados não são prova de acesso remoto.

## O que não é prometido

- Acesso universal por ID, histórico integral, membros não visíveis, dados privados ou privilégios administrativos.
- Leitura pelo destinatário: resposta positiva da Bot API confirma aceitação pelo servidor, não leitura ou recebimento no aplicativo.
- Bot funcionando em produção a partir de CI verde, healthcheck ou deploy sem teste no Telegram real.
- Envio ou recuperação automáticos após falha ambígua. Um envio incerto exige reconciliação manual antes de repetir.

## Revisão de integridade em 2026-11-09

A versão de main resultante do merge de PR #35 continha funções duplicadas, blocos antigos inseridos no fluxo novo e saídas enganosas. Esta recuperação restaura **18 arquivos de execução** exatamente como estavam no commit `73ff763ca75dc62c3ad07a4cbbcc23ce833a764f`, antes daquele merge defeituoso, mantendo todo o restante da branch-base. Entre as eliminações estão o bypass de limite de consultas, o registro de entradas privadas em texto aberto, a validação de anexos que alegava sucesso sem conferir bytes e os exits de erro com código 0.

A implementação é submetida novamente à CI em Pull Request. Não há credenciais reais neste commit nem contato vivo com Telegram/TgCloud; a confirmação de produção continua pendente até testes com credenciais seguras e alvos autorizados. Nenhuma execução atual deve alegar o que ainda não foi observado.
