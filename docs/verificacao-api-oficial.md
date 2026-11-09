# Referência normativa e evidência operacional — IC

## Fonte

A referência deste projeto é a documentação **atual publicada pelo Telegram no momento de cada execução**, não uma versão anterior do código nem o próprio teste. O verificador baixa os índices oficiais e os arquivos Markdown individuais em `https://core.telegram.org/bots/api.md` e `https://core.telegram.org/bots/api/types.md`, registra URL e SHA-256 no log e lê os requisitos dos métodos observados. Uma mudança no texto pode exigir ajuste do interpretador; nunca deve ser convertida automaticamente em aprovação.

A Bot API 10.4, publicada em 9 de novembro de 2026, tornou `chat_id` opcional **somente para certos envios efêmeros**. A operação normal do IC exige um destino explícito. O IC rejeita `ephemeral_message_parameters` porque não implementa esse modo; isso não é uma proibição da API.

## O que a execução comprova

`.github/workflows/official-api-conformance.yml` exercita métodos do cliente contra um servidor local simulado e confronta as requisições observadas com as tabelas oficiais. O inventário também indica referências a outros métodos no código que não foram executadas. Tipos desconhecidos, regras condicionais sem verificação, lacunas de cobertura e respostas sintéticas não autorizam uma declaração global de conformidade.

Códigos de saída do comparador:
- `1`: encontrou divergência dentro do que tentou verificar;
- `2`: faltam evidências para declarar conformidade integral, ou a fonte não pôde ser interpretada;
- `0`: não deve ocorrer na verificação local enquanto não houver provas de operação integral, pois ela usa respostas simuladas.

A action **não testa** autenticação externa, controle de acesso remoto, MTProto real, entregabilidade final ou leitura de mensagens pelo destinatário. Nenhum comentário, resumo ou CI verde deve substituir essas evidências.

## Execução real independente

`.github/workflows/official-api-live.yml` é manual e exige confirmação explícita. Utiliza `BOT_TOKEN` e `IC_TEST_CHAT_ID` configurados como **secrets do GitHub Actions**. Envia somente conteúdo sintético para o chat de teste explicitamente indicado; consulta `getMe` e `getChat`, envia texto, foto e documento, solicita `getFile` e compara os bytes recuperados do documento. Os logs mostram nomes de métodos e resultados, não os IDs do chat nem credenciais.

Esse teste real não executou automaticamente por ter sido criado na branch do PR. A existência do arquivo e uma CI de sintaxe bem-sucedida não comprovam funcionamento real. Após a integração controlada e configuração do chat de teste, o operador pode iniciá-lo manualmente; ele não garante a entrega ao aplicativo nem a leitura pelo usuário.

## Interpretação

A API determina as regras oficiais. O código implementa operações dentro da visibilidade e permissões concedidas pelo Telegram. O teste somente identifica evidências observadas, divergências e lacunas. A documentação não executa o programa nem certifica automaticamente a aplicação.