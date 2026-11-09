# Conferencia de contrato independente, Bot API
A action official-api-conformance.yml baixa https://core.telegram.org/bots/api.md a cada execução, identifica campos obrigatórios e tipos nas tabelas oficiais e compara com as requisições HTTP realmente geradas pelo BotClient. O servidor de resposta é local e sintético, nunca o Telegram.

Escopo: getMe, getChat, sendMessage, sendPhoto, sendDocument, getFile. Confere método, nomes e tipos de parâmetros e campos obrigatórios retornados segundo as tabelas publicadas. Possui controle negativo para demonstrar que um argumento não documentado é rejeitado pelo comparador.

A documentação é a fonte dos critérios; o código Python executa a comparação. Se o documento não puder ser baixado ou interpretado, o job encerra como INCONCLUSIVO, não aprovado.

A action não verifica semântica completa de parâmetros condicionais, acesso real a contas, MTProto, entrega ao usuário ou as demais operações. Um resultado positivo somente significa conformidade parcial com as regras explicitamente extraídas. Logs não contêm credenciais nem dados de alvos reais.
