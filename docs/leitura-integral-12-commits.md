# Registro mensurável da leitura total do repositório nos 12 commits

> **Retificação factual posterior:** consulte [proveniência dos commits e limites da evidência](retificacao-proveniencia-dos-commits.md) para os dados efetivamente registrados sobre a publicação pela integração GitHub, a identidade nativa do Git e a ausência de identificação do ambiente Linux executor.


**Repositório:** morfalespi/IC. **Head auditado:** 6a4eb788069055c48f0829580c32d64367ca0455. **Data da auditoria:** 2026-11-06. Este arquivo documenta exatamente o corpus lido e o limite das conclusões.

## 1. Cobertura de conteúdo realmente recuperado

| Medida | Resultado |
|---|---:|
| Commits mais recentes solicitados | **12 / 12** |
| Estados extras necessários à comparação | **2** (base B00 e primeiro pai P10) |
| Árvores Git completas examinadas | **14 / 14**, nenhuma marcada como truncada |
| Referências a arquivos presentes nas 14 árvores, com repetições entre commits | **585** |
| Versões distintas de blobs, sem contar o mesmo SHA mais de uma vez | **129 / 129** |
| Conteúdo integral recuperado dessas versões distintas via GitHub blob | **129 / 129** |
| Comparações de tamanho UTF-8 com o campo size da árvore Git | **129 / 129 correspondentes** |
| Bytes únicos recuperados e conferidos em todos os tipos de arquivo | **1.838.421 bytes** |
| Versões de código/configuração (py, js, sh, yaml/yml, json/jsonc, txt) | **103** |
| Bytes únicos em código/configuração | **1.422.687 bytes** |
| Caminhos de arquivo distintos em todos os estados | **48** |
| Execução própria de todos os ramos do código e de todos os métodos Telegram | **não realizada** |
| Comprovação de recebimento externo e hash de cada anexo | **não realizada** |

**Método material:** cada árvore foi obtida pela API Git Trees com recursive=1; cada blob identificado foi recuperado integralmente pela API Git Blobs, sem limite de trechos; o conteúdo foi percorrido e seu tamanho calculado em bytes UTF-8, confrontado com o tamanho que o GitHub informa para o SHA correspondente. Identidades repetidas entre árvores foram contadas uma vez. Foram também examinados diffs de commits e logs de workflows para interpretar comportamento. A lista abaixo permite verificar a identidade integral de cada versão.

**Limitação do termo “100%”:** há 100% de **recuperação de conteúdo dos blobs identificados e verificação de tamanho** no conjunto especificado, não alegação de prova formal de correção, de cobertura de ramos ou de compreensão infalível de todos os efeitos de cada linha. As conclusões operacionais provêm da interpretação de funções, diferenças entre versões e da evidência dos jobs, separadas de experimentos não executados. A conferência de tamanho não é um recálculo independente do SHA-1 de cada blob; o SHA é o identificador Git retornado pelo provedor.

## 2. Estados de código considerados

A ordem C01–C12 é **cronológica da sequência**, não a ordem de listagem inversa da API. B00 é o pai anterior de C01 no branch, e P10 é o **primeiro pai do commit de merge C10**. Sem P10, excluir README.md, AGENTS.md e SECURITY.md na integração à main passaria despercebido ao comparar apenas o branch do PR #32.

| Índice | SHA/árvore no GitHub | Arquivos | Arquivos de código/configuração | Bytes da árvore | Papel |
|---|---|---:|---:|---:|---|
| **B00** | [b7e59b14148f](https://github.com/morfalespi/IC/tree/b7e59b14148f3cd57352f44b7b2661155054fffc) | 37 | 25 | 460.187 | base anterior à sequência |
| **C01** | [aeef5957d13d](https://github.com/morfalespi/IC/tree/aeef5957d13d5c2893d23d066401750e21a59568) | 41 | 29 | 464.171 | substitui políticas |
| **C02** | [e37cf3d076af](https://github.com/morfalespi/IC/tree/e37cf3d076afd44bc07ed9ce8d01245abaae11e8) | 41 | 29 | 465.182 | diagnóstico dispatch |
| **C03** | [c7b1644a706b](https://github.com/morfalespi/IC/tree/c7b1644a706bdd359a7617a6475499255e0f4f5d) | 41 | 29 | 470.462 | falhas explícitas |
| **C04** | [8db7c084526a](https://github.com/morfalespi/IC/tree/8db7c084526a061246583e08b279269b48ea6634) | 41 | 29 | 470.458 | peers presumidos |
| **C05** | [9d3408c6e85a](https://github.com/morfalespi/IC/tree/9d3408c6e85a7dc88bcdaf170f947d85c259c5e5) | 41 | 29 | 470.779 | JSON no dispatch |
| **C06** | [4c1da31da3f4](https://github.com/morfalespi/IC/tree/4c1da31da3f499be517a9cb2df1c078aba56526d) | 41 | 29 | 477.344 | autenticação |
| **C07** | [c7d454523d3c](https://github.com/morfalespi/IC/tree/c7d454523d3c67efd8741db8ad449822c8423f8e) | 43 | 31 | 486.867 | redação e estados |
| **C08** | [03baeed97deb](https://github.com/morfalespi/IC/tree/03baeed97deb2adfd52dc0c3a37a1c8d6fef0af4) | 44 | 32 | 493.419 | integridade |
| **C09** | [cb7c48079b78](https://github.com/morfalespi/IC/tree/cb7c48079b78af99076e8f50f42963266c1b52e7) | 44 | 32 | 494.378 | pendências |
| **C10** | [c9195d125471](https://github.com/morfalespi/IC/tree/c9195d12547112745b8e091644b3586fccff9a2e) | 44 | 32 | 494.378 | merge #32 |
| **C11** | [7d718b312249](https://github.com/morfalespi/IC/tree/7d718b312249ea76bac4edc5ec07d8c3cdddf7e3) | 45 | 32 | 459.972 | reversão runtime |
| **C12** | [6a4eb7880690](https://github.com/morfalespi/IC/tree/6a4eb788069055c48f0829580c32d64367ca0455) | 45 | 32 | 459.972 | merge #34 |
| **P10** | [1d3433a5c2cc](https://github.com/morfalespi/IC/tree/1d3433a5c2cc7eb73fd6d9294b08eced23cb2fab) | 37 | 23 | 471.554 | primeiro pai do merge #32 |

**Nota sobre merges:** C10 tem pais **1d3433a5** e **cb7c4807**. C12 tem pais **c9195d12** e **7d718b31**. **C11 e C12 possuem a mesma árvore de arquivos**; a inclusão de ambos é obrigatória para examinar os 12 commits, mas os bytes em comum foram deduplicados no total.

## 3. Manifesto exaustivo das versões

Cada linha designa um conteúdo **distinto** por SHA Git; a última coluna indica todos os snapshots em que aquela exata versão aparece. Um arquivo que mudou várias vezes tem várias linhas. Documentos, configurações, workflows e arquivos de suporte são incluídos para não esconder partes da árvore. Um arquivo removido aparecerá apenas nas versões anteriores. A identidade do conteúdo pode ser conferida pela URL: https://api.github.com/repos/morfalespi/IC/git/blobs/ seguida pelo SHA informado.

| Nº | Caminho | Bytes | SHA Git completo | Snapshots que contêm este conteúdo |
|---:|---|---:|---|---|
| 001 | .env.example | 168 | 14696397461aa680e570d1865c0851e25d951227 | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12 |
| 002 | .env.example | 146 | 756059ee852867679006ae4d3f2832c1aa738a78 | B00, P10 |
| 003 | .github/workflows/ci.yml | 432 | bbcfadf652c167494ad83f430c2522f4bf5aa6a4 | P10 |
| 004 | .github/workflows/ci.yml | 724 | cf747624b2fbd973e5a1c5944a438439ca3122a1 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12 |
| 005 | .github/workflows/deploy.yml | 3.788 | c85d96d1f7585f5f057364242a07134cdb42c45d | B00, C01, C02, C03, C04, C05, C06 |
| 006 | .github/workflows/deploy.yml | 3.849 | e909dec4c5878aabe6a6eaf6bcdd49c59c86a9d5 | P10 |
| 007 | .github/workflows/deploy.yml | 4.518 | f84f39446363fd5ac22fd7933a78144b40c53cfc | C07, C08, C09, C10, C11, C12 |
| 008 | .github/workflows/resolver.yml | 3.937 | 05c46c73a533bfd3e156b214d1f599ea015e5617 | C03, C04, C05, C06 |
| 009 | .github/workflows/resolver.yml | 4.164 | 105622959ddafc9c3f02deae2429e0836fedacd2 | C11, C12 |
| 010 | .github/workflows/resolver.yml | 4.608 | 5c02fb62ac1ccd452b5e645d2f6096bf90057148 | C08, C09, C10 |
| 011 | .github/workflows/resolver.yml | 3.518 | 71c411d71882d950d3dbe92e9422cdc8ca3ab009 | P10 |
| 012 | .github/workflows/resolver.yml | 3.689 | aa964797a9797eef6c439fe132ba2726c1c68519 | C01, C02 |
| 013 | .github/workflows/resolver.yml | 4.154 | c4edb1dd646923dc55acf376bbe3286225ff76e2 | B00 |
| 014 | .github/workflows/resolver.yml | 4.234 | e7f39a2cced9ff0aaf2794104ab557fe2f78d6a6 | C07 |
| 015 | .gitignore | 374 | 3f47f96e0a59d01709e5c8764061096a81f36e2d | B00, P10 |
| 016 | .gitignore | 386 | fe55abb0b1e4ab57c5427af8d36e1bba0accba2e | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12 |
| 017 | AGENTS.md | 9.472 | 26f1f3bf267bee0494aff0b8a882245988293bdc | P10 |
| 018 | docs/auditoria-operacional.md | 20.076 | 4dba74661f56739c874479f793134dd3ee5c11ca | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 019 | docs/fontes-oficiais.md | 11.750 | 9f79b0f080fe40aefdea41db67294641bae46a95 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 020 | docs/inventario-peer-2026-11-03.md | 25.295 | 379b0239eb0c13c0bcfa89d09a520d05cd9f4547 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 021 | docs/launch-checklist.md | 3.659 | 46d91cda62bc8c8dd9c83ea9437fc54e0392ca0f | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 022 | docs/partners-mtproto-coverage.md | 28.194 | 21cfd8b06c1443742059defcd7f27d892815c55a | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 023 | docs/politica-runtime.md | 4.258 | 4123ea07dcc3f55a4f081a96d042d136f046e4ad | C11, C12 |
| 024 | docs/registro.md | 81.608 | 549f939716057cf4c1ec4f111656bc86868c28cc | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 025 | docs/revisao-integracoes-2026-11-04.md | 8.207 | 098cb2f06b8740559323a0cf28e02edb8a4b3197 | C01 |
| 026 | docs/revisao-integracoes-2026-11-04.md | 9.930 | 1d228b26a5639dd1bae34fb231118e5c1073b11a | B00 |
| 027 | docs/revisao-integracoes-2026-11-04.md | 18.322 | 36d9306316dff763c949e29596f413598cb2e0f3 | C07 |
| 028 | docs/revisao-integracoes-2026-11-04.md | 8.889 | 5c2817f920d93259adc2a4968ef61ed9baebc651 | C02 |
| 029 | docs/revisao-integracoes-2026-11-04.md | 19.461 | 7affd47e901c6c57c4f5d80d2235e02a1205aa8a | C08 |
| 030 | docs/revisao-integracoes-2026-11-04.md | 20.420 | 95270a555c74ba1611a52fef0e6c7daeb9980788 | C09, C10, C11, C12 |
| 031 | docs/revisao-integracoes-2026-11-04.md | 11.941 | bf1f65b15a6ae1a3fd503a9f338cd289353ecb34 | C03 |
| 032 | docs/revisao-integracoes-2026-11-04.md | 14.692 | cc71c2a97118f5befccf6f14b38deb77d2cb48e0 | C06 |
| 033 | docs/revisao-integracoes-2026-11-04.md | 12.525 | d60df99627c065c3d634823728d75d8c500c0bed | C04, C05 |
| 034 | docs/Serverless-OFFICIAL | 66.605 | 970c6c4e7279eb15a94f3621e108fb28ca166e50 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 035 | docs/tgcloud-sdk.md | 19.868 | f2ba99f6161abb2aa48b2158cb5effdd4af8926f | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 036 | LICENSE | 1.067 | 057feee61578ebb0c6ab196c7d2927cfb4c4f167 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 037 | package-lock.json | 10.827 | 1ba93d35735feb135210ec06b2e3d6ed32c79d4f | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 038 | package.json | 251 | 759794fe892701e280c8c7342fbfe35c0e627ccf | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 039 | README.md | 16.543 | ff18cc1ee633f18f816a284081a32afd77ca02c3 | P10 |
| 040 | scripts/bot_api.py | 2.206 | 0486998ecd46e2f8c8a21b21deca522297593742 | C11, C12 |
| 041 | scripts/bot_api.py | 5.896 | 3b5bcf38748c7b62bfadc6191794d66b24dd0662 | C06 |
| 042 | scripts/bot_api.py | 8.221 | 3cd4f56142c2fcc3196a7968a5e9f7ced03d52b3 | C09, C10 |
| 043 | scripts/bot_api.py | 3.719 | 949f520e626ec5bae21bc3247ba37140f0f932e6 | C01, C02 |
| 044 | scripts/bot_api.py | 4.511 | d3b711a033414fbef0c3fd39d5702b7bea8973dc | C03, C04, C05 |
| 045 | scripts/bot_api.py | 8.221 | f08b5d349aaa0139e6a68e3045352df0d40f4f35 | C07, C08 |
| 046 | scripts/check.sh | 523 | 4955de2029c27995a2866e837872432a12e9d590 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12 |
| 047 | scripts/check.sh | 558 | b89f6e79aa8332a17fc303922a73037bd07887d8 | P10 |
| 048 | scripts/compatibility.py | 1.439 | 00e488a9ebde1bdede61728312d73c535c1ecfe3 | C01, C02, C03, C04, C05, C06 |
| 049 | scripts/compatibility.py | 1.317 | 5b5e84e3c2f601f483385e64736e9bdf0f83df53 | B00 |
| 050 | scripts/compatibility.py | 1.472 | a8bf2984388724d98af61f3fd8252f8da8d1af98 | C07 |
| 051 | scripts/compatibility.py | 1.491 | db81411925e3c6d435a41a72ad1c730dc24a03bc | C08, C09, C10, C11, C12 |
| 052 | scripts/exportacao.py | 1.649 | 1aae9ee5b6fb48999b69f855fb2058ac450eb2ef | C07, C08, C09, C10 |
| 053 | scripts/exportacao.py | 796 | 9bce69ccb43c549d4d90f5b96731e48ce4dfaab9 | C11, C12 |
| 054 | scripts/ficha_completa.py | 10.174 | 09fc2bff615a892e41a88348aafd9b8f20685d87 | C08, C09, C10 |
| 055 | scripts/ficha_completa.py | 3.054 | d6cd9b542fb65316973a4cd4779373f1c81b4f39 | C11, C12 |
| 056 | scripts/ficha_completa.py | 10.113 | ea1adeba553e2bcc3e29319452c401eec1d44ae4 | B00, C01, C02, C03, C04, C05, C06, C07, P10 |
| 057 | scripts/mascarar_inputs.py | 635 | d8630253c9db38265085c685b6f5b7a26f58693d | C07 |
| 058 | scripts/mascarar_inputs.py | 299 | f9aed1e6226a2848eb9727702624a71c1e36cddc | C11, C12 |
| 059 | scripts/mascarar_inputs.py | 854 | fe76919795d6d366647b1d0ff50965722931b27a | C08, C09, C10 |
| 060 | scripts/mtproto_export.py | 1.949 | 64afac4befe6a6abde31bc7e194bb4978d96a5ea | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, P10 |
| 061 | scripts/mtproto_export.py | 731 | daf387612f403ba270727d02c27ed970be14fdca | C11, C12 |
| 062 | scripts/notificar_falha.py | 1.972 | 5f92ec94e43df0c61f0424aaa5e464d467c10b36 | C07, C08, C09, C10 |
| 063 | scripts/notificar_falha.py | 1.918 | 82e81b8e4e2d823a803093a95f1c658a7d631299 | C06 |
| 064 | scripts/notificar_falha.py | 567 | 9a110d92cad457eaf31951e2e148efa7e21719e6 | C11, C12 |
| 065 | scripts/notificar_falha.py | 1.307 | fd52623bb3f6855d2fdf6efc0002e910d9df31c7 | C01, C02, C03, C04, C05 |
| 066 | scripts/resolver-requirements.txt | 17 | e52665cc0900b0ed32b02374f0a33f77ab4e9dcf | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 067 | scripts/resolver.py | 132.769 | 15ef66594ea78811e3af8a720083096264a03657 | C04, C05 |
| 068 | scripts/resolver.py | 133.309 | 20abb3ff41d9025211a0a8da63b977461494f33f | B00 |
| 069 | scripts/resolver.py | 131.834 | 4ac839bf521c62c7d6c0c5a38b3a370c59281ebb | C01, C02 |
| 070 | scripts/resolver.py | 124.697 | 56deedb748dd902a613e8760fea2aea89cd13df4 | C11, C12 |
| 071 | scripts/resolver.py | 135.171 | 8b2ed9b36f50fd32105ddd5aff4f6d06a7304871 | C06 |
| 072 | scripts/resolver.py | 130.989 | 9744008fc510e522334a410de44fc5fc5ddc4f3e | P10 |
| 073 | scripts/resolver.py | 134.700 | a6837898151343b59bb6eeeb1a6ef91ef0c40f9d | C08, C09, C10 |
| 074 | scripts/resolver.py | 133.572 | ba758c5134c8d860944c9e6e21038d11d2f4195e | C03 |
| 075 | scripts/resolver.py | 134.652 | dee00ae7bba2aa07600f6741a8b146eefc43d301 | C07 |
| 076 | scripts/telegram_ids.py | 241 | d226c9a676cc0d35bda565208c8d88f07c3a6eee | C11, C12 |
| 077 | scripts/telegram_ids.py | 512 | d8f07d62ff103025e1d910e7389f47bfa20beebf | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10 |
| 078 | scripts/validar_apis.py | 871 | 12b059d6ef6947e68fb1f45b2c074c9e9a406fca | C11, C12 |
| 079 | scripts/validar_apis.py | 2.688 | 385a3f4fc57db8ae831830cd2b7036717fa3540c | C07, C08, C09, C10 |
| 080 | scripts/validar_apis.py | 1.964 | 5510d462bb6156a623ceee9b30a114131e336027 | B00 |
| 081 | scripts/validar_apis.py | 1.777 | 9d08c6162b0139044d1137a78de877f3141949d6 | C01, C02 |
| 082 | scripts/validar_apis.py | 1.999 | e9738e462d944a829caf52b9acd1626ef5b6d336 | C03, C04, C05, C06 |
| 083 | scripts/validar_entrega.py | 4.692 | 332799727f17a0c4620557bdfbf5ceafdf507632 | C08, C09, C10 |
| 084 | scripts/validar_entrega.py | 2.673 | 8410308826a21f21e991c140d27f8e00ee6491c8 | C11, C12 |
| 085 | SECURITY.md | 1.878 | 28cb1a7bcf4cf4f60d039fd4506a55c05ebd02fc | P10 |
| 086 | tgcloud.jsonc | 67 | bc8e19156e18cb54e41a5845c992f9478d4fb0e1 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 087 | tgcloud/handlers/callback_query.js | 1.154 | 0157178e5d8bbf0ce97ccf03b9b81fa7de9ecd67 | C11, C12 |
| 088 | tgcloud/handlers/callback_query.js | 1.445 | 5317acd91496224701a5e3c0139eaab662547d42 | P10 |
| 089 | tgcloud/handlers/callback_query.js | 1.513 | a065b2261a022bc1f406e9cdd601950a6fd253f1 | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10 |
| 090 | tgcloud/handlers/callback_query.js | 1.462 | b73b4e29d686835c06cae39e900f7d2b9bbbe049 | B00 |
| 091 | tgcloud/handlers/inline_query.js | 696 | 3c63e3f36f64f8d1f03087454a0649661d24f8c6 | P10 |
| 092 | tgcloud/handlers/inline_query.js | 764 | 434d2b1df1f5d75021763463d9e7d8fea857232c | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10 |
| 093 | tgcloud/handlers/inline_query.js | 713 | b90e9194104ee23f4ed085f3f4528da1cc94d415 | B00 |
| 094 | tgcloud/handlers/inline_query.js | 646 | d283e68e46558b7b042741472a00175ed9036b97 | C11, C12 |
| 095 | tgcloud/handlers/message.js | 4.036 | 6f6cb36bb150f3a7266a3e3cb0e415ecbdeba000 | C11, C12 |
| 096 | tgcloud/handlers/message.js | 4.212 | 862b5ad8646c60b8ea44495063c92c17223df88e | B00 |
| 097 | tgcloud/handlers/message.js | 4.263 | c433578fad36c8f6d67e53ffea8d7486b4039ed8 | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10 |
| 098 | tgcloud/handlers/message.js | 4.195 | d074bbcf2f4e4c1eb61f4f8ba61dadeed675a341 | P10 |
| 099 | tgcloud/lib/cartao.js | 1.950 | 5684e3f7cd884f294f1272ab31bf65e1b49058a7 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 100 | tgcloud/lib/consulta.js | 2.469 | 262fba3a38d0d213010b44f849adcc6448d958f7 | C03, C04, C05, C06, C07, C08, C09, C10 |
| 101 | tgcloud/lib/consulta.js | 2.690 | 3470e791e7cecb6abffb49ecf471e465a7a22853 | P10 |
| 102 | tgcloud/lib/consulta.js | 2.823 | 6e9ea24fe82aec2aea9799a04083ab3937a1b492 | C01, C02 |
| 103 | tgcloud/lib/consulta.js | 2.895 | 7bd40a47211928f917e29d483f95c8cdc4b92594 | B00 |
| 104 | tgcloud/lib/consulta.js | 1.198 | 812112c84f8c5bad770487d034c7e33f894c41bf | C11, C12 |
| 105 | tgcloud/lib/despacho.js | 1.978 | 440aacd78c44359fc46b97614bcabce94b21124e | P10 |
| 106 | tgcloud/lib/despacho.js | 2.628 | 906582fc84158a6a035a8d79a01f687728dea12b | C05, C06, C07, C08, C09, C10 |
| 107 | tgcloud/lib/despacho.js | 2.107 | a37db1171dff94f57c6ce1c8cfb918d1d4210bcd | C01 |
| 108 | tgcloud/lib/despacho.js | 1.906 | ae26fef47acf4af78412ef73690e6ad338cde27c | B00 |
| 109 | tgcloud/lib/despacho.js | 2.307 | bdf685078e444efa4144932a72c67db8cbabe8fb | C02, C03, C04 |
| 110 | tgcloud/lib/despacho.js | 1.244 | f8bb7b05b437e3b91f8ddf6b2ea1f65af745a68b | C11, C12 |
| 111 | tgcloud/lib/entrada.js | 2.835 | 139476dfddf765b3078b8be716c5cf2bc4d405d6 | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10 |
| 112 | tgcloud/lib/entrada.js | 2.702 | 4fd716a4710c4fe35b332d1bb4eda7483c89abfc | B00, P10 |
| 113 | tgcloud/lib/entrada.js | 1.198 | e8eff009a541aea4c596d3d8b0a8ef99a03fc3f0 | C11, C12 |
| 114 | tgcloud/lib/envio.js | 2.050 | 331afe10a02991bce94f59c1ef6cce97b541b122 | P10 |
| 115 | tgcloud/lib/envio.js | 1.993 | 71909562fbb4627eaad501b3786bf19063c725cd | C11, C12 |
| 116 | tgcloud/lib/envio.js | 2.330 | 719a212a9bf0ad9d587f3360b9d1b980452ece70 | C01, C02 |
| 117 | tgcloud/lib/envio.js | 2.084 | 8c6f04b1940e0c7614c5fc5d725fed894824d7af | B00 |
| 118 | tgcloud/lib/envio.js | 1.912 | d6dc43d01980870d23c9fc97430b292645e3f2d5 | C03, C04, C05, C06, C07, C08, C09, C10 |
| 119 | tgcloud/lib/erros.js | 1.261 | 13d7084b078ee5181e504d931a2d775c77f9e3ff | C11, C12 |
| 120 | tgcloud/lib/erros.js | 1.479 | 1443c18cecaabb5541abf71b2a9577273caf050b | C01 |
| 121 | tgcloud/lib/erros.js | 1.608 | 94a9a721b6b920ce8a2a2efc43ed80a94bdc3e64 | C02, C03 |
| 122 | tgcloud/lib/erros.js | 1.823 | bf79538ad51776d3fb3838b04130ce878517fc4d | C04, C05, C06, C07, C08, C09, C10 |
| 123 | tgcloud/lib/limite.js | 1.437 | 5d11635a30583c9cad4fa4af2fdbb70c11c0ca56 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, P10 |
| 124 | tgcloud/lib/limite.js | 127 | edc3243f6bc63509b9ce31628354262473314ff4 | C11, C12 |
| 125 | tgcloud/lib/relatorio.js | 2.963 | 1c631a334c50008c4327b1342423bbfd8816f259 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10 |
| 126 | tgcloud/lib/relatorio.js | 2.806 | 3f42055dc60898b7934b556d7f23a3e26196a987 | C11, C12 |
| 127 | tgcloud/lib/relatorio.js | 3.018 | 5a947498e8021da5954ed3c8936d06e54c83195a | P10 |
| 128 | tgcloud/lib/segredos.js | 70 | 65da1573b08474c00133605aed2ecf6f533ec468 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |
| 129 | tgcloud/schema.js | 218 | d7ba18c4a4e2df5199bbb94f6b38352f5f79dad0 | B00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, P10 |

## 4. O que os logs realmente provaram

Além da leitura do corpus, foram consultados o status de workflows, etapas de jobs e trechos operacionais de logs do GitHub Actions, sem republicar dados coletados de terceiros.

- **C12:** [CI](https://github.com/morfalespi/IC/actions/runs/42238080549) e [Deploy](https://github.com/morfalespi/IC/actions/runs/42238080624) concluíram com sucesso, mas seu escopo é instalação, checagens e publicação, não prova de entrega.
- **C12:** [healthcheck](https://github.com/morfalespi/IC/actions/runs/42238133744) concluiu verde **sem executar o resolver**.
- **C12:** [job real do resolver](https://github.com/morfalespi/IC/actions/runs/42238240333) executou a rotina, relatou erros de stickers e de download, gerou aviso de nomes duplicados no ZIP e marcou relatório como concluído. A implementação atual pode devolver status zero e confirmar aceitação sem validar Message ou bytes.
- **C08:** [validação de APIs](https://github.com/morfalespi/IC/actions/runs/42023095036) terminou verde sob condições de validação mais restritas do código daquela revisão.
- **C10:** [primeira](https://github.com/morfalespi/IC/actions/runs/42106712608), [segunda](https://github.com/morfalespi/IC/actions/runs/42106692706) e [terceira](https://github.com/morfalespi/IC/actions/runs/42106526642) execuções reais analisadas terminaram com erro no resolver.

**Escopo externo não coberto:** não houve leitura da caixa de entrada do chat final, recálculo de hash de anexos realmente recebidos, monitoramento do servidor Telegram ou prova de que todas as chamadas remotas ocorreram com sucesso. Estes fatos permanecem **não confirmados**, não “aprovados”.

## 5. Auditabilidade e reexecução da comparação

1. Consulte os commits C01–C12 e os pais B00/P10 da tabela.
2. Para cada árvore, solicite Git Trees recursive=1 e anote os campos path, type=blob, size e sha.
3. Deduplicate os blobs pelo campo sha.
4. Obtenha cada Git Blob completo e compare seu tamanho UTF-8 ao size catalogado; caso algum falhe, reduza a porcentagem reportada.
5. Faça os diffs por primeiro pai nos dois merges e confronte a árvore final à da revisão original.
6. Para efeitos de produção, confira conclusões de **jobs e passos**, depois as saídas efetivas, separando aceitação local, aceitação HTTP, confirmação Message e verificação de integridade.
7. **Não replique conteúdos sensíveis obtidos das execuções** ao produzir auditoria pública.

Os dois outros arquivos documentam interpretação e as lacunas da síntese: [evolução prática](evolucao-pratica-12-commits.md) e [omissões](complemento-omissoes-12-commits.md). Este arquivo não altera o executável do repositório.

## Autoria e responsabilidade pela aplicação

- **Autor da análise, redação, seleção das evidências e conclusões deste relatório:** ChatGPT (GPT-6).
- **Responsável pelas decisões editoriais e pela execução integral da tarefa:** ChatGPT (GPT-6). A elaboração e aplicação do texto foram executadas sem solicitar decisões editoriais ao usuário.
- **Responsável pela criação e publicação dos arquivos no repositório:** ChatGPT (GPT-6), por meio da integração GitHub.
- **Metadados nativos do Git:** os campos `author` e `committer` dos commits feitos pela integração aparecem sob a conta autenticada (`morfalespi`); essa identificação técnica é distinta da atribuição da elaboração e aplicação acima.
