import re
import logging

from typing import Any, Dict, List
from segmentation.base import AssociationSegmenter, GazetteSegment
from tasks.utils import batched, get_checksum, get_territory_data, get_territory_slug


class ALAssociacaoMunicipiosSegmenter(AssociationSegmenter):
    RE_NOMES_MUNICIPIOS = re.compile(
        r"""
        (ESTADO\sDE\sALAGOAS(?:|\s)\n{1,2}PREFEITURA\sMUNICIPAL\sDE\s)  # Marcador de início do cabeçalho de publicação do município
        ((?!EDUCAÇÃO).*?\n{0,2}(?!VAMOS).*?$)                           # Nome do município (pode estar presente em até duas linhas). Exceções Notáveis: VAMOS, Poço das Trincheiras, 06/01/2022, ato CCB3A6AB; EDUCAÇÃO, Dois Riachos, 07/12/2023, ato ABCCE576
        (\n\s(?:\s|SECRETARIA|Secretaria))                              # Marcador de fim do cabeçalho (pula mais de duas linhas). Exceções Notáveis: SECRETARIA, Coité do Nóia, 02/10/2018, ato 12F7DE15; Secretaria, Qubrângulo, 18/07/2023, atos 27FB2D83 a 1FAF9421
        """,
        re.MULTILINE | re.VERBOSE,
    )

    def get_gazette_segments(self, gazette: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts with the gazettes metadata
        """
        territory_to_text_map = self.split_text_by_territory(gazette["source_text"])
        gazette_segments = [
            self.build_segment(territory_slug, segment_text, gazette).__dict__
            for territory_slug, segment_text in territory_to_text_map.items()
        ]
        return gazette_segments

    def split_text_by_territory(self, text: str) -> Dict[str, str]:
        """
        Segment a association text by territory
        and returns a dict with the territory name and the text segment
        """
        ama_header = text.lstrip().split("\n", maxsplit=1)[0].rstrip()
        # clean headers
        clean_text = "\n".join(re.split(re.escape(ama_header), text))
        # clean final lines
        clean_text = "\n".join(
            re.split(r"(Código Ide ?ntificador:\s*\w+)", clean_text)[:-1]
        )

        raw_segments = re.split(self.RE_NOMES_MUNICIPIOS, clean_text)[1:]

        territory_to_text_map = {}
        for pattern_batch in batched(raw_segments, 4):
            territory_name = pattern_batch[1]
            clean_territory_name = self._normalize_territory_name(territory_name)
            territory_slug = get_territory_slug(clean_territory_name, "AL")
            previous_text_or_header = territory_to_text_map.setdefault(
                territory_slug, f"{ama_header}\n"
            )
            raw_batch_text = "".join(pattern_batch)
            new_territory_text = f"{previous_text_or_header}\n{raw_batch_text}"
            territory_to_text_map[territory_slug] = new_territory_text

        return territory_to_text_map

    def build_segment(
        self, territory_slug: str, segment_text: str, gazette: Dict
    ) -> GazetteSegment:
        logging.debug(
            f"Creating segment for territory \"{territory_slug}\" from {gazette['file_path']} file."
        )
        territory_data = get_territory_data(territory_slug, self.territories)

        return GazetteSegment(**{
            **gazette,
            # segment specific values
            "processed": True,
            "file_checksum": get_checksum(segment_text),
            "source_text": segment_text.strip(),
            "territory_name": territory_data["territory_name"],
            "territory_id": territory_data["id"],
        })

    def _normalize_territory_name(self, territory_name: str) -> str:
        clean_name = territory_name.strip().replace("\n", "")
        # Alguns nomes de municípios possuem um /AL no final, exemplo: Viçosa no diário 2022-01-17, ato 8496EC0A. Para evitar erros como "vicosa-/al-secretaria-municipal...", a linha seguir remove isso.
        clean_name = re.sub(
            "\s*(\/AL.*|GABINETE DO PREFEITO.*|PODER.*|http.*|PORTARIA.*|Extrato.*|ATA DE.*|SECRETARIA.*|Fundo.*|SETOR.*|ERRATA.*|- AL.*|GABINETE.*|EXTRATO.*|SÚMULA.*|RATIFICAÇÃO.*)",
            "",
            clean_name,
        )
        name_to_fixed = {
            "MAJOR IZIDORO": "MAJOR ISIDORO",
        }
        return name_to_fixed.get(clean_name, clean_name)
