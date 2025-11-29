# Guia de Uso - Monitoramento de Conexões Tika e OpenSearch

## Visão Geral

Sistema de logging estruturado adicionado para monitorar e diagnosticar problemas de conexão entre o querido-diario-data-processing e os serviços Apache Tika e OpenSearch.

## Como Usar

### 1. Executar com Monitoramento (Automático)

O monitoramento está **ativado automaticamente**. Basta executar normalmente:

```bash
docker-compose up querido-diario-data-processing
```

### 2. Ver Logs em Tempo Real

```bash
# Ver todos os logs
docker logs -f querido-diario-data-processing

# Filtrar apenas eventos de monitoramento
docker logs -f querido-diario-data-processing 2>&1 | grep -E "TIKA_|OPENSEARCH_"

# Ver apenas erros
docker logs -f querido-diario-data-processing 2>&1 | grep "ERROR"
```

### 3. Analisar Logs

```bash
# Análise em tempo real
docker logs -f querido-diario-data-processing 2>&1 | python scripts/analyze_logs.py -

# Analisar logs existentes
docker logs querido-diario-data-processing > /tmp/logs.txt
python scripts/analyze_logs.py /tmp/logs.txt

# Salvar relatório
docker logs querido-diario-data-processing 2>&1 | \
  python scripts/analyze_logs.py - > relatorio_$(date +%Y%m%d_%H%M%S).txt
```

## Investigando Problemas Específicos

### ChunkedEncodingError / IncompleteRead

Este erro indica que o Tika encerrou a conexão antes de enviar todos os dados.

**1. Identificar arquivos problemáticos:**
```bash
docker logs querido-diario-data-processing 2>&1 | \
  grep "TIKA_ERROR.*ChunkedEncodingError" | \
  grep -o "filepath=[^ ]*"
```

**2. Verificar tamanhos dos arquivos:**
```bash
docker logs querido-diario-data-processing 2>&1 | \
  grep "TIKA_ERROR.*ChunkedEncodingError" | \
  grep -o "file_size_mb=[0-9.]*"
```

**3. Verificar duração até erro:**
```bash
docker logs querido-diario-data-processing 2>&1 | \
  grep "TIKA_ERROR.*ChunkedEncodingError" | \
  grep -o "duration_ms=[0-9.]*"
```

**Possíveis Soluções:**

**A) Arquivos muito grandes (>50MB):**
```bash
# Aumentar limite de tamanho
export MAX_GAZETTE_FILE_SIZE_MB=100
```

**B) Timeout de rede:**
```yaml
# Em docker-compose.yml
apache-tika:
  environment:
    - TIKA_REQUEST_TIMEOUT=300000  # 5 minutos em ms
```

**C) Memória insuficiente no Tika:**
```yaml
# Em docker-compose.yml
apache-tika:
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G
```

**D) Verificar saúde do Tika:**
```bash
# Verificar logs do Tika
docker logs apache-tika 2>&1 | tail -100

# Verificar uso de memória
docker stats apache-tika --no-stream

# Testar endpoint
curl -X GET http://localhost:9998/tika
```

### Requisições Lentas (>30s)

**1. Identificar requisições lentas:**
```bash
docker logs querido-diario-data-processing 2>&1 | \
  python scripts/analyze_logs.py - | \
  grep -A 10 "Requisições lentas"
```

**2. Verificar se é problema de arquivo ou sistema:**
```bash
# Listar arquivos lentos com tamanhos
docker logs querido-diario-data-processing 2>&1 | \
  grep "TIKA_RESPONSE.*duration_ms=[3-9][0-9][0-9][0-9][0-9]" | \
  grep -o "filepath=[^ ]*\|file_size_mb=[0-9.]*\|duration_ms=[0-9.]*"
```

**Possíveis Soluções:**

- Arquivos PDF complexos: normal levar >30s para arquivos grandes
- Tika sobrecarregado: reiniciar container do Tika
- CPU limitada: aumentar recursos alocados

### OpenSearch Lento ou Falhando

**1. Ver operações lentas:**
```bash
docker logs querido-diario-data-processing 2>&1 | \
  grep "OPENSEARCH_OPERATION.*duration_ms=[5-9][0-9][0-9][0-9]"
```

**2. Verificar erros:**
```bash
docker logs querido-diario-data-processing 2>&1 | \
  grep "OPENSEARCH_ERROR"
```

**Possíveis Soluções:**

**A) Documentos muito grandes (>10MB):**
```yaml
# Em docker-compose.yml
opensearch:
  environment:
    - http.max_content_length=200mb
```

**B) OpenSearch lento:**
```bash
# Verificar saúde
curl -u admin:admin "http://localhost:9200/_cluster/health?pretty"

# Verificar uso de recursos
docker stats opensearch --no-stream
```

## Exemplos de Saída

### Logs Estruturados

```
2025-11-29 14:30:45 [INFO] tika.request - TIKA_REQUEST filepath=/tmp/tmpABC/gazette.pdf file_size_mb=5.2 content_type=application/pdf
2025-11-29 14:30:47 [INFO] tika.response - TIKA_RESPONSE filepath=/tmp/tmpABC/gazette.pdf duration_ms=2345.67 response_size_kb=150.2 status_code=200
2025-11-29 14:30:47 [INFO] opensearch.operation - OPENSEARCH_OPERATION operation=index duration_ms=123.45 document_size_kb=150
```

### Relatório de Análise

```
======================================================================
RELATÓRIO DE ANÁLISE DE LOGS
======================================================================

📄 APACHE TIKA
----------------------------------------------------------------------
Total de requisições: 150
Respostas bem-sucedidas: 145
Requisições falhadas: 5
Duração média: 2345.67ms (2.35s)

❌ Erros do Tika:
  - ChunkedEncodingError: 3 ocorrências
  - ConnectionError: 2 ocorrências

⚠️  Requisições lentas (>30s): 2
  - /tmp/tmpXYZ123/gazette.pdf: 45.23s
  - /tmp/tmpABC456/gazette.pdf: 38.91s

💡 RECOMENDAÇÕES:
  • ChunkedEncodingError detectado - Possíveis causas:
    - Tika server encerrando conexão prematuramente
    - Timeout na rede entre containers
    - Arquivo muito grande causando timeout
    - Problema de memória no Tika
```

## Resumo de Estatísticas

Ao final da execução, o sistema imprime automaticamente:

```
=== RESUMO DE CONEXÕES ===

Apache Tika:
  Total de requisições: 150
  Bem-sucedidas: 145
  Falhas: 5
  Duração média: 2345.67ms
  Tipos de erro: {'ChunkedEncodingError': 3, 'ConnectionError': 2}

OpenSearch:
  Total de operações: 145
  Bem-sucedidas: 145
  Falhas: 0
  Duração média: 123.45ms
```

## Debug Avançado

### Ativar Logs de Debug

```bash
# Via docker-compose
docker-compose run -e DEBUG=1 querido-diario-data-processing

# Via docker
docker run -e DEBUG=1 querido-diario-data-processing
```

### Monitorar em Tempo Real

```bash
# Terminal 1: Executar processamento
docker-compose up querido-diario-data-processing

# Terminal 2: Analisar em tempo real
docker logs -f querido-diario-data-processing 2>&1 | \
  python scripts/analyze_logs.py -

# Terminal 3: Ver estatísticas de recursos
watch -n 5 'docker stats --no-stream apache-tika opensearch querido-diario-data-processing'
```

### Comparar Antes e Depois

```bash
# Coletar baseline
docker logs querido-diario-data-processing > baseline_$(date +%Y%m%d).log
python scripts/analyze_logs.py baseline_$(date +%Y%m%d).log > baseline_report.txt

# Após mudanças, coletar novamente
docker logs querido-diario-data-processing > after_$(date +%Y%m%d).log
python scripts/analyze_logs.py after_$(date +%Y%m%d).log > after_report.txt

# Comparar
diff baseline_report.txt after_report.txt
```

## Troubleshooting

### Problema: Muitos ChunkedEncodingError

1. Verificar memória do Tika: `docker stats apache-tika`
2. Aumentar memória do Tika no docker-compose.yml
3. Reduzir tamanho máximo de arquivos: `MAX_GAZETTE_FILE_SIZE_MB=50`

### Problema: Requisições muito lentas

1. Verificar CPU disponível: `docker stats`
2. Verificar logs do Tika: `docker logs apache-tika`
3. Testar Tika manualmente:
   ```bash
   curl -T test.pdf -H "Content-Type: application/pdf" http://localhost:9998/tika
   ```

### Problema: OpenSearch rejeitando documentos

1. Verificar tamanho: logs mostrarão `document_size_kb`
2. Aumentar limite no OpenSearch
3. Verificar se documento está corrompido

## Próximos Passos

1. **Alertas**: Configurar alertas quando taxa de erro > 5%
2. **Grafana**: Exportar métricas para visualização
3. **Retry**: Implementar retry automático com backoff
4. **Circuit Breaker**: Proteger Tika de sobrecarga
