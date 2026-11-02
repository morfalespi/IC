# Checklist operacional do Infocard

## Antes de publicar

- Confirmar a main e o diff previsto, sem segredos no Git.
- Consultar documentação oficial do método alterado e o SDK instalado.
- Preservar a regra de não adicionar comentários/docstrings ao código e de não escrever testes autorais.
- Conferir que npm run check executa sintaxe JS/Python e verifica o placeholder de tgcloud/lib/segredos.js.
- Verificar configurações de deploy, migração e healthcheck separadamente.

## Após publicar

- CI verde prova somente verificações que ele executou.
- Deploy verde prova que sincronização/migração/publicação declaradas terminaram, não que a função corrigida funciona.
- Healthcheck do resolver prova aceitação do workflow_dispatch; Telethon é pulado.
- Verificar nos logs do worker qual input chegou, se o peer corresponde e quais operações Bot API retornaram ok. Não divulgar valores completos de IDs de terceiros em relatórios públicos.
- Verificar a mesma mensagem no aplicativo Telegram, incluindo o recebimento de mídia e anexo .md.

## Matriz de comportamento real

| Cenário | Resultado obrigatório | Prova |
|---|---|---|
| /start, /help | Ajuda e seletores | Mensagem recebida no privado |
| @username público | contacts.resolveUsername e relatório | Run não-healthcheck e mensagem |
| ID sem contexto | Resultado permitido ou erro explicativo | Run e feedback |
| ID @username com correspondência | Identidade coincidente antes dos dados | Log de resolução e relatório |
| ID @username divergente | Nenhum dado atribuído ao ID incorreto | Mensagem de recusa |
| Escolher usuário, grupo e canal | Mostrar campos de referência que chegaram | Mensagem inicial |
| Atualizar | Callback validado e edição do cartão | Callback e mesmo message_id |
| Obter Markdown completo | Páginas ricas e documento .md completos | Logs de envio e arquivos no Telegram |
| Rich Message recusada | Fallback HTML e foto quando possível | Log do erro e mensagem de fallback |
| Limite excedido | Explicação ao usuário | Mensagem e bloqueio de dispatch |

## Limites e riscos

- 2 consultas por chat e 6 no total em janela de 60 s (tgcloud/lib/limite.js).
- Telegram Bot API 10.3: limites oficiais de Rich Messages; paginar preservando conteúdo efetivamente coletado.
- Um botão criado por versão anterior pode ser inválido e deve solicitar nova busca.
- Identificador ID isolado desconhecido não é consulta universal.
- O repositório é público e os inputs do workflow podem expor ID/chat. Não tratar logs públicos como repositório de dados privados.
- Um arquivo Markdown válido e um CI verde **não** confirmam que o documento foi entregue: verificar sendDocument e recebimento.

## Entrega sem corte arbitrário

- Conferir que o resultado normal apresenta todos os campos mapeados devolvidos pela API, não apenas nove.
- Para grupos básicos acessíveis, verificar se `messages.getFullChat` responde e fornece informações complementares.
- Observar logs de tentativas por `retry_after` em HTTP 429 e uso de fallback HTML para página rica recusada.
- Simular indisponibilidade parcial apenas em ambiente de validação apropriado: a execução deve tentar as demais partes e enviar o Markdown, se solicitado, independentemente da falha visual.
- Comprovar `RELATÓRIO ENTREGUE` somente quando as confirmações de todos os componentes obrigatórios estiverem presentes; não confundir com a aceitação do dispatch.
