import re

from .diario_municipal import Diario, Municipio

# No final do regex, existe uma estrutura condicional que verifica se o próximo match é um \s ou SECRETARIA. Isso foi feito para resolver um problema no diário de 2018-10-02, em que o município de Coité do Nóia não foi percebido pelo código. Para resolver isso, utilizamos a próxima palavra (SECRETARIA) para tratar esse caso.
# Exceções Notáveis
# String: VAMOS, município Poço das Trincheiras, 06/01/2022, ato CCB3A6AB
re_nomes_municipios = (
    r"ESTADO DE ALAGOAS(?:| )\n{1,2}PREFEITURA MUNICIPAL DE (.*\n{0,2}(?!VAMOS).*$)\n\s(?:\s|SECRETARIA)")


def extrair_diarios_municipais(texto_diario: str, pdf_path: dict, territories: list):
    texto_diario_slice = texto_diario.lstrip().splitlines()

    # Processamento
    linhas_apagar = []  # slice de linhas a ser apagadas ao final.
    ama_header = texto_diario_slice[0]
    ama_header_count = 0
    codigo_count = 0
    codigo_total = texto_diario.count("Código Identificador")

    for num_linha, linha in enumerate(texto_diario_slice):
        # Remoção do cabeçalho AMA, porém temos que manter a primeira aparição.
        if linha.startswith(ama_header):
            ama_header_count += 1
            if ama_header_count > 1:
                linhas_apagar.append(num_linha)

        # Remoção das linhas finais
        if codigo_count == codigo_total:
            linhas_apagar.append(num_linha)
        elif linha.startswith("Código Identificador"):
            codigo_count += 1

    # Apagando linhas do slice
    texto_diario_slice = [l for n, l in enumerate(
        texto_diario_slice) if n not in linhas_apagar]

    # Inserindo o cabeçalho no diário de cada município.
    texto_diarios = {}
    nomes_municipios = re.findall(
        re_nomes_municipios, texto_diario, re.MULTILINE)
    for municipio in nomes_municipios:
        municipio = Municipio(municipio)
        texto_diarios[municipio] = ama_header + '\n\n'

    num_linha = 0
    municipio_atual = None
    while num_linha < len(texto_diario_slice):
        linha = texto_diario_slice[num_linha].rstrip()

        if linha.startswith("ESTADO DE ALAGOAS"):
            nome = nome_municipio(texto_diario_slice, num_linha)
            if nome is not None:
                municipio_atual = Municipio(nome)

        # Só começa, quando algum muncípio for encontrado.
        if municipio_atual is None:
            num_linha += 1
            continue

        # Conteúdo faz parte de um muncípio
        texto_diarios[municipio_atual] += linha + '\n'
        num_linha += 1

    diarios = []
    for municipio, diario in texto_diarios.items():
        diarios.append(Diario(municipio, ama_header, diario, pdf_path, territories).__dict__)

    return diarios


def nome_municipio(texto_diario_slice: slice, num_linha: int):
    texto = '\n'.join(texto_diario_slice[num_linha:num_linha+10])
    match = re.findall(re_nomes_municipios, texto, re.MULTILINE)
    if len(match) > 0:
        return match[0].strip().replace('\n', '')
    return None
