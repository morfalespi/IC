# AGENTS.md

Orientação para assistentes de IA e pessoas neste repositório. As afirmações técnicas sobre o que funciona ficam em `docs/registro.md`, com data, condição e evidência. Este arquivo não é prova de que algo funciona.

## O que é

Bot de Telegram no Telegram Serverless. Recebe `@username` ou ID numérico, no privado ou inline, e apresenta os dados que a API disponibiliza para a entidade consultada. Sem Mini App nem endpoints. O banco tem a tabela `disparos`.

## Regras do dono (DECISÃO)

- Sem comentários no código.
- Sem testes escritos por quem escreveu o código. A verificação é a execução real: deploy e Actions.
- Não afirmar como fato o que não tenha fonte verificável. Dizer o que não foi verificado.
- Nenhuma falha silenciosa: todo erro chega a quem usou, com a causa.
- Publicar direto na `main`. Cada push em `tgcloud/**` vai ao ar.
- Um problema por vez: identificar o comportamento atual, definir o esperado, corrigir, verificar, conferir regressões.
- Fontes: `docs/Serverless-OFFICIAL`, `docs/tgcloud-sdk.md`, a documentação do Bot API em `romastefale/loggerview` (`biblioteca/core-telegram-org-bots-api`), `romastefale/td`, `romastefale/mtproto` e `romastefale/abafigurinhas` como referência.

## Classificação das afirmações

VERIFICADO, IMPLEMENTADO, HIPÓTESE e DECISÃO, como definido em `docs/registro.md`. Um deploy concluído não prova que as funções estão corretas. Comentários não são requisitos: confira o código e a documentação antes de confiar.

## Estrutura

| Caminho | O que é |
|---|---|
| `tgcloud/handlers/` | Um arquivo por tipo de update: `message.js`, `inline_query.js`. Sem subpastas. |
| `tgcloud/lib/` | Módulos compartilhados. |
| `tgcloud/schema.js` | Schema do banco (`disparos`). A plataforma recusa módulo vazio. |
| `.github/workflows/deploy.yml` | Publica a cada push em `main` que altera `tgcloud/**` e arquivos de configuração. |
| `.github/workflows/resolver.yml` | Busca por MTProto com `scripts/resolver.py`. O bot o dispara em `lib/despacho.js`. |
| `tgcloud/lib/segredos.js` | No git só tem valor vazio. O `deploy.yml` o sobrescreve no runner com o secret `GH_DISPATCH_TOKEN` antes do `push`. Nunca commitar o token. |
| `docs/registro.md` | O que foi verificado, implementado, hipótese e decisão. |
| `.tgcloud/` | Estado do CLI. Nunca editar nem ler. |

Só `.js` dentro de `tgcloud/` vai para a nuvem.

## Regras do runtime (documentação do Serverless)

- Importar módulos do projeto por caminho relativo com `.js`; o SDK pelo nome (`'sdk'`, `'sdk/db'`).
- Sem sistema de arquivos e sem pacotes npm.
- O handler recebe o payload do update; o `Update` completo está em `ctx.update`.
- Toda chamada de banco é assíncrona: sempre `await`.
- Sem chaves estrangeiras. Remoção só por `.deprecated('motivo')`. Mudança de tipo é manual.
- Publicar não altera o banco.
- O `push` espelha a pasta: o que for editado só no @BotFather é sobrescrito.
- O link `tg://user?id=` só funciona dentro de link embutido ou botão (documentação do Bot API).

## Comandos

```
npx tgcloud status   # o que mudou localmente contra a nuvem
npx tgcloud run <módulo> '<payload>'   # executa na plataforma sem publicar
```

Não use `npx tgcloud` fora do projeto: sem o CLI local, o npx baixa um pacote avulso de mesmo nome.
