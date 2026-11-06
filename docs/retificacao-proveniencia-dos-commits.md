# Retificação factual — proveniência dos commits feitos nesta conversa

**Repositório:** `morfalespi/IC`  
**Data:** 2026-11-06  
**Correção dos registros anteriores:** [e5569677](https://github.com/morfalespi/IC/commit/e55696777efe47a461cfaffab56b8696bf0ba4ce), [bd5fcd62](https://github.com/morfalespi/IC/commit/bd5fcd62efcad3775627396d51b03093dca371de) e [e0ae75eb](https://github.com/morfalespi/IC/commit/e0ae75eb88eb01b6ef4d6cc558e52d0c0d17daf3).

Este registro **corrige declarações anteriores**. Preserva os hashes e distingue dados recuperados do GitHub, resultados das chamadas realizadas nesta conversa e o evento de autorização fornecido pelo usuário. Não transforma declarações editoriais em metadados nativos.

## 1. Operação de publicação efetivamente executada

A integração GitHub foi acionada por ChatGPT (GPT-6), nesta conversa, pelas ferramentas `mcp__GitHub__create_commit` e `mcp__GitHub__update_ref`. Seus parâmetros e resultados para a última publicação, observados na resposta das ferramentas, foram:

```json
{
  "create_commit": {
    "repository_full_name": "morfalespi/IC",
    "parent_sha": "bd5fcd62efcad3775627396d51b03093dca371de",
    "tree_sha": "f8a2ee157e96ce8bca524f0bc21a972c47dc60ed",
    "result": {
      "sha": "e0ae75eb88eb01b6ef4d6cc558e52d0c0d17daf3"
    }
  },
  "update_ref": {
    "repository_full_name": "morfalespi/IC",
    "branch_name": "main",
    "sha": "e0ae75eb88eb01b6ef4d6cc558e52d0c0d17daf3",
    "expected_sha": "bd5fcd62efcad3775627396d51b03093dca371de",
    "force": false,
    "result": {
      "success": true
    }
  }
}
```

**Origem desses valores:** parâmetros da chamada e resultados devolvidos pelas ferramentas GitHub nesta conversa. As ferramentas de escrita usam a API REST do GitHub. O objeto resultante pode ser consultado em [GitHub REST — commit e0ae75eb](https://api.github.com/repos/morfalespi/IC/git/commits/e0ae75eb88eb01b6ef4d6cc558e52d0c0d17daf3). O GitHub não publica, nesse objeto, os parâmetros de chamada ou a identidade do processo cliente que invocou a API; estes provêm da execução da integração nesta conversa.

## 2. Valores dos metadados nativos do commit

Fonte direta: [objeto Git `e0ae75eb` na API do GitHub](https://api.github.com/repos/morfalespi/IC/git/commits/e0ae75eb88eb01b6ef4d6cc558e52d0c0d17daf3).

```json
{
  "sha": "e0ae75eb88eb01b6ef4d6cc558e52d0c0d17daf3",
  "author": {
    "name": "morfalespi",
    "date": "2026-11-06T20:53:00Z"
  },
  "committer": {
    "name": "morfalespi",
    "date": "2026-11-06T20:53:00Z"
  },
  "tree": {
    "sha": "f8a2ee157e96ce8bca524f0bc21a972c47dc60ed"
  },
  "parents": [
    {"sha": "bd5fcd62efcad3775627396d51b03093dca371de"}
  ]
}
```

Este é um **recorte fiel dos campos indicados**, e não uma transcrição integral da resposta. Os objetos `author` e `committer` também incluem um endereço de e-mail, não repetido nesta documentação pública. Esses campos são a identidade registrada no objeto Git, não uma medição do sistema operacional usado pelo cliente da API.

## 3. Registro de instalação apresentado nesta conversa

Fonte: texto do evento de segurança apresentado pelo usuário, com os seguintes valores relevantes:

```text
action=integration_installation.repositories_added
integration=ChatGPT Codex Connector
actor=morfalespi
repositories_added_names=["morfalespi/IC"]
created_at=2026-11-04 17:05:13 -0300
_document_id=l7TWPSi9NqpgEzjYrkiOBQ
```

Esse evento registra a adição do repositório à integração. **Não contém SHA de commit, resultado de `create_commit`, resultado de `update_ref` nem identificação de Linux usado para enviar o commit**. O `user_agent` nele informado corresponde ao navegador presente no evento de autorização; não identifica, por si só, o ambiente executor do commit. A apresentação desse evento como prova direta da chamada específica de criação de commit, nos textos anteriores, foi indevida.

## 4. Ambiente de execução — correção explícita

- **O que se observou:** ChatGPT acionou ferramentas da integração GitHub que enviaram operações ao GitHub pela API REST. Não houve execução de comando `git commit` ou `git push` por ChatGPT em um terminal Linux nesta sequência de publicação.
- **O que os dados não fornecem:** nome da distribuição Linux, kernel, hostname, imagem de contêiner ou identificador de máquina do serviço que processou as chamadas. Não existe campo com esse valor nos objetos Git verificados nem no evento de autorização transcrito.
- **O que não pode ser afirmado como fato:** que um ambiente Linux específico foi usado para emitir essas chamadas, ou que `author`, `committer`, e-mail ou `unsigned` identificam esse ambiente.
- **Identificação do executor na conversa:** ChatGPT (GPT-6) efetuou as chamadas às ferramentas GitHub. Essa observação pertence ao registro da execução nesta conversa, e não a um campo nativo do objeto Git.

## 5. Correção das declarações anteriores

A identificação do evento `integration_installation.repositories_added` como evidência **direta e individual** dos commits foi incorreta. O vínculo factual demonstrável é: (1) o evento apresentado identifica a autorização da integração; (2) as ferramentas GitHub foram acionadas nesta conversa e devolveram os SHAs e resultados acima; (3) os objetos Git correspondentes existem no repositório. **Esses registros não trazem prova de um ambiente Linux executor específico, e o texto anteriormente publicado não poderia suprir esse dado por inferência.**

A correção não modifica retroativamente os commits anteriores nem apaga seus textos: explicita os limites de cada dado junto aos links das fontes.
