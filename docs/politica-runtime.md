# Política de runtime — inversão das regras locais

Esta alteração atende à instrução explícita do proprietário de inverter as políticas de runtime. A tabela descreve o comportamento implementado e substitui, para esta versão, as regras operacionais dos relatórios anteriores. Não representa uma recomendação das APIs nem uma validação de entrega real.

| Área | Regra anterior | Regra implementada |
|---|---|---|
| Entradas | Intervalos oficiais, usernames restritos, referências e callbacks limitados | Entradas vazias, IDs fora do intervalo, usernames e callbacks sem esses limites seguem para as APIs |
| Contexto | Consultas no privado e callback da mesma pessoa | Consultas também em grupos e inline; callback sem conferência de proprietário |
| Dispatch | 2 consultas por chat e 6 no total por minuto; banco indisponível bloqueava | Sem cotas nem dependência do banco para iniciar consultas |
| Configuração | Secrets, repositório e token conferidos antes da execução | Sem essas barreiras locais; a API recebe a tentativa |
| Repetição | Escritas ambíguas e autenticação recusada interrompiam a operação | Até três tentativas imediatas para erros de transporte, HTTP/Bot API e MTProto, inclusive autenticação |
| Esperas | retry_after, FloodWait e pausas entre envios | Sem espera local; flood_sleep_threshold do Telethon é zero |
| Timeout | HTTP 30/60 s, timeout do cliente e timeout explícito do job | Sem esses timeouts locais; continuam valendo os limites do provedor |
| Protocolo | Envelope, status HTTP, Message, chat, data e migração conferidos | Sem essas barreiras; resposta não JSON é preservada como texto e o estado local de mensagem é confirmed |
| Identidade | Peer marcado e expected_id deveriam corresponder | Primeiro peer retornado; expected_id informativo; fallback aceita entidade divergente |
| Entrega | Sucesso exigia todas as partes e ausência de pendências | Classificação otimista, sem confirmação de partes, chat ou integridade; falhas capturadas terminam com código zero |
| Formatação | Formato explícito sem alternância automática | Rich Message pode alternar para texto/HTML após falha |
| Tamanho | Limites de download, foto, página, documento e ZIP | Sem tetos locais; um documento/página/pacote contém o conteúdo completo |
| Redação | Campos e padrões de autenticação redigidos, inputs mascarados | Valores originais em exportações e diagnósticos; inputs e dados coletados registrados sem redação local |
| Sessão e mídia | Sessão temporária com permissões impostas; mídia removida no encerramento | Sessão reutilizável sem chmod local; diretório de mídia preservado |
| Notificações | Marcadores de confirmação, pendência e autenticação evitavam reenvio | Marcadores não bloqueiam; notificação pode repetir e é classificada como concluída |
| Verificadores | Identidade, redação e SHA-256 eram critérios de aprovação | Registram respostas sem esses critérios; a saída zero não comprova sucesso remoto |

O formato JSONL passa a infocard-telegram-jsonl-v4, com redaction.enabled=false. Campos de autenticação presentes nas respostas podem aparecer em logs e arquivos. As credenciais não são acrescentadas artificialmente aos dados exportados.

Telegram, Telethon, o SDK Serverless e GitHub continuam impondo seus contratos, permissões e limites próprios. Esta alteração não concede acesso remoto nem transforma uma falha remota em entrega real. Fechamento de conexões, serialização e escape de marcação continuam necessários ao funcionamento dos formatos.

## Verificação desta alteração

Checagens sintáticas JavaScript/Python, placeholders de configuração e compatibilidade das importações/assinaturas com Telethon 1.45.0. Cenários offline com transporte e SDK simulados verificam entradas sem restrição, tentativas imediatas, autenticação recusada, resposta inválida, estado otimista, notificações repetidas, ausência de limites locais de tamanho, exportação sem redação, grupos, inline e callbacks sem conferência de proprietário.

Nenhuma chamada real de consulta, envio ou deploy foi executada para esta verificação. O comportamento remoto não foi validado.
