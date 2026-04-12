# Docker Build Optimizations

Registro das otimizações aplicadas aos Dockerfiles e ao processo de build multiarch.

## Resumo de Ganhos

| Métrica | Antes | Depois |
|---------|-------|--------|
| Tamanho da imagem (estimado) | ~2.3 GB | ~700 MB–1 GB |
| Maior contribuinte removido | torch CUDA (~1.5 GB) | torch CPU-only (~500 MB) |
| Build subsequente (cache remoto) | 15–30 min | 5–10 min |
| Ferramentas de dev na imagem prod | `black`, `coverage` instalados | removidos |

> Os valores de tamanho são estimativas; confirme com `docker image ls` após o build.

---

## Otimizações Implementadas

### 1. torch CPU-only (`Dockerfile.base`)

`sentence-transformers` puxa o PyTorch completo com suporte a CUDA por padrão (~2 GB).
O projeto usa o modelo BERT apenas para inferência e não possui GPU em produção.

Solução: instalar `torch` com `--index-url https://download.pytorch.org/whl/cpu` antes
dos demais pacotes. O `pip` reutiliza o torch já instalado ao processar os demais
requisitos, evitando o download do build CUDA.

Economia estimada: **~1.5 GB**.

### 2. Separação de dependências de dev (`requirements.txt` / `requirements-dev.txt`)

`black`, `coverage` e `ruff` foram removidos de `requirements.txt` para `requirements-dev.txt`.
A imagem de produção instala apenas `requirements.txt`.

Para desenvolvimento local:
```bash
pip install -r requirements-dev.txt
```

### 3. Remoção de `curl` do builder stage (`Dockerfile.base`)

O `curl` não tem uso no builder após a remoção do `git-lfs` (o modelo BERT é baixado
via `huggingface_hub` em Python, não via curl). Elimina uma camada de `apt-get`
desnecessária.

### 4. OCI labels apenas no runtime stage (`Dockerfile.base`)

Labels no stage intermediário (builder) são descartadas e não aparecem na imagem final,
porém ainda consomem uma camada durante o build. Movidas exclusivamente para o stage
runtime.

### 5. Limpeza de diretórios de teste dos pacotes (`Dockerfile.base`)

Após a instalação dos pacotes Python, são removidos os diretórios `tests/` e `test/`
bundled dentro dos pacotes em `/root/.local`, antes do `COPY` para o runtime stage.

### 6. `TIKA_VERSION` parametrizado (`Dockerfile_apache_tika`)

A versão do Apache Tika foi extraída para um `ARG`:
```
ARG TIKA_VERSION=3.2.2
```

Atualizar o Tika não requer mais edição do Dockerfile:
```bash
make build-tika-server TIKA_VERSION=3.3.0
```

### 7. `REGISTRY` derivado automaticamente do remote git (`Makefile`)

Quando `REGISTRY` não é passado, o valor é inferido da URL do remote `origin`:

| Remote | REGISTRY derivado |
|--------|-------------------|
| `git@github.com:org/repo.git` | `ghcr.io/org` |
| `https://github.com/org/repo.git` | `ghcr.io/org` |
| `git@gitlab.com:org/repo.git` | `registry.gitlab.com/org` |

Override manual ainda funciona: `make build-base-multi-arch REGISTRY=my.registry/org`

---

## Outras Mudanças de Infraestrutura (subagente)

As seguintes mudanças foram aplicadas em commit anterior ao das 7 otimizações acima:

- **`.dockerignore`** criado: exclui `.git`, `tests/`, `debug/`, `docs/`, `models/`, `*.md`
  do contexto de build, reduzindo o contexto de ~25 MB para ~5 MB.
- **`build-essential` / `libpq-dev` / `git-lfs` removidos** do builder: desnecessários
  com `psycopg2-binary`.
- **ARGs de multiarch e labels OCI** adicionados a `Dockerfile.base` e `Dockerfile`.
- **Novos targets no Makefile** com cache remoto: `build-base-multi-arch`,
  `build-multi-arch-optimized`, `build-multi-arch-tika-optimized`, `build-all-multi-arch`,
  `build-multi-arch-load`, `help-build`.

---

## Estrutura de Arquivos Relevantes

```
Dockerfile.base          # Builder + runtime da imagem base (deps + modelo ML)
Dockerfile               # Imagem final (só copia o código sobre a base)
Dockerfile_apache_tika   # Imagem do Apache Tika (multi-stage)
requirements.txt         # Dependências de produção
requirements-dev.txt     # Dependências de dev/test (inclui requirements.txt via -r)
.dockerignore            # Exclusões do contexto de build
Makefile                 # Targets de build com suporte a multiarch e cache remoto
docs/BASE_IMAGE.md       # Guia prático de build para contribuidores
```
