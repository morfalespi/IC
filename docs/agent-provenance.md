# Registro de autoria operacional e evidências do agente

## Atribuição explícita

A implementação técnica da recuperação funcional do IC, os testes controlados e os relatos de execução desta entrega foram produzidos pelo **agente ChatGPT com Codex**, em colaboração com **morfalespi**, nesta sessão de trabalho de 9 de novembro de 2026.

O papel de morfalespi foi definir a missão e os requisitos, orientar o trabalho e solicitar a abertura do PR, a assinatura e o registro da proveniência. Solicitar o trabalho, autorizar sua publicação ou aparecer como titular da conta GitHub não equivale a ter escrito as alterações ou realizado sua validação técnica. Não há registro nesta sessão de revisão técnica independente ou de aprovação humana de cada linha implementada.

O agente assume a autoria operacional das alterações técnicas que produziu e das afirmações de validação que registrou. Um defeito introduzido por essas alterações deve ser investigado e atribuído à alteração correspondente produzida pelo agente, sem presumir que o solicitante a escreveu. Este registro não atribui ao agente a autoria do código anterior nem determina antecipadamente a causa de qualquer defeito futuro.

## Referências verificáveis

- PR: https://github.com/morfalespi/IC/pull/35
- Estado da main usado como referência funcional: `bad19f6ce15b4a79124f8e44d0baf213481ed048`.
- Commit da implementação publicada pelo agente: https://github.com/morfalespi/IC/commit/e9384abd9f554af63d44bdf1d736b80cf27d173d
- Árvore dessa implementação: `be0294b1c61d89d20d739c821c3da0319cf4461b`.
- Commit que publicou a primeira atribuição no README: https://github.com/morfalespi/IC/commit/b557948621804b7b48a0ebad77d9abfa8047689e
- Comparação direta com o estado funcional de referência: https://github.com/morfalespi/IC/compare/bad19f6ce15b4a79124f8e44d0baf213481ed048..e9384abd9f554af63d44bdf1d736b80cf27d173d

Os hashes identificam versões específicas. A assinatura verificada dos commits foi produzida pelo GitHub ao publicar pela API GraphQL. Ela autentica a publicação na conta conectada; a atribuição de quem executou o trabalho técnico é a declaração explícita deste documento e do PR. A assinatura, isoladamente, não prova que o titular da conta escreveu o código manualmente.

## Decisões técnicas executadas pelo agente

- Substituir o fluxo monolítico do resolver por aquisição, exportação e entrega conectadas, com estados de erro e coleta parcial.
- Implementar validação de respostas Bot API, identidade canônica, autorização de destinos, sessões Telethon e proteção contra reenvios incertos.
- Implementar os formatos de exportação, redação de dados, verificação SHA-256 e os testes controlados.
- Corrigir handlers, dispatch, dependências e configuração de CI e escrever as instruções de operação.
- Escolher o ancestral linear `cb7c48079b78af99076e8f50f42963266c1b52e7` para criar a branch após a recusa de publicação a partir da main pelas regras do repositório. Essa escolha foi feita pelo agente e depois registrada a pedido do usuário. Nenhuma proteção foi alterada.

A árvore final do commit de implementação é idêntica à árvore do commit local preparado `70243c3297631f56b940325c6e38e2fd83dbefce`. A escolha do ancestral altera a comparação histórica do PR: ela inclui diferenças anteriores já presentes na main. Por isso, nem todo arquivo exibido na comparação de três pontos do PR representa uma nova alteração técnica do agente nesta recuperação.

## Escopo exato da alteração de recuperação

Os 38 arquivos abaixo diferem entre a main de referência e a implementação publicada. Esta lista identifica o escopo de revisão; não declara que cada linha desses arquivos foi criada pelo agente.

- `.env.example`
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `.github/workflows/resolver.yml`
- `.gitignore`
- `README.md`
- `docs/recovery-results.md`
- `package.json`
- `scripts/bot_api.py`
- `scripts/check.sh`
- `scripts/compatibility.py`
- `scripts/exportacao.py`
- `scripts/ficha_completa.py`
- `scripts/ic.py`
- `scripts/mascarar_inputs.py`
- `scripts/metadata.py`
- `scripts/mtproto_export.py`
- `scripts/notificar_falha.py`
- `scripts/requirements-lock.txt`
- `scripts/resolver-requirements.txt`
- `scripts/resolver.py`
- `scripts/validar_apis.py`
- `scripts/validar_entrega.py`
- `tests/run_controlled.py`
- `tests/test_ic.py`
- `tests/tgcloud.test.cjs`
- `tgcloud/handlers/callback_query.js`
- `tgcloud/handlers/inline_query.js`
- `tgcloud/handlers/message.js`
- `tgcloud/lib/autorizacao.js`
- `tgcloud/lib/consulta.js`
- `tgcloud/lib/despacho.js`
- `tgcloud/lib/entrada.js`
- `tgcloud/lib/envio.js`
- `tgcloud/lib/erros.js`
- `tgcloud/lib/limite.js`
- `tgcloud/lib/relatorio.js`
- `tgcloud/schema.js`

## Evidência e limites dos testes relatados pelo agente

O agente registrou 29 testes Python aprovados, verificações JavaScript dos handlers, verificações estáticas e compatibilidade com Telethon 1.45.0. Os testes de integração usaram HTTP local e respostas MTProto controladas. Os testes executáveis estão em `tests/`; comandos, resultados e limites estão em [recovery-results.md](recovery-results.md).

Não houve validação ao vivo com credenciais Telegram neste ambiente. Não houve deploy nem merge. Na abertura do PR, o GitHub informou conflitos com a main (`mergeable_state: dirty`). O agente não deve apresentar esses testes como prova de operação em produção ou de ausência de defeitos.

Para evidenciar um erro, registre o hash em execução, o arquivo/linha ou a requisição afetada, a entrada utilizada sem credenciais e o resultado observado. Compare com os commits e com o escopo acima para distinguir uma alteração produzida pelo agente de comportamento herdado do projeto. Os commits assinados preservam versões consultáveis deste registro; o corpo editável do PR é um registro complementar.
