# Segurança do Infocard

## Estado do projeto

O repositório morfalespi/IC é público. As execuções GitHub Actions também podem tornar visíveis metadados e logs. O fluxo de workflow_dispatch passa username/ID pesquisado, expected_id e chat/message_id como inputs; por isso **não é um transporte de dados de consulta confidencial**.

Não fazer pesquisas de dados sensíveis de terceiros por esta arquitetura supondo sigilo. Para proteção de consultas privadas será necessário projetar um transporte autenticado que não publique o contexto em workflows visíveis e decidir retenção mínima, controles de acesso e exclusão.

## Credenciais

Não versionar TGCLOUD_TOKEN, GH_DISPATCH_TOKEN, API_ID, API_HASH, BOT_TOKEN, sessões MTProto ou access_hash. O arquivo tgcloud/lib/segredos.js deve permanecer no Git apenas com placeholders vazios. Durante o deploy, o GH_DISPATCH_TOKEN é injetado no módulo publicado no Telegram Serverless; proteger a conta do bot, acesso ao runtime e política de rotação.

Usar permissões mínimas para GH_DISPATCH_TOKEN e rotacionar qualquer segredo exposto em commits, prints, issues ou logs públicos. Não adicionar secrets a documentação ou mensagens de diagnóstico.

## Dados

Mostrar somente campos efetivamente retornados pelas APIs e permitidos pela privacidade. Campo ausente não comprova inexistência. Os recursos de Rich Messages e Markdown não concedem maior acesso a dados.

Não criar coletores de terceiros, bancos de perfis ou cache persistente sem revisão explícita de finalidade, privacidade, segurança e consentimentos pertinentes.

## Relatar problemas

Descrever a falha e o link do run com informações sensíveis omitidas. Não colocar IDs privados, telefones, tokens ou documentos pessoais em issues públicas. Usar canal privado autorizado pelo proprietário do projeto para vulnerabilidades.
