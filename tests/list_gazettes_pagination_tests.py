"""
Testes para as funções de listagem de gazettes com paginação

Inclui testes de regressão para garantir que:
1. A paginação funciona corretamente
2. database.select() é chamado com assinatura correta
3. Queries SQL contêm LIMIT e OFFSET corretos
4. Não há tentativa de passar parâmetros separados para select()
"""

import os
from datetime import date, datetime
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from tasks.list_gazettes_to_be_processed import (
    get_all_gazettes_extracted,
    get_gazettes_extracted_since_yesterday,
    get_gazettes_to_be_processed,
    get_unprocessed_gazettes,
)


class GazettesListingPaginationTests(TestCase):
    """
    Testes para garantir que a paginação funciona corretamente
    e prevenir regressão do erro de parâmetros do PostgreSQL
    """

    def setUp(self):
        """Setup comum para todos os testes"""
        self.database_mock = MagicMock()
        
        # Mock data - simula resultados do banco
        self.sample_gazette_row = (
            1,  # id
            "",  # source_text
            date(2020, 10, 18),  # date
            "1",  # edition_number
            False,  # is_extra_edition
            "executive",  # power
            "checksum-123",  # file_checksum
            "path/to/file.pdf",  # file_path
            "http://example.com/file.pdf",  # file_url
            datetime.now(),  # scraped_at
            datetime.now(),  # created_at
            "3550308",  # territory_id
            False,  # processed
            "Test City",  # territory_name
            "SC",  # state_code
        )

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "2"})
    def test_get_unprocessed_gazettes_pagination_with_small_page_size(self):
        """
        Testa que a paginação funciona com página pequena
        REGRESSÃO: Garante que select() é chamado corretamente SEM parâmetros extras
        """
        # Simula 5 gazettes no total (3 páginas: 2 + 2 + 1)
        self.database_mock.select.side_effect = [
            [self.sample_gazette_row, self.sample_gazette_row],  # Página 1: 2 itens
            [self.sample_gazette_row, self.sample_gazette_row],  # Página 2: 2 itens
            [self.sample_gazette_row],  # Página 3: 1 item
        ]

        # Executa a função
        result = list(get_unprocessed_gazettes(self.database_mock))

        # Verifica que retornou 5 gazettes
        self.assertEqual(len(result), 5)

        # CRÍTICO: Verifica que select() foi chamado 3 vezes
        self.assertEqual(self.database_mock.select.call_count, 3)

        # CRÍTICO: Verifica que cada chamada teve APENAS 1 argumento (o comando SQL)
        for call_args in self.database_mock.select.call_args_list:
            args, kwargs = call_args
            self.assertEqual(
                len(args),
                1,
                msg=f"select() deve receber apenas 1 argumento (SQL command), recebeu {len(args)}",
            )
            self.assertEqual(
                len(kwargs),
                0,
                msg=f"select() não deve receber kwargs, recebeu {kwargs}",
            )

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "100"})
    def test_get_unprocessed_gazettes_queries_contain_limit_and_offset(self):
        """
        Testa que as queries SQL contêm LIMIT e OFFSET corretos
        REGRESSÃO: Garante que os valores são embutidos no SQL (f-string), não passados como parâmetros
        """
        # Simula uma página com resultados
        self.database_mock.select.return_value = [self.sample_gazette_row]

        # Executa a função
        list(get_unprocessed_gazettes(self.database_mock))

        # Verifica que select() foi chamado
        self.assertTrue(self.database_mock.select.called)

        # Pega o comando SQL da primeira chamada
        first_call_args = self.database_mock.select.call_args_list[0]
        sql_command = first_call_args[0][0]  # Primeiro argumento posicional

        # CRÍTICO: Verifica que LIMIT e OFFSET estão no SQL
        self.assertIn("LIMIT 100", sql_command, "SQL deve conter 'LIMIT 100'")
        self.assertIn("OFFSET 0", sql_command, "SQL deve conter 'OFFSET 0'")

        # CRÍTICO: Verifica que NÃO usa placeholders de parâmetros
        self.assertNotIn("%(limit)s", sql_command, "SQL não deve usar placeholder %(limit)s")
        self.assertNotIn("%(offset)s", sql_command, "SQL não deve usar placeholder %(offset)s")

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "3"})
    def test_get_unprocessed_gazettes_stops_when_no_more_results(self):
        """
        Testa que a iteração para quando não há mais resultados
        """
        # Simula 2 páginas: primeira com 3 itens, segunda vazia
        self.database_mock.select.side_effect = [
            [self.sample_gazette_row, self.sample_gazette_row, self.sample_gazette_row],
            [],  # Página vazia - deve parar aqui
        ]

        result = list(get_unprocessed_gazettes(self.database_mock))

        # Verifica que retornou apenas 3 gazettes
        self.assertEqual(len(result), 3)

        # Verifica que select() foi chamado apenas 2 vezes
        self.assertEqual(self.database_mock.select.call_count, 2)

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "10"})
    def test_get_unprocessed_gazettes_stops_when_partial_page(self):
        """
        Testa que a iteração para quando recebe página parcial (menos que page_size)
        """
        # Simula página com menos itens que o page_size (10)
        self.database_mock.select.return_value = [
            self.sample_gazette_row,
            self.sample_gazette_row,
            self.sample_gazette_row,
        ]  # 3 < 10

        result = list(get_unprocessed_gazettes(self.database_mock))

        # Verifica que retornou 3 gazettes
        self.assertEqual(len(result), 3)

        # Verifica que select() foi chamado apenas 1 vez (não tentou próxima página)
        self.assertEqual(self.database_mock.select.call_count, 1)

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "2"})
    def test_get_unprocessed_gazettes_offset_increments_correctly(self):
        """
        Testa que o OFFSET incrementa corretamente a cada página
        """
        self.database_mock.select.side_effect = [
            [self.sample_gazette_row, self.sample_gazette_row],  # Página 1
            [self.sample_gazette_row, self.sample_gazette_row],  # Página 2
            [self.sample_gazette_row],  # Página 3
        ]

        list(get_unprocessed_gazettes(self.database_mock))

        # Verifica os OFFSETs nas chamadas
        calls = self.database_mock.select.call_args_list
        
        sql_1 = calls[0][0][0]
        sql_2 = calls[1][0][0]
        sql_3 = calls[2][0][0]

        self.assertIn("OFFSET 0", sql_1, "Primeira página deve ter OFFSET 0")
        self.assertIn("OFFSET 2", sql_2, "Segunda página deve ter OFFSET 2")
        self.assertIn("OFFSET 4", sql_3, "Terceira página deve ter OFFSET 4")

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "5"})
    def test_get_all_gazettes_extracted_uses_pagination(self):
        """
        Testa que get_all_gazettes_extracted também usa paginação
        """
        self.database_mock.select.side_effect = [
            [self.sample_gazette_row] * 5,  # Página completa
            [self.sample_gazette_row] * 3,  # Página parcial - deve parar
        ]

        result = list(get_all_gazettes_extracted(self.database_mock))

        self.assertEqual(len(result), 8)
        self.assertEqual(self.database_mock.select.call_count, 2)

        # Verifica que todas as chamadas têm apenas 1 argumento
        for call_args in self.database_mock.select.call_args_list:
            args, _ = call_args
            self.assertEqual(len(args), 1)

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "5"})
    def test_get_gazettes_extracted_since_yesterday_uses_pagination(self):
        """
        Testa que get_gazettes_extracted_since_yesterday também usa paginação
        """
        self.database_mock.select.side_effect = [
            [self.sample_gazette_row] * 5,  # Página completa
            [],  # Vazio
        ]

        result = list(get_gazettes_extracted_since_yesterday(self.database_mock))

        self.assertEqual(len(result), 5)
        self.assertEqual(self.database_mock.select.call_count, 2)

    def test_get_gazettes_to_be_processed_routes_to_correct_function(self):
        """
        Testa que get_gazettes_to_be_processed roteia corretamente
        """
        self.database_mock.select.return_value = []

        # Testa UNPROCESSED
        list(get_gazettes_to_be_processed("UNPROCESSED", self.database_mock))
        self.assertTrue(self.database_mock.select.called)
        self.database_mock.reset_mock()

        # Testa ALL
        list(get_gazettes_to_be_processed("ALL", self.database_mock))
        self.assertTrue(self.database_mock.select.called)
        self.database_mock.reset_mock()

        # Testa DAILY
        list(get_gazettes_to_be_processed("DAILY", self.database_mock))
        self.assertTrue(self.database_mock.select.called)

    def test_get_gazettes_to_be_processed_raises_on_invalid_mode(self):
        """
        Testa que levanta exceção para modo inválido
        """
        with self.assertRaises(Exception) as context:
            list(get_gazettes_to_be_processed("INVALID", self.database_mock))

        self.assertIn("invalid", str(context.exception).lower())

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "1000"})
    def test_default_page_size_is_used(self):
        """
        Testa que o page_size padrão (1000) é usado quando não configurado
        """
        # Remove a variável de ambiente
        if "GAZETTE_QUERY_PAGE_SIZE" in os.environ:
            del os.environ["GAZETTE_QUERY_PAGE_SIZE"]

        self.database_mock.select.return_value = [self.sample_gazette_row]

        list(get_unprocessed_gazettes(self.database_mock))

        sql_command = self.database_mock.select.call_args[0][0]
        self.assertIn("LIMIT 1000", sql_command, "Deve usar LIMIT padrão de 1000")

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "2"})
    def test_pagination_returns_correct_data_structure(self):
        """
        Testa que a paginação retorna dicionários com estrutura correta
        """
        self.database_mock.select.return_value = [self.sample_gazette_row]

        result = list(get_unprocessed_gazettes(self.database_mock))

        self.assertEqual(len(result), 1)
        gazette = result[0]

        # Verifica estrutura do dicionário
        self.assertIsInstance(gazette, dict)
        self.assertIn("id", gazette)
        self.assertIn("file_checksum", gazette)
        self.assertIn("file_path", gazette)
        self.assertIn("territory_id", gazette)
        self.assertIn("processed", gazette)
        self.assertEqual(gazette["id"], 1)
        self.assertEqual(gazette["file_checksum"], "checksum-123")


class GazettesListingRegressionTests(TestCase):
    """
    Testes específicos de regressão para o bug de parâmetros do PostgreSQL
    """

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "100"})
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

    @patch.dict("os.environ", {"GAZETTE_QUERY_PAGE_SIZE": "50"})
    def test_sql_injection_safety_numeric_values(self):
        """
        Testa que os valores usados em f-strings são sempre numéricos e seguros
        """
        database_mock = MagicMock()
        database_mock.select.return_value = []

        list(get_unprocessed_gazettes(database_mock))

        sql_command = database_mock.select.call_args[0][0]

        # Verifica que LIMIT e OFFSET são números inteiros no SQL
        import re
        limit_match = re.search(r"LIMIT\s+(\d+)", sql_command)
        offset_match = re.search(r"OFFSET\s+(\d+)", sql_command)

        self.assertIsNotNone(limit_match, "SQL deve conter LIMIT com valor numérico")
        self.assertIsNotNone(offset_match, "SQL deve conter OFFSET com valor numérico")

        # Verifica que são números válidos
        limit_value = int(limit_match.group(1))
        offset_value = int(offset_match.group(1))

        self.assertGreater(limit_value, 0, "LIMIT deve ser positivo")
        self.assertGreaterEqual(offset_value, 0, "OFFSET deve ser não-negativo")


if __name__ == "__main__":
    import unittest

    unittest.main()
