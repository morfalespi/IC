# Segurança

## Segredos

Nunca versione tokens ou credenciais. O arquivo `tgcloud/lib/segredos.js` deve permanecer no Git apenas com placeholders vazios; o workflow de deploy injeta `GH_DISPATCH_TOKEN` e o nome do repositório somente no runner antes da publicação.

Secrets esperados no GitHub Actions:

- `TGCLOUD_TOKEN`
- `GH_DISPATCH_TOKEN`
- `API_ID`
- `API_HASH`
- `BOT_TOKEN`

O `GH_DISPATCH_TOKEN` deve ser um token fine-grained restrito a este repositório e com apenas a permissão necessária para disparar Actions. Rotacione imediatamente qualquer segredo que apareça em commit, log, issue, print ou mensagem pública.

## Dados retornados

O bot deve exibir apenas campos efetivamente entregues pelas APIs utilizadas. Não trate ausência de campo como prova de inexistência e não prometa acesso a dados protegidos por configurações de privacidade.

## Relato de vulnerabilidade

Enquanto o repositório for privado, use um canal privado do proprietário do projeto para relatar vulnerabilidades. Não publique tokens, IDs privados ou dados pessoais em issues.