import json
import re
import unicodedata
from datetime import date, datetime
from .utils import get_territorie_info
import hashlib
from io import BytesIO


class Municipio:

    def __init__(self, municipio):
        municipio = municipio.rstrip().replace('\n', '')  # limpeza inicial
        # Alguns nomes de municípios possuem um /AL no final, exemplo: Viçosa no diário 2022-01-17, ato 8496EC0A. Para evitar erros como "vicosa-/al-secretaria-municipal...", a linha seguir remove isso. 
        municipio = re.sub("(\/AL.*|GABINETE DO PREFEITO.*|PODER.*|http.*|PORTARIA.*|Extrato.*|ATA DE.*|SECRETARIA.*|Fundo.*|SETOR.*|ERRATA.*|- AL.*|GABINETE.*)", "", municipio)
        self.id = self._computa_id(municipio)
        self.nome = municipio

    def _computa_id(self, nome_municipio):
        ret = nome_municipio.strip().lower().replace(" ", "-")
        ret = unicodedata.normalize('NFKD', ret)
        ret = ret.encode('ASCII', 'ignore').decode("utf-8")
        return ret

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return json.dumps(self.__dict__, indent=2, default=str, ensure_ascii=False)


class Diario:

    _mapa_meses = {
        "Janeiro": 1,
        "Fevereiro": 2,
        "Março": 3,
        "Abril": 4,
        "Maio": 5,
        "Junho": 6,
        "Julho": 7,
        "Agosto": 8,
        "Setembro": 9,
        "Outubro": 10,
        "Novembro": 11,
        "Dezembro": 12,
    }

    def __init__(self, municipio: Municipio, cabecalho: str, texto: str, gazette: dict, territories: list):
        
       
        self.territory_id, self.territory_name, self.state_code = get_territorie_info(
            name=municipio.nome,
            state=cabecalho.split(",")[0],
            territories=territories)
        
        self.source_text = texto.rstrip()
        self.date = self._extrai_data_publicacao(cabecalho)
        self.edition_number = cabecalho.split("Nº")[1].strip()
        self.is_extra_edition = False
        self.power = "executive_legislative"
        self.file_url = gazette["file_url"]
        self.file_path = gazette["file_path"]
        self.file_checksum = self.md5sum(BytesIO(self.source_text.encode(encoding='UTF-8')))
        self.id = gazette["id"]
        self.scraped_at = datetime.utcnow()
        self.created_at = self.scraped_at
        self.file_raw_txt = f"/{self.territory_id}/{self.date}/{self.file_checksum}.txt"
        self.processed = True
        self.url = self.file_raw_txt

    def _extrai_data_publicacao(self, ama_header: str):
        match = re.findall(
            r".*(\d{2}) de (\w*) de (\d{4})", ama_header, re.MULTILINE)[0]
        mes = Diario._mapa_meses[match[1]]
        return date(year=int(match[2]), month=mes, day=int(match[0]))

    def md5sum(self, file):
        """Calculate the md5 checksum of a file-like object without reading its
        whole content in memory.
        from io import BytesIO
        md5sum(BytesIO(b'file content to hash'))
        '784406af91dd5a54fbb9c84c2236595a'
        """
        m = hashlib.md5()
        while True:
            d = file.read(8096)
            if not d:
                break
            m.update(d)
        return m.hexdigest()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return dict(self.__dict__)
