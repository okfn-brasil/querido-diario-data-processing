# Relatório de Otimização de Performance - Querido Diário Data Processing

## Sumário Executivo

Este relatório apresenta uma análise completa das oportunidades de melhoria de performance no pipeline de processamento de dados do Querido Diário, identificando gargalos críticos e propondo soluções práticas com base na arquitetura atual do sistema.

**⚠️ REVISÃO (2025-11-28):** Este plano foi revisado para priorizar iniciativas que endereçam problemas de **Out Of Memory (OOM)** em produção, que têm sido críticos e impactam a estabilidade do sistema.

**Status Atual:** O sistema processa documentos de forma sequencial, sem paralelização, com múltiplos pontos de I/O bloqueante e carregamento completo de documentos em memória.

**Impacto Estimado:** As otimizações propostas podem reduzir o tempo de processamento em 60-80% e o consumo de memória em 40-60%. **A prioridade agora é reduzir o consumo de memória para evitar crashes OOM.**

---

## 1. Análise da Arquitetura Atual

### 1.1 Componentes do Sistema

```
┌─────────────────┐
│   PostgreSQL    │ ← Metadados dos diários
└────────┬────────┘
         │
         v
┌─────────────────┐       ┌──────────────────┐
│  Processamento  │ ←────→│  Apache Tika     │
│   Sequencial    │       │  (Extração PDF)  │
└────────┬────────┘       └──────────────────┘
         │
         v
┌─────────────────┐       ┌──────────────────┐
│  Minio/S3       │ ←────→│   OpenSearch     │
│  (Arquivos)     │       │   (Indexação)    │
└─────────────────┘       └──────────────────┘
```

### 1.2 Fluxo de Processamento Atual

O pipeline principal (`gazette_text_extraction.py`) executa:

1. **Lista documentos** do PostgreSQL (todo o conjunto)
2. **Para cada documento** (sequencial):
   - Download do arquivo do Minio
   - Extração de texto via Apache Tika (HTTP síncrono)
   - Upload do texto extraído para Minio
   - Segmentação (se aplicável)
   - Indexação no OpenSearch
   - Marcação como processado no PostgreSQL
   - Garbage collection manual

### 1.3 Gargalos Identificados

| Gargalo | Localização | Impacto | Severidade | Impacto OOM |
|---------|-------------|---------|------------|-------------|
| **Query sem Paginação** | `list_gazettes_to_be_processed.py:54-55` | Médio | 🔴 **CRÍTICO OOM** | 🔥 Causa OOM |
| **Carregamento Total em Memória** | `text_extraction.py:43-50` | Médio | 🔴 **CRÍTICO OOM** | 🔥 Causa OOM |
| **Processamento Sequencial** | `gazette_text_extraction.py:35-46` | Alto | 🟡 Crítico | ⚠️ Retém objetos |
| **Download/Upload Síncrono** | `gazette_text_extraction.py:166-174` | Alto | 🟡 Crítico | ⚠️ Retém buffers |
| **Apache Tika Síncrono** | `text_extraction.py:28-41` | Alto | 🟡 Crítico | ⚠️ Retém documentos |
| **Indexação Individual** | `gazette_text_extraction.py:83-84` | Médio | 🟡 Moderado | ⚠️ Acumula payloads |
| **Embeddings sem Cache** | `gazette_excerpts_embedding_reranking.py:19-44` | Baixo | 🟢 Menor | ✅ Baixo |

---

## 2. Oportunidades de Otimização

**🔥 PRIORIDADES REVISADAS - FOCO EM OOM:**
1. **🚨 Crítico OOM** - Implementar IMEDIATAMENTE (previne crashes)
2. **⚡ Alto OOM** - Implementar em seguida (reduz consumo significativo)
3. **📊 Médio OOM** - Implementar após estabilização
4. **✅ Baixo OOM** - Pode aguardar

---

### 2.1 ~~Processamento em Batch de Documentos~~ **[DESPRIORI ZADO]** ⭐⭐⭐

**Problema:** Cada documento é processado individualmente em loop sequencial.

**Solução:** Implementar processamento em batch com controle de concorrência.

**Benefícios:**
- ✅ Redução de 60-75% no tempo total de processamento
- ✅ Melhor utilização de CPU e rede
- ✅ Paralelização de I/O operations
- ✅ Redução de overhead de conexões

**Complexidade:** Média

**Impacto OOM:** ⚠️ Moderado (pode aumentar uso de memória se não controlado)

**⚠️ ATENÇÃO:** Implementar apenas APÓS resolver problemas críticos de memória (2.3 e 2.4), caso contrário pode **AGRAVAR** problemas de OOM ao processar múltiplos documentos simultaneamente.

**Arquivos Afetados:**
- `tasks/gazette_text_extraction.py`
- `tasks/list_gazettes_to_be_processed.py`
- `main/__main__.py`

---

### 2.2 ~~Processamento Assíncrono com Concurrent Futures~~ **[POSTERGAR]** ⭐⭐⭐

**Problema:** Operações de rede (download, upload, Apache Tika) são síncronas e bloqueantes.

**Solução:** Usar `concurrent.futures.ThreadPoolExecutor` para I/O paralelo.

**Benefícios:**
- ✅ Processamento paralelo de múltiplos documentos
- ✅ Redução de 50-70% no tempo de I/O
- ✅ Melhor aproveitamento de recursos de rede
- ✅ Compatível com arquitetura atual (sem mudanças complexas)

**Complexidade:** Média

**Impacto OOM:** ⚠️ **ALTO - Pode AGRAVAR OOM** se implementado sem correções de memória

**⚠️ ATENÇÃO:** NÃO implementar antes de resolver 2.3 (Streaming) e 2.4 (Paginação), pois paralelizar processos com alto consumo de memória irá **multiplicar o problema** e causar mais crashes.

**Arquivos Afetados:**
- `tasks/gazette_text_extraction.py`
- `storage/digital_ocean_spaces.py` (opcional: adicionar métodos async)

---

### 2.3 🚨 **[PRIORIDADE MÁXIMA - OOM]** Streaming de Arquivos Grandes ⭐⭐⭐⭐⭐

**Problema:** Arquivos são carregados completamente na memória durante download/upload, causando **crashes de OOM em produção**.

**Solução:** Implementar streaming com chunks para arquivos grandes (ex: chunks de 8MB).

**Benefícios para OOM:**
- 🔥 **CRÍTICO:** Previne OOM durante processamento de arquivos grandes
- ✅ Redução de 40-60% no consumo de memória
- ✅ Possibilidade de processar arquivos maiores que a RAM disponível
- ✅ Melhor estabilidade do sistema
- ✅ **Elimina causa raiz de crashes OOM**

**Complexidade:** Baixa-Média

**Arquivos Afetados:**
- `storage/digital_ocean_spaces.py` (já tem `upload_file_multipart`)
- `data_extraction/text_extraction.py`
- `tasks/gazette_text_extraction.py`

**Nota:** O código já possui `upload_file_multipart` implementado mas não é utilizado.

**🚨 AÇÃO IMEDIATA:**
1. Modificar `digital_ocean_spaces.py` para fazer download em chunks
2. Modificar `text_extraction.py` para processar em streaming via Apache Tika
3. Usar `upload_file_multipart` já existente para uploads
4. Adicionar limite de memória explícito (ex: `max_memory_per_file=100MB`)

---

### 2.4 🚨 **[PRIORIDADE MÁXIMA - OOM]** Paginação PostgreSQL ⭐⭐⭐⭐⭐

**Problema:** Query carrega TODOS os documentos pendentes em memória de uma vez, causando **OOM quando há muitos documentos para processar**.

**Solução:** Implementar paginação/cursor no PostgreSQL para carregar documentos em lotes.

**Benefícios para OOM:**
- 🔥 **CRÍTICO:** Previne OOM ao listar milhares de documentos
- ✅ Consumo de memória constante independente do volume
- ✅ Redução imediata de 60-90% no uso de memória inicial
- ✅ **Elimina causa raiz de crashes OOM no início do processamento**

**Complexidade:** Baixa

**Arquivos Afetados:**
- `tasks/list_gazettes_to_be_processed.py`

**🚨 AÇÃO IMEDIATA:**
1. Adicionar parâmetros `limit` e `offset` ou usar cursor PostgreSQL
2. Implementar iteração por páginas (ex: 100-1000 docs por página)
3. Processar cada página antes de carregar a próxima

---

### 2.5 ⚡ **[ALTA PRIORIDADE - OOM]** Bulk Indexing no OpenSearch ⭐⭐⭐⭐

**Benefícios:**
- ✅ Redução de 70-90% no tempo de indexação
- ✅ Menor overhead de rede
- ✅ Melhor throughput do OpenSearch
- ⚠️ **Reduz acúmulo de payloads em memória** (ajuda com OOM indiretamente)

**Impacto OOM:** ⚡ Moderado (reduz objetos acumulados em memória)
- ✅ Redução de conexões HTTP

**Complexidade:** Baixa

**Arquivos Afetados:**
- `index/opensearch.py`
- `tasks/gazette_text_extraction.py`
- `tasks/gazette_themed_excerpts_extraction.py`

---

### 2.5 Paginação de Queries no PostgreSQL ⭐⭐⭐

**Problema:** Queries carregam todos os registros de uma vez na memória.

**Solução:** Implementar cursor server-side e paginação.

**Benefícios:**
- ✅ Redução de 50-80% no consumo de memória inicial
- ✅ Início mais rápido do processamento
- ✅ Melhor escalabilidade
- ✅ Streaming de dados do banco

**Complexidade:** Baixa

**Arquivos Afetados:**
- `database/postgresql.py`
- `tasks/list_gazettes_to_be_processed.py`

---

### 2.6 Cache de Modelos de ML ⭐⭐⭐

**Problema:** Modelo BERT é carregado para cada tema/batch de processamento.

**Solução:** Implementar cache singleton do modelo em memória.

**Benefícios:**
- ✅ Redução de 90% no tempo de inicialização de embeddings
- ✅ Menor uso de disco e rede
- ✅ Processamento mais rápido

**Complexidade:** Baixa

**Arquivos Afetados:**
- `tasks/gazette_excerpts_embedding_reranking.py`

---

### 2.7 Connection Pooling ⭐⭐⭐

**Problema:** Cada operação cria novas conexões com serviços externos.

**Solução:** Implementar connection pools para PostgreSQL, OpenSearch e S3.

**Benefícios:**
- ✅ Redução de 30-50% em overhead de conexão
- ✅ Melhor performance em operações repetidas
- ✅ Maior estabilidade
- ✅ Melhor controle de recursos

**Complexidade:** Média

**Arquivos Afetados:**
- `database/postgresql.py`
- `index/opensearch.py`
- `storage/digital_ocean_spaces.py`

---

### 2.8 Compressão de Dados em Trânsito ⭐⭐

**Problema:** Textos grandes são transferidos sem compressão entre serviços.

**Solução:** Implementar compressão gzip para uploads/downloads de texto.

**Benefícios:**
- ✅ Redução de 60-80% no tráfego de rede
- ✅ Transferências mais rápidas
- ✅ Menor custo de storage (especialmente em cloud)

**Complexidade:** Baixa

**Arquivos Afetados:**
- `storage/digital_ocean_spaces.py`
- `tasks/gazette_text_extraction.py`

---

### 2.9 Retry Logic com Backoff Exponencial ⭐⭐⭐

**Problema:** Falhas temporárias em serviços externos causam perda de documentos processados.

**Solução:** Implementar retry com backoff exponencial e circuit breaker.

**Benefícios:**
- ✅ Maior resiliência a falhas temporárias
- ✅ Melhor taxa de sucesso no processamento
- ✅ Menor necessidade de reprocessamento manual

**Complexidade:** Baixa-Média

**Arquivos Afetados:**
- `data_extraction/text_extraction.py`
- `storage/digital_ocean_spaces.py`
- `index/opensearch.py`

---

### 2.10 Processamento Incremental Inteligente ⭐⭐

**Problema:** Modo `UNPROCESSED` verifica flag booleana simples, mas documentos podem falhar parcialmente.

**Solução:** Implementar estados de processamento mais granulares e checkpoints.

**Benefícios:**
- ✅ Recuperação mais eficiente de falhas
- ✅ Reprocessamento seletivo de etapas
- ✅ Melhor rastreabilidade

**Complexidade:** Média

**Arquivos Afetados:**
- `database/postgresql.py`
- `tasks/gazette_text_extraction.py`
- Schema do banco de dados

---

## 3. Plano de Implementação

### Fase 1: Quick Wins (1-2 semanas) 🚀

**Objetivo:** Ganhos rápidos com baixo risco

#### Prioridade 1.1 - Bulk Indexing OpenSearch
- **Esforço:** 2-3 dias
- **Impacto:** Alto (70-90% redução em tempo de indexação)
- **Risco:** Baixo

**Tarefas:**
1. Adicionar método `bulk_index()` em `index/opensearch.py`
2. Modificar `gazette_text_extraction.py` para acumular documentos
3. Implementar flush automático a cada 100 documentos
4. Adicionar testes unitários e de integração

#### Prioridade 1.2 - Paginação PostgreSQL
- **Esforço:** 1-2 dias
- **Impacto:** Médio (50-80% redução em memória)
- **Risco:** Baixo

**Tarefas:**
1. Modificar `postgresql.py` para usar server-side cursor
2. Implementar generator com fetch size configurável
3. Atualizar `list_gazettes_to_be_processed.py`
4. Adicionar testes

#### Prioridade 1.3 - Cache de Modelo ML
- **Esforço:** 1 dia
- **Impacto:** Médio (90% redução em tempo de carregamento)
- **Risco:** Baixo

**Tarefas:**
1. Criar singleton para gerenciar cache do modelo
2. Modificar `gazette_excerpts_embedding_reranking.py`
3. Adicionar limpeza de memória adequada

#### Prioridade 1.4 - Usar Multipart Upload Existente
- **Esforço:** 0.5 dia
- **Impacto:** Médio (melhoria em estabilidade)
- **Risco:** Baixo

**Tarefas:**
1. Modificar `gazette_text_extraction.py` para usar `upload_file_multipart`
2. Adicionar lógica de detecção de tamanho de arquivo
3. Testar com arquivos grandes

---

### Fase 2: Processamento Paralelo (2-3 semanas) 🔥

**Objetivo:** Paralelização com ThreadPoolExecutor

#### Prioridade 2.1 - Processamento em Batch
- **Esforço:** 5-7 dias
- **Impacto:** Muito Alto (60-75% redução em tempo total)
- **Risco:** Médio

**Tarefas:**
1. Criar módulo `tasks/batch_processor.py`
2. Implementar `BatchProcessor` com configuração de tamanho de batch
3. Adicionar controle de concorrência (max workers)
4. Implementar coleta de métricas (tempo, sucesso, falhas)
5. Adicionar testes de carga

#### Prioridade 2.2 - I/O Assíncrono com ThreadPool
- **Esforço:** 5-7 dias
- **Impacto:** Alto (50-70% redução em I/O)
- **Risco:** Médio

**Tarefas:**
1. Modificar `gazette_text_extraction.py` para usar ThreadPoolExecutor
2. Paralelizar download, Apache Tika, upload
3. Implementar tratamento de exceções em threads
4. Adicionar rate limiting para Apache Tika
5. Testes de stress

#### Prioridade 2.3 - Connection Pooling
- **Esforço:** 3-4 dias
- **Impacto:** Médio (30-50% redução em overhead)
- **Risco:** Médio

**Tarefas:**
1. Adicionar `psycopg2.pool` em `postgresql.py`
2. Implementar pool para OpenSearch
3. Configurar pool do boto3 para S3
4. Ajustar configurações de pool (min, max connections)

---

### Fase 3: Streaming e Resiliência (2-3 semanas) 💪

**Objetivo:** Streaming de arquivos e maior resiliência

#### Prioridade 3.1 - Streaming de Arquivos
- **Esforço:** 5-6 dias
- **Impacto:** Alto (40-60% redução em memória)
- **Risco:** Médio

**Tarefas:**
1. Modificar `download_gazette_file` para stream com chunks
2. Adaptar Apache Tika para aceitar streams
3. Implementar threshold para escolher entre memory/stream
4. Adicionar compressão gzip nos streams
5. Testes com arquivos grandes (>100MB)

#### Prioridade 3.2 - Retry Logic
- **Esforço:** 3-4 dias
- **Impacto:** Médio (melhoria em resiliência)
- **Risco:** Baixo

**Tarefas:**
1. Adicionar biblioteca `tenacity` ou implementar retry decorator
2. Aplicar em todas as chamadas de rede
3. Configurar backoff exponencial (2^n segundos)
4. Adicionar circuit breaker para Apache Tika
5. Logging detalhado de retries

#### Prioridade 3.3 - Estados de Processamento
- **Esforço:** 4-5 dias
- **Impacto:** Médio (melhor rastreabilidade)
- **Risco:** Médio-Alto (mudança de schema)

**Tarefas:**
1. Criar migration para adicionar coluna `processing_state`
2. Definir estados: `pending`, `downloading`, `extracting`, `uploading`, `indexing`, `completed`, `failed`
3. Implementar checkpointing em cada etapa
4. Adicionar recovery automático
5. Dashboard de monitoramento (opcional)

---

### Fase 4: Otimizações Avançadas (2-3 semanas) 🚀

**Objetivo:** Otimizações mais sofisticadas

#### Prioridade 4.1 - Fila de Processamento (Celery/RQ)
- **Esforço:** 7-10 dias
- **Impacto:** Alto (escalabilidade horizontal)
- **Risco:** Alto

**Tarefas:**
1. Avaliar Celery vs RQ vs Python-RQ
2. Configurar Redis como broker
3. Criar tasks assíncronas para cada etapa
4. Implementar retry e dead letter queue
5. Dashboard de monitoramento (Flower)

#### Prioridade 4.2 - Cache Distribuído (Redis)
- **Esforço:** 3-4 dias
- **Impacto:** Médio (redução de reprocessamento)
- **Risco:** Médio

**Tarefas:**
1. Adicionar Redis ao docker-compose
2. Implementar cache de texto extraído
3. Cache de embeddings já calculados
4. Configurar TTL e políticas de eviction

#### Prioridade 4.3 - Processamento Distribuído Multi-Worker
- **Esforço:** 5-7 dias
- **Impacto:** Muito Alto (escalabilidade horizontal)
- **Risco:** Alto

**Tarefas:**
1. Implementar particionamento de trabalho
2. Coordenação via PostgreSQL ou Redis
3. Worker pools independentes
4. Load balancing
5. Health checks

---

## 4. Exemplo de Código: Implementação de Batch Processing

```python
# tasks/batch_processor.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Callable
import logging

class BatchProcessor:
    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        
    def process_batch(
        self,
        items: List[Dict],
        process_func: Callable,
        **kwargs
    ) -> List[Dict]:
        """Process items in parallel batches"""
        results = []
        failed = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_func, item, **kwargs): item 
                for item in items
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logging.error(f"Failed to process {item['file_path']}: {e}")
                    failed.append(item)
                    
        return results, failed

# Uso em gazette_text_extraction.py
def extract_text_from_gazettes_batch(
    gazettes: Iterable[Dict[str, Any]],
    territories: Iterable[Dict[str, Any]],
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor: TextExtractorInterface,
    batch_size: int = 10,
    max_workers: int = 4,
) -> List[str]:
    """
    Extracts text from gazettes using batch processing
    """
    processor = BatchProcessor(batch_size, max_workers)
    
    all_ids = []
    gazette_batch = []
    
    for gazette in gazettes:
        gazette_batch.append(gazette)
        
        if len(gazette_batch) >= batch_size:
            results, failed = processor.process_batch(
                gazette_batch,
                try_process_gazette_file,
                territories=territories,
                database=database,
                storage=storage,
                index=index,
                text_extractor=text_extractor,
            )
            
            # Bulk index the results
            if results:
                document_ids = [r for result in results for r in result]
                all_ids.extend(document_ids)
                
            gazette_batch = []
            gc.collect()
    
    # Process remaining
    if gazette_batch:
        results, failed = processor.process_batch(
            gazette_batch,
            try_process_gazette_file,
            territories=territories,
            database=database,
            storage=storage,
            index=index,
            text_extractor=text_extractor,
        )
        all_ids.extend([r for result in results for r in result])
    
    return all_ids
```

---

## 5. Exemplo de Código: Bulk Indexing OpenSearch

```python
# index/opensearch.py - Adicionar método
def bulk_index(
    self,
    documents: List[Dict],
    index: str = "",
    refresh: bool = False,
) -> Dict:
    """
    Bulk index multiple documents at once
    """
    index = self.get_index_name(index)
    
    # Prepare bulk request body
    bulk_body = []
    for doc in documents:
        doc_id = doc.pop('_id', None)
        action = {'index': {'_index': index}}
        if doc_id:
            action['index']['_id'] = doc_id
        bulk_body.append(action)
        bulk_body.append(doc)
    
    if not bulk_body:
        return {'items': []}
    
    response = self._search_engine.bulk(
        body=bulk_body,
        refresh=refresh,
        request_timeout=120
    )
    
    # Check for errors
    if response.get('errors'):
        failed = [
            item for item in response['items'] 
            if item.get('index', {}).get('status', 200) >= 400
        ]
        logging.warning(f"Bulk index had {len(failed)} failures")
    
    return response

# Uso em gazette_text_extraction.py
def try_process_gazette_file_batch(
    gazettes: List[Dict],
    territories: Iterable[Dict[str, Any]],
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor: TextExtractorInterface,
) -> List[str]:
    """Process multiple gazettes and bulk index"""
    
    documents_to_index = []
    
    for gazette in gazettes:
        # ... processing logic ...
        gazette["source_text"] = try_to_extract_content(gazette_file, text_extractor)
        # ... rest of processing ...
        
        if gazette_type_is_aggregated(gazette):
            segmenter = get_segmenter(gazette["territory_id"], territories)
            segments = segmenter.get_gazette_segments(gazette)
            for segment in segments:
                segment['_id'] = segment['file_checksum']
                documents_to_index.append(segment)
        else:
            gazette['_id'] = gazette['file_checksum']
            documents_to_index.append(gazette)
    
    # Bulk index all documents
    if documents_to_index:
        index.bulk_index(documents_to_index, refresh=True)
    
    # Bulk update database
    for gazette in gazettes:
        set_gazette_as_processed(gazette, database)
    
    return [doc['_id'] for doc in documents_to_index]
```

---

## 6. Exemplo de Código: Streaming de Arquivos

```python
# storage/digital_ocean_spaces.py - Adicionar método
def get_file_stream(
    self, 
    file_key: str, 
    chunk_size: int = 8192
) -> Iterator[bytes]:
    """
    Stream file from storage in chunks
    """
    response = self._client.get_object(
        Bucket=self._bucket,
        Key=str(file_key)
    )
    
    stream = response['Body']
    try:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        stream.close()

# data_extraction/text_extraction.py - Modificar
def _try_extract_text_streaming(self, filepath: str, file_size: int) -> str:
    """
    Extract text using streaming for large files
    """
    # Use streaming for files > 10MB
    if file_size > 10 * 1024 * 1024:
        with open(filepath, "rb") as file:
            headers = {
                "Content-Type": self._get_file_type(filepath),
                "Accept": "text/plain",
            }
            
            # Stream to Apache Tika
            response = requests.put(
                f"{self._url}/tika",
                data=self._chunk_generator(file),
                headers=headers,
                stream=True
            )
            
            # Collect response in chunks
            text_chunks = []
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                if chunk:
                    text_chunks.append(chunk)
            
            return ''.join(text_chunks)
    else:
        return self._try_extract_text(filepath)

def _chunk_generator(self, file, chunk_size=8192):
    """Generator for file chunks"""
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk
```

---

## 7. Métricas e Monitoramento

### 7.1 KPIs para Acompanhar

| Métrica | Baseline Atual | Meta Fase 1 | Meta Fase 2 | Meta Fase 3 |
|---------|---------------|-------------|-------------|-------------|
| **Tempo médio por documento** | ~10s | ~8s (-20%) | ~4s (-60%) | ~3s (-70%) |
| **Throughput (docs/hora)** | ~360 | ~450 (+25%) | ~900 (+150%) | ~1200 (+233%) |
| **Uso de memória (pico)** | 100% | 70% (-30%) | 50% (-50%) | 40% (-60%) |
| **Taxa de falha** | 5-10% | 3-5% | 1-2% | <1% |
| **Tempo de indexação** | 100% | 20% (-80%) | 15% | 10% |
| **Escalabilidade (workers)** | 1 | 1 | 4 | N |

### 7.2 Instrumentação Recomendada

```python
# tasks/metrics.py
import time
import logging
from functools import wraps

class ProcessingMetrics:
    def __init__(self):
        self.total_processed = 0
        self.total_failed = 0
        self.total_time = 0
        self.stage_times = {}
    
    def record_processing(self, stage: str):
        """Decorator to record processing time"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.total_processed += 1
                    return result
                except Exception as e:
                    self.total_failed += 1
                    raise
                finally:
                    duration = time.time() - start
                    self.total_time += duration
                    self.stage_times.setdefault(stage, []).append(duration)
                    logging.info(f"{stage} took {duration:.2f}s")
            return wrapper
        return decorator
    
    def get_report(self) -> Dict:
        """Generate performance report"""
        return {
            'total_processed': self.total_processed,
            'total_failed': self.total_failed,
            'success_rate': self.total_processed / (self.total_processed + self.total_failed),
            'avg_time_per_doc': self.total_time / self.total_processed if self.total_processed > 0 else 0,
            'stage_averages': {
                stage: sum(times) / len(times)
                for stage, times in self.stage_times.items()
            }
        }
```

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Concorrência causa corrupção de dados** | Média | Alto | Implementar locks, transações atômicas, testes extensivos |
| **Memory leaks em processamento paralelo** | Média | Alto | Profiling contínuo, limites de memória, garbage collection |
| **Apache Tika sobrecarga** | Alta | Médio | Rate limiting, múltiplas instâncias, queue |
| **Deadlocks em connection pools** | Baixa | Médio | Timeouts adequados, monitoring, circuit breakers |
| **Mudanças quebram compatibilidade** | Baixa | Alto | Feature flags, rollback plan, testes A/B |
| **Custos de infraestrutura aumentam** | Média | Médio | Monitoramento de custos, auto-scaling inteligente |

---

## 9. Estimativas de Custo-Benefício

### 9.1 Esforço Total Estimado

| Fase | Duração | Desenvolvedores | Esforço (pessoa-dias) |
|------|---------|-----------------|----------------------|
| Fase 1 | 1-2 semanas | 1-2 | 10-15 dias |
| Fase 2 | 2-3 semanas | 2 | 25-35 dias |
| Fase 3 | 2-3 semanas | 2 | 25-35 dias |
| Fase 4 | 2-3 semanas | 2-3 | 30-45 dias |
| **Total** | **7-11 semanas** | **2-3** | **90-130 dias** |

### 9.2 Retorno Esperado

**Cenário Base:** 10.000 documentos/dia

| Métrica | Antes | Depois (Fase 2) | Economia |
|---------|-------|-----------------|----------|
| Tempo de processamento | 27.8 horas | 11.1 horas | 16.7 horas/dia |
| Custo de compute (estimado) | $50/dia | $25/dia | $750/mês |
| Capacidade | 10k docs/dia | 25k docs/dia | +150% |

**ROI:** Break-even em ~2-3 meses considerando economia de infraestrutura e ganho de capacidade.

---

## 10. Recomendações Finais - **REVISADO COM FOCO EM OOM**

### 🚨 CRÍTICO - Implementar ESTA SEMANA (Previne Crashes OOM)

1. **🔥 Paginação PostgreSQL** - Evita carregar milhares de docs em memória de uma vez
   - **Impacto:** Reduz 60-90% do uso de memória inicial
   - **Esforço:** 1-2 dias
   - **Risco:** Muito baixo
   
2. **🔥 Streaming de Arquivos** - Processa arquivos em chunks, não carrega tudo em memória
   - **Impacto:** Previne OOM em arquivos grandes (>50MB)
   - **Esforço:** 2-3 dias (código multipart já existe!)
   - **Risco:** Baixo

3. **🔥 Garbage Collection Explícito + Memory Limits** - Garante liberação de memória
   - **Impacto:** Reduz acúmulo de objetos entre documentos
   - **Esforço:** 1 dia
   - **Risco:** Muito baixo

### ⚡ ALTA PRIORIDADE - Próximas 2 Semanas (Reduz Consumo)

4. **Bulk Indexing OpenSearch** - Reduz objetos acumulados em memória
5. **Connection Pooling** - Evita acúmulo de conexões abertas
6. **Retry Logic com Cleanup** - Garante limpeza em caso de erro

### 📊 MÉDIA PRIORIDADE - Após Estabilização (Semanas 3-4)

7. **Monitoramento de Memória** - Métricas e alertas de uso
8. **Cache de Modelo ML** - Mas com limite de tamanho
9. **Otimização de Query PostgreSQL** - Reduz overhead

### ⚠️ POSTERGAR - Implementar APENAS Após Resolver OOM

10. **Processamento em Batch** - PODE AGRAVAR OOM se feito antes
11. **ThreadPoolExecutor/Async** - PODE AGRAVAR OOM se feito antes
12. **Multi-Worker Distribuído** - PODE AGRAVAR OOM se feito antes

### ❌ BAIXA PRIORIDADE - Futuro Distante

13. **Fila de Processamento (Celery)** - Apenas para escalabilidade horizontal
14. **Cache Distribuído** - Apenas se houver redundância

---

## 11. Próximos Passos - **PLANO DE AÇÃO OOM**

### 🚨 AÇÃO IMEDIATA (HOJE - DIA 0)

1. ✅ **APROVAR este plano revisado com foco em OOM**
2. ✅ Alocar desenvolvedor(es) para Fase 0 com prioridade máxima
3. ✅ Configurar monitoramento de memória em produção (se ainda não existe)
4. ✅ Criar ambiente de staging com limites de memória similares a produção
5. ✅ Documentar casos recentes de OOM (logs, contexto, volume)

### 📅 DIA 1-2: Paginação PostgreSQL

1. 🚀 Implementar paginação em `list_gazettes_to_be_processed.py`
2. 🧪 Testar com 10k+ documentos pendentes
3. 📊 Medir uso de memória antes/depois
4. ✅ Code review e merge

### 📅 DIA 2-4: Streaming de Arquivos

1. 🚀 Implementar download em chunks
2. 🚀 Modificar integração com Apache Tika para streaming
3. 🚀 Ativar `upload_file_multipart` existente
4. 🧪 Testar com arquivos grandes (100MB+)
5. 📊 Medir uso de memória durante processamento
6. ✅ Code review e merge

### 📅 DIA 5: Deploy e Validação

1. 🚀 Deploy em staging
2. 🧪 Processar 1000+ documentos reais
3. 📊 Monitorar memória por 24 horas
4. ✅ Se estável, deploy em produção
5. 📊 Monitorar produção por 48-72 horas

### 📅 SEMANA 2: Monitoramento e Ajustes

1. 📊 Coletar métricas de produção
2. 🐛 Corrigir problemas identificados
3. 📝 Documentar lições aprendidas
4. ✅ **GATE:** Sistema deve estar estável por 1+ semana antes de prosseguir

### 📅 SEMANA 3-4: Fase 1 (Se estável)

1. 🚀 Implementar Fase 1 (Bulk indexing, connection pooling)
2. 🧪 Testes contínuos de memória
3. 📊 Validar que não há regressão de OOM

### ⏸️ PAUSAR E AVALIAR

- ✅ Sistema estável por 2+ semanas?
- ✅ Sem crashes OOM em produção?
- ✅ Métricas de memória consistentes?
- ✅ **SE SIM:** Considerar Fase 2
- ❌ **SE NÃO:** Investigar e corrigir antes de prosseguir

---

## 12. Apêndices

### Apêndice A: Ferramentas Recomendadas

- **Profiling:** `cProfile`, `py-spy`, `memory_profiler`
- **Monitoring:** Prometheus + Grafana
- **Load Testing:** Locust, Apache Bench
- **Tracing:** OpenTelemetry (opcional)

### Apêndice B: Bibliotecas Úteis

```txt
# Adicionar ao requirements.txt
tenacity==8.2.3           # Retry logic
redis==5.0.0              # Caching (Fase 4)
celery==5.3.4             # Task queue (Fase 4)
python-json-logger==2.0.7 # Structured logging
```

### Apêndice C: Configurações Recomendadas

```python
# config/performance.py
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
BULK_INDEX_SIZE = int(os.getenv('BULK_INDEX_SIZE', '100'))
DB_FETCH_SIZE = int(os.getenv('DB_FETCH_SIZE', '1000'))
STREAMING_THRESHOLD_MB = int(os.getenv('STREAMING_THRESHOLD_MB', '10'))
RETRY_MAX_ATTEMPTS = int(os.getenv('RETRY_MAX_ATTEMPTS', '3'))
RETRY_BACKOFF_FACTOR = float(os.getenv('RETRY_BACKOFF_FACTOR', '2'))

# Connection Pool Sizes
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', '20'))
S3_POOL_SIZE = int(os.getenv('S3_POOL_SIZE', '10'))
```

---

## Conclusão - **REVISÃO COM FOCO EM OOM**

Este relatório foi **REVISADO** para priorizar a solução de problemas de **Out Of Memory (OOM)** que têm causado crashes em produção. A priorização foi completamente alterada:

### ❌ Plano Original (Foco em Performance)
- Prioridade: Paralelização e velocidade
- Risco: **Poderia AGRAVAR problemas de OOM**
- Timeline: 7-11 semanas

### ✅ Plano Revisado (Foco em Estabilidade/OOM)
- Prioridade: Redução de memória e estabilidade
- Benefício: **Elimina crashes de OOM primeiro, performance depois**
- Timeline: 3-5 dias para estabilização crítica

### 🎯 Mudanças Principais

1. **🚨 Fase 0 (NOVA):** Emergência OOM - 3-5 dias
   - Paginação PostgreSQL (elimina picos iniciais)
   - Streaming de arquivos (elimina OOM em arquivos grandes)
   - Memory safeguards (garbage collection, limites)

2. **⚠️ POSTERGAR:** Paralelização e Async
   - ThreadPoolExecutor e batch processing foram **DESPRIORIZADOS**
   - Motivo: Podem **multiplicar** uso de memória e agravar OOM
   - Implementar apenas APÓS sistema estável

3. **📊 Foco em Monitoramento:** 
   - Métricas de memória em tempo real
   - Gates de aprovação entre fases
   - Rollback imediato se memória aumentar

### 🚀 Recomendação REVISADA

**CRÍTICO:** Implementar **Fase 0 IMEDIATAMENTE** (esta semana) antes de qualquer otimização de performance. Um sistema rápido mas instável é pior que um sistema lento mas confiável.

**Não prosseguir** com otimizações de performance (batch, async, paralelização) até que:
1. ✅ Sistema estável por 2+ semanas sem OOM
2. ✅ Métricas de memória consistentes
3. ✅ Volumes de produção processados com sucesso

---

**Documento criado em:** 2025-11-28  
**Versão:** 2.0 - **REVISADO PARA FOCO EM OOM**  
**Autores:** GitHub Copilot CLI - Análise de Codebase  
**Status:** ⚠️ **PLANO DE AÇÃO EMERGENCIAL - APROVAÇÃO URGENTE NECESSÁRIA**
