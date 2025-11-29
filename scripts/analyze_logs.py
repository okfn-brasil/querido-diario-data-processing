#!/usr/bin/env python3
"""
Script para analisar logs estruturados e identificar problemas de conexão

Uso:
    python analyze_logs.py <arquivo_de_log>
    
Exemplo:
    python analyze_logs.py /var/log/querido-diario-processing.log
    docker logs querido-diario-data-processing 2>&1 | python analyze_logs.py -
"""

import sys
import re
from collections import defaultdict
from datetime import datetime


def parse_log_line(line):
    """Extrai informações estruturadas de uma linha de log"""
    # Padrões para identificar eventos
    patterns = {
        'tika_request': r'TIKA_REQUEST.*filepath[=:\s]+([^\s]+).*file_size_mb[=:\s]+([0-9.]+)',
        'tika_response': r'TIKA_RESPONSE.*filepath[=:\s]+([^\s]+).*duration_ms[=:\s]+([0-9.]+)',
        'tika_error': r'TIKA_ERROR.*filepath[=:\s]+([^\s]+).*error_type[=:\s]+([^\s]+).*duration_ms[=:\s]+([0-9.]+)',
        'opensearch_operation': r'OPENSEARCH_OPERATION.*operation[=:\s]+([^\s]+).*duration_ms[=:\s]+([0-9.]+)',
        'opensearch_error': r'OPENSEARCH_ERROR.*operation[=:\s]+([^\s]+).*error_type[=:\s]+([^\s]+)',
        'chunked_encoding_error': r'ChunkedEncodingError',
        'connection_error': r'ConnectionError',
        'incomplete_read': r'IncompleteRead',
    }
    
    for event_type, pattern in patterns.items():
        match = re.search(pattern, line)
        if match:
            return event_type, match.groups(), line
    
    return None, None, line


def analyze_logs(log_file):
    """Analisa logs e gera relatório de problemas"""
    
    stats = {
        'tika': {
            'requests': 0,
            'responses': 0,
            'errors': defaultdict(int),
            'total_duration_ms': 0,
            'failed_files': [],
            'slow_requests': [],  # > 30s
        },
        'opensearch': {
            'operations': defaultdict(int),
            'errors': defaultdict(int),
            'total_duration_ms': 0,
            'slow_operations': [],  # > 5s
        },
        'connection_issues': {
            'chunked_encoding': 0,
            'connection_errors': 0,
            'incomplete_reads': 0,
        }
    }
    
    print("Analisando logs...\n")
    
    if log_file == '-':
        lines = sys.stdin
    else:
        lines = open(log_file, 'r')
    
    for line in lines:
        event_type, groups, full_line = parse_log_line(line)
        
        if event_type == 'tika_request':
            stats['tika']['requests'] += 1
            
        elif event_type == 'tika_response':
            stats['tika']['responses'] += 1
            filepath, duration = groups
            duration_ms = float(duration)
            stats['tika']['total_duration_ms'] += duration_ms
            
            if duration_ms > 30000:  # > 30s
                stats['tika']['slow_requests'].append((filepath, duration_ms))
                
        elif event_type == 'tika_error':
            filepath, error_type, duration = groups
            stats['tika']['errors'][error_type] += 1
            stats['tika']['failed_files'].append((filepath, error_type))
            
        elif event_type == 'opensearch_operation':
            operation, duration = groups
            stats['opensearch']['operations'][operation] += 1
            duration_ms = float(duration)
            stats['opensearch']['total_duration_ms'] += duration_ms
            
            if duration_ms > 5000:  # > 5s
                stats['opensearch']['slow_operations'].append((operation, duration_ms))
                
        elif event_type == 'opensearch_error':
            operation, error_type = groups
            stats['opensearch']['errors'][error_type] += 1
            
        elif event_type == 'chunked_encoding_error':
            stats['connection_issues']['chunked_encoding'] += 1
            
        elif event_type == 'connection_error':
            stats['connection_issues']['connection_errors'] += 1
            
        elif event_type == 'incomplete_read':
            stats['connection_issues']['incomplete_reads'] += 1
    
    if log_file != '-':
        lines.close()
    
    return stats


def print_report(stats):
    """Imprime relatório de análise"""
    
    print("=" * 70)
    print("RELATÓRIO DE ANÁLISE DE LOGS - QUERIDO DIÁRIO DATA PROCESSING")
    print("=" * 70)
    
    # Apache Tika
    print("\n📄 APACHE TIKA")
    print("-" * 70)
    print(f"Total de requisições: {stats['tika']['requests']}")
    print(f"Respostas bem-sucedidas: {stats['tika']['responses']}")
    print(f"Requisições falhadas: {stats['tika']['requests'] - stats['tika']['responses']}")
    
    if stats['tika']['responses'] > 0:
        avg_duration = stats['tika']['total_duration_ms'] / stats['tika']['responses']
        print(f"Duração média: {avg_duration:.2f}ms ({avg_duration/1000:.2f}s)")
    
    if stats['tika']['errors']:
        print(f"\n❌ Erros do Tika:")
        for error_type, count in sorted(stats['tika']['errors'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error_type}: {count} ocorrências")
    
    if stats['tika']['slow_requests']:
        print(f"\n⚠️  Requisições lentas (>30s): {len(stats['tika']['slow_requests'])}")
        for filepath, duration in stats['tika']['slow_requests'][:5]:
            print(f"  - {filepath}: {duration/1000:.2f}s")
        if len(stats['tika']['slow_requests']) > 5:
            print(f"  ... e mais {len(stats['tika']['slow_requests']) - 5}")
    
    if stats['tika']['failed_files']:
        print(f"\n❌ Arquivos que falharam: {len(stats['tika']['failed_files'])}")
        for filepath, error_type in stats['tika']['failed_files'][:5]:
            print(f"  - {filepath} ({error_type})")
        if len(stats['tika']['failed_files']) > 5:
            print(f"  ... e mais {len(stats['tika']['failed_files']) - 5}")
    
    # OpenSearch
    print("\n\n🔍 OPENSEARCH")
    print("-" * 70)
    total_ops = sum(stats['opensearch']['operations'].values())
    print(f"Total de operações: {total_ops}")
    
    if stats['opensearch']['operations']:
        print(f"\nOperações por tipo:")
        for op_type, count in sorted(stats['opensearch']['operations'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {op_type}: {count}")
    
    if total_ops > 0:
        avg_duration = stats['opensearch']['total_duration_ms'] / total_ops
        print(f"\nDuração média: {avg_duration:.2f}ms")
    
    if stats['opensearch']['errors']:
        print(f"\n❌ Erros do OpenSearch:")
        for error_type, count in sorted(stats['opensearch']['errors'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error_type}: {count} ocorrências")
    
    if stats['opensearch']['slow_operations']:
        print(f"\n⚠️  Operações lentas (>5s): {len(stats['opensearch']['slow_operations'])}")
        for operation, duration in stats['opensearch']['slow_operations'][:5]:
            print(f"  - {operation}: {duration/1000:.2f}s")
    
    # Problemas de Conexão
    print("\n\n🔌 PROBLEMAS DE CONEXÃO")
    print("-" * 70)
    total_issues = (stats['connection_issues']['chunked_encoding'] + 
                   stats['connection_issues']['connection_errors'] + 
                   stats['connection_issues']['incomplete_reads'])
    
    if total_issues > 0:
        print(f"⚠️  Total de problemas detectados: {total_issues}")
        print(f"\nDetalhes:")
        print(f"  - ChunkedEncodingError: {stats['connection_issues']['chunked_encoding']}")
        print(f"  - ConnectionError: {stats['connection_issues']['connection_errors']}")
        print(f"  - IncompleteRead: {stats['connection_issues']['incomplete_reads']}")
        
        print(f"\n💡 RECOMENDAÇÕES:")
        if stats['connection_issues']['chunked_encoding'] > 0:
            print(f"  • ChunkedEncodingError detectado - Possíveis causas:")
            print(f"    - Tika server encerrando conexão prematuramente")
            print(f"    - Timeout na rede entre containers")
            print(f"    - Arquivo muito grande causando timeout")
            print(f"    - Problema de memória no Tika")
        
        if stats['connection_issues']['incomplete_reads'] > 0:
            print(f"  • IncompleteRead detectado - Possíveis causas:")
            print(f"    - Resposta do Tika cortada")
            print(f"    - Problema de rede intermitente")
            print(f"    - Tika crashando durante processamento")
    else:
        print("✅ Nenhum problema de conexão detectado")
    
    # Resumo Geral
    print("\n\n📊 RESUMO GERAL")
    print("-" * 70)
    
    tika_success_rate = (stats['tika']['responses'] / stats['tika']['requests'] * 100) if stats['tika']['requests'] > 0 else 0
    print(f"Taxa de sucesso Tika: {tika_success_rate:.1f}%")
    
    if total_issues > 0 and stats['tika']['requests'] > 0:
        issue_rate = (total_issues / stats['tika']['requests'] * 100)
        print(f"Taxa de problemas de conexão: {issue_rate:.1f}%")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analyze_logs.py <arquivo_de_log>")
        print("      python analyze_logs.py -  (lê de stdin)")
        print("\nExemplo:")
        print("  docker logs querido-diario-data-processing 2>&1 | python analyze_logs.py -")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    try:
        stats = analyze_logs(log_file)
        print_report(stats)
    except FileNotFoundError:
        print(f"Erro: arquivo '{log_file}' não encontrado")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nAnálise interrompida pelo usuário")
        sys.exit(0)
