# Monitoramento e Logging Estruturado

Este módulo fornece logging estruturado para monitorar conexões com Apache Tika e OpenSearch, ajudando a diagnosticar problemas de conectividade e performance.

## Funcionalidades

### 1. Logging Estruturado

O módulo registra automaticamente:

**Apache Tika:**
- Requisições (arquivo, tamanho, tipo MIME)
- Respostas (duração, tamanho da resposta)
- Erros (tipo, mensagem, duração até falha)

**OpenSearch:**
- Operações (index, search, etc.)
- Duração de cada operação
- Erros e falhas

### 2. Monitor de Estatísticas

Coleta estatísticas em tempo real:
- Total de requisições/operações
- Taxa de sucesso/falha
- Duração média
- Tipos de erros mais comuns

### 3. Análise de Logs

Script para analisar logs e identificar problemas.

## Uso

### Configuração Automática

O monitoramento é configurado automaticamente ao iniciar o pipeline. Não é necessário nenhuma configuração adicional.

### Logs Gerados

Os logs seguem o formato:

```
2025-11-29 14:30:45 [INFO] tika.request - TIKA_REQUEST
2025-11-29 14:30:47 [INFO] tika.response - TIKA_RESPONSE
2025-11-29 14:30:50 [ERROR] tika.error - TIKA_ERROR
2025-11-29 14:30:51 [INFO] opensearch.operation - OPENSEARCH_OPERATION
```

### Analisando Logs

Use o script `analyze_logs.py` para analisar logs e identificar problemas:

```bash
# Analisar logs de container Docker
docker logs querido-diario-data-processing 2>&1 | python scripts/analyze_logs.py -

# Analisar arquivo de log
python scripts/analyze_logs.py /var/log/querido-diario-processing.log

# Analisar logs em tempo real
docker logs -f querido-diario-data-processing 2>&1 | python scripts/analyze_logs.py -
```

### Relatório de Análise

O script gera um relatório detalhado:

```
======================================================================
RELATÓRIO DE ANÁLISE DE LOGS - QUERIDO DIÁRIO DATA PROCESSING
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

🔍 OPENSEARCH
----------------------------------------------------------------------
Total de operações: 145
Operações por tipo:
  - index: 145

Duração média: 123.45ms

🔌 PROBLEMAS DE CONEXÃO
----------------------------------------------------------------------
⚠️  Total de problemas detectados: 5

Detalhes:
  - ChunkedEncodingError: 3
  - ConnectionError: 2
  - IncompleteRead: 0

💡 RECOMENDAÇÕES:
  • ChunkedEncodingError detectado - Possíveis causas:
    - Tika server encerrando conexão prematuramente
    - Timeout na rede entre containers
    - Arquivo muito grande causando timeout
    - Problema de memória no Tika
```

## Investigando o ChunkedEncodingError

O erro `ChunkedEncodingError: IncompleteRead` indica que o Tika encerrou a conexão antes de enviar todos os dados. Possíveis causas:

### 1. Arquivo Muito Grande
```bash
# Verificar tamanhos de arquivos que falharam
docker logs querido-diario-data-processing 2>&1 | grep "TIKA_ERROR" | grep -o "file_size_mb[: ]*[0-9.]*"
```

**Solução:** Aumentar `MAX_GAZETTE_FILE_SIZE_MB` ou adicionar timeout maior

### 2. Timeout de Rede
```bash
# Verificar durações até erro
docker logs querido-diario-data-processing 2>&1 | grep "TIKA_ERROR" | grep -o "duration_ms[: ]*[0-9.]*"
```

**Solução:** Aumentar timeout no docker-compose.yml:
```yaml
apache-tika:
  environment:
    - TIKA_REQUEST_TIMEOUT=300000  # 5 minutos
```

### 3. Memória Insuficiente no Tika
```bash
# Verificar uso de memória do Tika
docker stats apache-tika
```

**Solução:** Aumentar memória alocada:
```yaml
apache-tika:
  deploy:
    resources:
      limits:
        memory: 4G
```

### 4. Tika Crashando

```bash
# Verificar logs do Tika
docker logs apache-tika 2>&1 | grep -i "error\|exception\|crash"
```

**Solução:** Verificar logs do Tika e ajustar configurações

## Estatísticas em Tempo Real

Ao final da execução, o monitor imprime um resumo:

```python
from monitoring import get_monitor

monitor = get_monitor()
monitor.print_summary()
```

Saída:
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

## Integração Manual

Se precisar adicionar monitoramento em outro módulo:

```python
from monitoring import log_tika_request, log_tika_response, log_tika_error
import time

# Antes da requisição
log_tika_request(filepath, file_size, content_type, tika_url)

start_time = time.time()
try:
    # Fazer requisição ao Tika
    response = requests.put(...)
    duration_ms = (time.time() - start_time) * 1000
    
    # Registrar sucesso
    log_tika_response(filepath, duration_ms, len(response.text), response.status_code)
except Exception as e:
    duration_ms = (time.time() - start_time) * 1000
    
    # Registrar erro
    log_tika_error(filepath, type(e).__name__, str(e), duration_ms, file_size)
    raise
```

## Variáveis de Ambiente

- `DEBUG=1` - Ativa logs de debug com mais detalhes

## Próximos Passos

1. **Alertas Automáticos**: Adicionar alertas quando taxa de erro > 5%
2. **Métricas Prometheus**: Exportar métricas para Prometheus/Grafana
3. **Retry Automático**: Implementar retry com backoff exponencial
4. **Circuit Breaker**: Adicionar circuit breaker para proteger Tika
