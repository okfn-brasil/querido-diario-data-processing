import re

from typing import Any
from segmentation.base import AssociationSegmenter, GazetteSegment
from tasks.utils import get_checksum

class ALAssociacaoMunicipiosSegmenter(AssociationSegmenter):
    def __init__(self, association_gazzete: dict[str, Any]):
        super().__init__(association_gazzete)
        # No final do regex, existe uma estrutura condicional que verifica se o próximo match é um \s ou SECRETARIA. Isso foi feito para resolver um problema no diário de 2018-10-02, em que o município de Coité do Nóia não foi percebido pelo código. Para resolver isso, utilizamos a próxima palavra (SECRETARIA) para tratar esse caso.
        # Exceções Notáveis
        # String: VAMOS, município Poço das Trincheiras, 06/01/2022, ato CCB3A6AB
        self.RE_NOMES_MUNICIPIOS = (
            r"ESTADO DE ALAGOAS(?:| )\n{1,2}PREFEITURA MUNICIPAL DE (.*\n{0,2}(?!VAMOS).*$)\n\s(?:\s|SECRETARIA)"
        )
        self.association_source_text = self.association_gazette["source_text"]

    def get_gazette_segments(self) -> list[dict[str, Any]]:
        """
        Returns a list of dicts with the gazettes metadata
        """
        territory_to_text_split = self.split_text_by_territory()
        gazette_segments = []
        for municipio, texto_diario in territory_to_text_split.items():
            segmento = self.build_segment(municipio, texto_diario)
            gazette_segments.append(segmento.__dict__)
        return gazette_segments

    def split_text_by_territory(self) -> dict[str, str]:
        """
        Segment a association text by territory
        and returns a dict with the territory name and the text segment
        """
        texto_diario_slice = self.association_source_text.lstrip().splitlines()

        # Processamento
        linhas_apagar = []  # slice de linhas a ser apagadas ao final.
        ama_header = texto_diario_slice[0]
        ama_header_count = 0
        codigo_count = 0
        codigo_total = self.association_source_text.count("Código Identificador")

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
        territory_to_text_split = {}
        nomes_municipios = re.findall(
            self.RE_NOMES_MUNICIPIOS, self.association_source_text, re.MULTILINE)
        for municipio in nomes_municipios:
            nome_municipio_normalizado = self._normalize_territory_name(municipio)
            territory_to_text_split[nome_municipio_normalizado] = ama_header + '\n\n'

        num_linha = 0
        municipio_atual = None
        while num_linha < len(texto_diario_slice):
            linha = texto_diario_slice[num_linha].rstrip()

            if linha.startswith("ESTADO DE ALAGOAS"):
                nome = self._extract_territory_name(texto_diario_slice, num_linha)
                if nome is not None:
                    nome_normalizado = self._normalize_territory_name(nome)
                    municipio_atual = nome_normalizado

            # Só começa, quando algum muncípio for encontrado.
            if municipio_atual is None:
                num_linha += 1
                continue

            # Conteúdo faz parte de um muncípio
            territory_to_text_split[municipio_atual] += linha + '\n'
            num_linha += 1

        return territory_to_text_split

    def build_segment(self, territory, segment_text) -> GazetteSegment:
        file_checksum = get_checksum(segment_text)
        processed = True
        territory_name = territory
        source_text = segment_text.rstrip()
        
        # TODO: get territory data and replace the None values
        territory_id = None
        # file_raw_txt = f"/{territory_id}/{date}/{file_checksum}.txt"
        file_raw_txt = None
        # url = file_raw_txt
        url = None
        
        return GazetteSegment(
            # same association values
            created_at=self.association_gazette.get("created_at"),
            date=self.association_gazette.get("date"),
            edition_number=self.association_gazette.get("edition_number"),
            file_path=self.association_gazette.get("file_path"),
            file_url=self.association_gazette.get("file_url"),
            is_extra_edition=self.association_gazette.get("is_extra_edition"),
            power=self.association_gazette.get("power"),
            scraped_at=self.association_gazette.get("scraped_at"),
            state_code=self.association_gazette.get("state_code"),
            url=self.association_gazette.get("url"),

            # segment specific values
            file_checksum=file_checksum,
            processed=processed,
            territory_name=territory_name,
            source_text=source_text,
            territory_id=territory_id,
            file_raw_txt=file_raw_txt,
        )

    def _normalize_territory_name(self, municipio: str) -> str:
        municipio = municipio.rstrip().replace('\n', '')  # limpeza inicial
        # Alguns nomes de municípios possuem um /AL no final, exemplo: Viçosa no diário 2022-01-17, ato 8496EC0A. Para evitar erros como "vicosa-/al-secretaria-municipal...", a linha seguir remove isso. 
        municipio = re.sub("(\/AL.*|GABINETE DO PREFEITO.*|PODER.*|http.*|PORTARIA.*|Extrato.*|ATA DE.*|SECRETARIA.*|Fundo.*|SETOR.*|ERRATA.*|- AL.*|GABINETE.*)", "", municipio)
        return municipio

    def _extract_territory_name(self, texto_diario_slice: list[str], num_linha: int):
        texto = '\n'.join(texto_diario_slice[num_linha:num_linha+10])
        match = re.findall(self.RE_NOMES_MUNICIPIOS, texto, re.MULTILINE)
        if len(match) > 0:
            return match[0].strip().replace('\n', '')
        return None
