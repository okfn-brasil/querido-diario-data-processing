#!/bin/bash
# Script para criar o índice do OpenSearch para o Querido Diário
# Este script é executado automaticamente no início do ambiente de desenvolvimento

set -e

OPENSEARCH_HOST="${OPENSEARCH_HOST:-http://opensearch:9200}"
OPENSEARCH_USER="${OPENSEARCH_USER:-admin}"
OPENSEARCH_PASSWORD="${OPENSEARCH_PASSWORD:-admin}"
INDEX_NAME="${INDEX_NAME:-querido-diario}"

echo "🔍 Aguardando OpenSearch estar disponível..."
until curl -s -u "$OPENSEARCH_USER:$OPENSEARCH_PASSWORD" "$OPENSEARCH_HOST/_cluster/health" > /dev/null 2>&1; do
    echo "   Aguardando OpenSearch..."
    sleep 2
done

echo "✅ OpenSearch está disponível!"

# Verifica se o índice já existe
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -u "$OPENSEARCH_USER:$OPENSEARCH_PASSWORD" "$OPENSEARCH_HOST/$INDEX_NAME")

if [ "$HTTP_CODE" = "200" ]; then
    echo "ℹ️  Índice '$INDEX_NAME' já existe"
    exit 0
elif [ "$HTTP_CODE" != "404" ]; then
    echo "❌ Erro ao verificar índice. HTTP Code: $HTTP_CODE"
    exit 1
fi

echo "📝 Criando índice '$INDEX_NAME'..."

# Cria o índice com mapeamento básico
RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT -u "$OPENSEARCH_USER:$OPENSEARCH_PASSWORD" \
    -H "Content-Type: application/json" \
    "$OPENSEARCH_HOST/$INDEX_NAME" \
    -d '{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "default": {
          "type": "standard"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "source_text": {
        "type": "text",
        "fields": {
          "exact": {
            "type": "keyword"
          }
        }
      },
      "date": {
        "type": "date"
      },
      "scraped_at": {
        "type": "date"
      },
      "territory_id": {
        "type": "keyword"
      },
      "territory_name": {
        "type": "text"
      },
      "state_code": {
        "type": "keyword"
      },
      "edition_number": {
        "type": "keyword"
      },
      "is_extra_edition": {
        "type": "boolean"
      },
      "power": {
        "type": "keyword"
      },
      "file_checksum": {
        "type": "keyword"
      },
      "file_path": {
        "type": "keyword"
      },
      "file_url": {
        "type": "keyword"
      },
      "file_raw_txt": {
        "type": "text"
      },
      "processed": {
        "type": "boolean"
      }
    }
  }
}')

# Separa o corpo da resposta do código HTTP
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo ""
echo "Resposta: $BODY"
echo "HTTP Code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Índice '$INDEX_NAME' criado com sucesso!"
    exit 0
else
    echo "❌ Erro ao criar índice '$INDEX_NAME'"
    exit 1
fi
