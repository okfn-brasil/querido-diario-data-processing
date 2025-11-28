# 🧪 Testes de Regressão - Paginação de Gazettes

**Data:** 2025-11-28  
**Versão:** 1.0  
**Objetivo:** Prevenir regressão do erro `TypeError: PostgreSQL.select() takes 2 positional arguments but 3 were given`

---

## 📋 Resumo

Foram criados **testes abrangentes** para garantir que a paginação funciona corretamente e que o erro de parâmetros do PostgreSQL **nunca mais aconteça**.

---

## 📁 Arquivos Criados

### 1. `tests/list_gazettes_pagination_tests.py` (Principal)

**Conteúdo:**
- 2 classes de testes
- 15 métodos de teste
- ~450 linhas de código

**Classes:**

#### `GazettesListingPaginationTests`
Testa a funcionalidade de paginação em si:
- ✅ Paginação com diferentes tamanhos de página
- ✅ Incremento correto de OFFSET
- ✅ Parada quando não há mais resultados
- ✅ Parada em página parcial
- ✅ Estrutura correta dos dados retornados
- ✅ Roteamento para funções corretas
- ✅ Tamanho de página padrão

#### `GazettesListingRegressionTests`
Testa especificamente contra regressões:
- ✅ **Assinatura do método select()** - O teste mais importante!
- ✅ Segurança contra SQL injection
- ✅ Valores numéricos em LIMIT/OFFSET

---

### 2. `tests/validate_pagination_tests.py` (Validador Standalone)

**Conteúdo:**
- Script Python executável
- Valida código sem precisar de dependências
- Pode ser usado em CI/CD

**Validações:**
1. ✅ QUERY_PAGE_SIZE está definido
2. ✅ Usa f-strings (não placeholders)
3. ✅ Não tenta passar parâmetros extras para select()
4. ✅ Implementa loop de paginação
5. ✅ Tem condições de parada
6. ✅ Converte valores para int (segurança)
7. ✅ Tem logging de progresso
8. ✅ Arquivo de teste existe e é válido

---

## 🎯 Teste Mais Importante (Anti-Regressão)

### `test_select_method_signature_compatibility()`

Este é o teste **crucial** que previne a regressão:

```python
def test_select_method_signature_compatibility(self):
    """
    REGRESSÃO: Garante que select() é sempre chamado com a assinatura correta
    
    Este teste falha se tentarmos passar parâmetros extras para select(),
    prevenindo a regressão do bug original:
    TypeError: PostgreSQL.select() takes 2 positional arguments but 3 were given
    """
    database_mock = MagicMock()
    
    # Configura o mock para aceitar APENAS 1 argumento
    def strict_select(command):
        """Mock que rejeita chamadas com mais de 1 argumento"""
        if not isinstance(command, str):
            raise TypeError("select() expects a string command")
        return []
    
    database_mock.select.side_effect = strict_select

    # Se o código tentar passar parâmetros extras, este teste falhará
    try:
        list(get_unprocessed_gazettes(database_mock))
        # Se chegou aqui, está OK
    except TypeError as e:
        self.fail(f"select() foi chamado com assinatura incorreta: {e}")
```

**Como funciona:**
1. Mock simula comportamento estrito do PostgreSQL.select()
2. Aceita APENAS 1 argumento (string)
3. Se o código tentar passar 2 argumentos, **o teste falha**
4. Se alguém reverter para `database.select(command, params)`, **o teste detecta imediatamente**

---

## 🚀 Como Executar os Testes

### Opção 1: Validação Rápida (Sem dependências)

```bash
cd tests/
python validate_pagination_tests.py
```

**Saída esperada:**
```
============================================================
VALIDAÇÃO DE TESTES DE REGRESSÃO DE PAGINAÇÃO
============================================================
✅ TODAS as validações passaram!
✅ VALIDAÇÃO COMPLETA: Tudo OK!
```

---

### Opção 2: Testes Completos (Com dependências)

```bash
# Com pytest
pytest tests/list_gazettes_pagination_tests.py -v

# Ou com unittest
python -m unittest tests.list_gazettes_pagination_tests -v

# Ou direto (se PYTHONPATH estiver configurado)
cd tests/
python list_gazettes_pagination_tests.py
```

**Saída esperada:**
```
test_get_unprocessed_gazettes_pagination_with_small_page_size ... ok
test_get_unprocessed_gazettes_queries_contain_limit_and_offset ... ok
test_get_unprocessed_gazettes_stops_when_no_more_results ... ok
...
test_select_method_signature_compatibility ... ok
test_sql_injection_safety_numeric_values ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.XXXs

OK
```

---

### Opção 3: Executar em CI/CD

Adicione ao `.github/workflows/` ou script de CI:

```yaml
- name: Validate Pagination Implementation
  run: python tests/validate_pagination_tests.py

- name: Run Pagination Regression Tests
  run: |
    pip install -r requirements-dev.txt
    pytest tests/list_gazettes_pagination_tests.py -v
```

---

## 📊 Cobertura de Testes

### Funções Testadas
- ✅ `get_gazettes_to_be_processed()`
- ✅ `get_gazettes_extracted_since_yesterday()`
- ✅ `get_all_gazettes_extracted()`
- ✅ `get_unprocessed_gazettes()`

### Cenários Testados
- ✅ Paginação com páginas completas
- ✅ Paginação com página parcial final
- ✅ Página vazia (nenhum resultado)
- ✅ Diferentes tamanhos de página (2, 3, 5, 10, 50, 100, 1000)
- ✅ Incremento correto de OFFSET
- ✅ Condições de parada
- ✅ Estrutura de dados retornados
- ✅ Roteamento de modos de execução
- ✅ **Assinatura do método select() (CRÍTICO)**
- ✅ Segurança contra SQL injection
- ✅ Valores numéricos em queries

---

## 🔍 Como Identificar Regressão

Se alguém tentar reverter para o código incorreto:

```python
# ❌ CÓDIGO INCORRETO (causará falha nos testes)
params = {"limit": QUERY_PAGE_SIZE, "offset": offset}
page_results = list(database.select(command, params))
```

**Os seguintes testes falharão:**
1. `test_select_method_signature_compatibility()` ← **Principal**
2. `test_get_unprocessed_gazettes_pagination_with_small_page_size()`
3. `test_get_unprocessed_gazettes_queries_contain_limit_and_offset()`
4. Todos os outros testes de paginação

**Mensagem de erro esperada:**
```
TypeError: select() expects a string command
# ou
AssertionError: select() deve receber apenas 1 argumento (SQL command), recebeu 2
```

---

## 📝 Checklist de Validação

Antes de fazer merge de mudanças em `list_gazettes_to_be_processed.py`:

- [ ] Executar `python tests/validate_pagination_tests.py`
- [ ] Executar testes unitários completos
- [ ] Verificar que select() é chamado com 1 argumento
- [ ] Verificar que LIMIT e OFFSET usam f-strings
- [ ] Verificar que não há placeholders %(limit)s ou %(offset)s
- [ ] Code review aprovado

---

## 🎓 Lições para Desenvolvedores

### ⚠️ O que NÃO fazer:

```python
# ❌ INCORRETO - Vai falhar em produção
command = "SELECT * FROM gazettes LIMIT %(limit)s OFFSET %(offset)s"
params = {"limit": 100, "offset": 0}
database.select(command, params)  # TypeError!
```

### ✅ O que fazer:

```python
# ✅ CORRETO - Funciona
command = f"SELECT * FROM gazettes LIMIT {limit} OFFSET {offset}"
database.select(command)  # OK!
```

### 🔒 Por que é seguro?

```python
# limit e offset são sempre int, nunca string arbitrária
QUERY_PAGE_SIZE = int(os.environ.get("GAZETTE_QUERY_PAGE_SIZE", 1000))
offset = 0
offset += QUERY_PAGE_SIZE  # Sempre múltiplo de QUERY_PAGE_SIZE
```

---

## 📚 Referências

- **Bug Original:** `TypeError: PostgreSQL.select() takes 2 positional arguments but 3 were given`
- **Hotfix:** HOTFIX_POSTGRESQL_PARAMS.md
- **Implementação:** PHASE_0_OOM_FIXES.md
- **Código:** tasks/list_gazettes_to_be_processed.py

---

## ✅ Status

- [x] Testes implementados
- [x] Validador standalone criado
- [x] Documentação completa
- [x] Validação passou (8/8 checks)
- [x] Sintaxe validada
- [ ] Executar testes em ambiente com dependências
- [ ] Adicionar ao CI/CD pipeline

---

## 🚦 Próximos Passos

1. **Executar testes em ambiente com dependências instaladas**
   ```bash
   pip install -r requirements-dev.txt
   pytest tests/list_gazettes_pagination_tests.py -v
   ```

2. **Adicionar ao CI/CD**
   - Adicionar validação automática em PRs
   - Bloquear merge se testes falharem

3. **Monitorar em produção**
   - Confirmar que paginação funciona
   - Confirmar que não há mais erros de TypeError

---

**Versão:** 1.0  
**Última atualização:** 2025-11-28  
**Autor:** GitHub Copilot CLI  
**Status:** ✅ Pronto para uso
