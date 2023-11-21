from associations import extrair_diarios_municipais


def extrarir_diarios(pdf_text, gazette, territories):

    diarios = extrair_diarios_municipais(pdf_text, gazette, territories)
    return diarios
