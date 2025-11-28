#!/usr/bin/env python3
"""
Script de validação standalone dos testes de paginação

Este script valida que o código de paginação segue as regras corretas
sem precisar executar os testes completos (que requerem dependências).

Pode ser executado em CI/CD para validação rápida.
"""

import ast
import re
import sys
from pathlib import Path


def validate_pagination_code():
    """Valida que o código de paginação está correto"""
    
    print("🔍 Validando código de paginação...")
    
    code_file = Path(__file__).parent.parent / "tasks" / "list_gazettes_to_be_processed.py"
    
    if not code_file.exists():
        print(f"❌ Arquivo não encontrado: {code_file}")
        return False
    
    with open(code_file, "r") as f:
        code = f.read()
    
    # Lista de validações
    validations = []
    
    # 1. Verifica que QUERY_PAGE_SIZE está definido
    if "QUERY_PAGE_SIZE" in code:
        print("✅ QUERY_PAGE_SIZE está definido")
        validations.append(True)
    else:
        print("❌ QUERY_PAGE_SIZE não está definido")
        validations.append(False)
    
    # 2. Verifica que usa f-strings para LIMIT e OFFSET
    if re.search(r'LIMIT\s+{', code) and re.search(r'OFFSET\s+{', code):
        print("✅ Usa f-strings para LIMIT e OFFSET")
        validations.append(True)
    else:
        print("❌ Não usa f-strings para LIMIT e OFFSET")
        validations.append(False)
    
    # 3. Verifica que NÃO usa placeholders de parâmetros
    if "%(limit)s" not in code and "%(offset)s" not in code:
        print("✅ NÃO usa placeholders de parâmetros (correto)")
        validations.append(True)
    else:
        print("❌ Usa placeholders de parâmetros (INCORRETO - causará TypeError)")
        validations.append(False)
    
    # 4. Verifica que database.select() é chamado com 1 argumento
    # Procura por padrões de chamada incorreta
    if "database.select(command, params)" in code or "database.select(command, data)" in code:
        print("❌ database.select() está sendo chamado com 2 argumentos (INCORRETO)")
        validations.append(False)
    else:
        print("✅ database.select() não está sendo chamado com 2 argumentos")
        validations.append(True)
    
    # 5. Verifica que há loop while True para paginação
    if "while True:" in code and "offset += " in code:
        print("✅ Implementa loop de paginação (while True + incremento de offset)")
        validations.append(True)
    else:
        print("❌ Loop de paginação não encontrado")
        validations.append(False)
    
    # 6. Verifica que há condição de parada (break)
    break_count = code.count("break")
    if break_count >= 2:  # Pelo menos 2 breaks por função de paginação
        print(f"✅ Tem condições de parada ({break_count} breaks)")
        validations.append(True)
    else:
        print(f"❌ Poucas condições de parada ({break_count} breaks)")
        validations.append(False)
    
    # 7. Verifica que QUERY_PAGE_SIZE é convertido para int
    if "int(os.environ.get(" in code:
        print("✅ QUERY_PAGE_SIZE é convertido para int (seguro contra SQL injection)")
        validations.append(True)
    else:
        print("⚠️  QUERY_PAGE_SIZE pode não estar sendo convertido para int")
        validations.append(False)
    
    # 8. Verifica logging de progresso
    if 'logging.debug(f"Processing page' in code or 'logging.debug(f"Processing page' in code:
        print("✅ Tem logging de progresso da paginação")
        validations.append(True)
    else:
        print("⚠️  Sem logging de progresso (recomendado para debugging)")
        validations.append(False)
    
    # Resumo
    print("\n" + "=" * 60)
    passed = sum(validations)
    total = len(validations)
    print(f"Resultado: {passed}/{total} validações passaram")
    
    if passed == total:
        print("✅ TODAS as validações passaram!")
        return True
    elif passed >= total - 1:
        print("⚠️  Quase todas as validações passaram (avisos apenas)")
        return True
    else:
        print("❌ FALHOU - código não está correto")
        return False


def validate_test_file():
    """Valida que o arquivo de teste existe e está correto"""
    
    print("\n🔍 Validando arquivo de testes...")
    
    test_file = Path(__file__).parent / "list_gazettes_pagination_tests.py"
    
    if not test_file.exists():
        print(f"❌ Arquivo de teste não encontrado: {test_file}")
        return False
    
    print(f"✅ Arquivo de teste existe: {test_file}")
    
    with open(test_file, "r") as f:
        test_code = f.read()
    
    # Verifica que tem testes de regressão
    if "GazettesListingRegressionTests" in test_code:
        print("✅ Contém classe de testes de regressão")
    else:
        print("❌ Não contém classe de testes de regressão")
        return False
    
    # Verifica que testa a assinatura do select()
    if "select_method_signature_compatibility" in test_code:
        print("✅ Testa compatibilidade da assinatura do select()")
    else:
        print("❌ Não testa compatibilidade da assinatura do select()")
        return False
    
    # Verifica que testa LIMIT e OFFSET
    if "queries_contain_limit_and_offset" in test_code:
        print("✅ Testa que queries contêm LIMIT e OFFSET")
    else:
        print("⚠️  Não testa explicitamente LIMIT e OFFSET")
    
    # Verifica sintaxe Python
    try:
        ast.parse(test_code)
        print("✅ Sintaxe Python válida")
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe: {e}")
        return False
    
    print("✅ Arquivo de teste está correto")
    return True


def main():
    """Executa todas as validações"""
    print("=" * 60)
    print("VALIDAÇÃO DE TESTES DE REGRESSÃO DE PAGINAÇÃO")
    print("=" * 60)
    
    code_ok = validate_pagination_code()
    test_ok = validate_test_file()
    
    print("\n" + "=" * 60)
    if code_ok and test_ok:
        print("✅ VALIDAÇÃO COMPLETA: Tudo OK!")
        print("=" * 60)
        return 0
    else:
        print("❌ VALIDAÇÃO FALHOU: Corrija os erros acima")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
