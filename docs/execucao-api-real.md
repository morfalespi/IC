# Execução externa controlada da Bot API

A auditoria estática e os fixtures locais não constituem comprovação de execução externa. Para produzir essa evidência, `.github/workflows/official-api-live.yml` disponibiliza execução **manual e voluntária** de `tests/official_api_live.py`.

Pré-condições verificadas em tempo de execução:

1. Confirmação manual `autorizo_envios_sinteticos=true`.
2. Secret `BOT_TOKEN` configurado para o bot de teste próprio.
3. Secret `IC_TEST_CHAT_ID` configurado para um chat numérico em que o bot tenha permissão de envio.
4. Rede e autenticação reais aceitas pelo Telegram.

Somente após as pré-condições, o teste envia texto, PNG e documento sintéticos ao destino configurado, consulta `getMe`, `getChat` e `getFile`, compara os parâmetros com a documentação atual e baixa o documento por `getFile` para confrontar SHA-256 e bytes. O script não pode certificar que uma pessoa leu a mensagem, nem provar operações MTProto ou coleta de dados de terceiros.

Um resultado positivo **desta execução manual** (não da auditoria local) representa a comprovação limitada às chamadas reais exercitadas, ao destino de teste e à sessão configurada. Quaisquer operações que não participarem do teste continuam não verificadas. Não é necessário publicar ou divulgar tokens em código, chat ou logs.

**Estado atual:** workflow adicionado à branch de recuperação em um Pull Request em rascunho. Isso por si só não executa a prova externa, nem confirma disponibilidade de secrets.
