import logging
import os
import traceback
import xml.etree.cElementTree as ET
from datetime import datetime
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory, mkstemp
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile

from botocore.exceptions import ClientError

from database import DatabaseInterface
from storage import StorageInterface

from .utils import br_timezone, get_territory_slug, hash_file

logger = logging.getLogger(__name__)


def create_aggregates(database: DatabaseInterface, storage: StorageInterface):
    """
    Create xml for all territories available in database
    """
    logger.info("Agregando os arquivos TXT para XML de territórios e estados...")

    results_query_states = database.select(
        """
        SELECT 
            t.state_code AS code, 
            g_years.year,
            json_agg(json_build_object('id', t.id, 'name', t.name)) 
        FROM 
            territories t 
            INNER JOIN (
                SELECT
                    date_part('Year', g.date) AS year,
                    g.territory_id
                FROM
                    gazettes g
                GROUP BY
                    year,
                    g.territory_id
            ) as g_years
            ON
                g_years.territory_id=t.id
        WHERE
            t.id NOT LIKE '%00000'
        GROUP BY 
            code,
            g_years.year
        """
    )

    for state_code, year, territories_list in results_query_states:
        create_aggregates_for_territories_and_state(
            state_code, int(year), territories_list, database, storage
        )


def create_aggregates_for_territories_and_state(
    state_code: str,
    year: int,
    territories_list: list,
    database: DatabaseInterface,
    storage: StorageInterface,
):
    """
    Create a .xml files for each year of gazettes for a territory
    """
    state_xmls = []
    state_needs_update = True
    state_needs_update = False

    with TemporaryDirectory() as tmpdir:
        for territory in territories_list:
            gazettes_in_territory_year = database.select(
                f"""
                SELECT
                    to_jsonb(g)
                FROM 
                    gazettes g 
                WHERE
                    g.territory_id='{territory['id']}'
                    and date_part('Year', g.date)={year}
                    and g.processed=true
                ORDER BY
                   g.date DESC
                """
            )

            xml_info = generate_xml_content(
                state_code,
                str(year),
                territory,
                gazettes_in_territory_year,
                storage,
                tmpdir,
            )

            state_xmls.append(xml_info)

            need_update_territory_zip = zip_needs_upsert(xml_info, database)

            if need_update_territory_zip:
                state_needs_update = True
                try_create_zip_for_territory(xml_info, database, storage)

        if state_needs_update:
            try_create_zip_for_state(state_xmls, state_code, year, database, storage)


def generate_xml_content(
    state_code: str,
    year: str,
    territory: dict,
    gazettes_in_territory_year: Iterable,
    storage: StorageInterface,
    save_dir: str,
):
    """
    Generates xml file with gazzetes content
    """

    logger.info(
        f"Gerando XML para cidade {territory['name']}-{state_code} no ano {year}"
    )

    tree = ET.ElementTree(ET.Element("root"))
    populate_xml_tree(
        tree, state_code, year, territory, gazettes_in_territory_year, storage
    )

    ET.indent(tree, space="  ")

    xml_file_descriptor, xml_file_path = mkstemp(dir=save_dir)
    with os.fdopen(xml_file_descriptor, "w") as xml_file:
        tree.write(xml_file, encoding="unicode")

    xml_info = {
        "xml_file_path": xml_file_path,
        "hash_info": hash_file(xml_file_path),
        "territory_id": territory["id"],
        "territory_name": territory["name"],
        "state_code": state_code,
        "year": year,
    }
    return xml_info


def populate_xml_tree(
    tree: ET.ElementTree,
    state_code: str,
    year: str,
    territory: dict,
    gazettes_in_territory_year: Iterable,
    storage: StorageInterface,
):
    root = tree.getroot()
    meta_info_tag = ET.SubElement(root, "meta")
    ET.SubElement(meta_info_tag, "uf").text = state_code
    ET.SubElement(meta_info_tag, "ano_publicacao").text = str(year)
    ET.SubElement(meta_info_tag, "municipio").text = territory["name"]
    ET.SubElement(meta_info_tag, "municipio_codigo_ibge").text = territory["id"]
    all_gazettes_tag = ET.SubElement(root, "diarios")

    for gazette_ in gazettes_in_territory_year:
        gazette = gazette_[0]

        gazette_tag = ET.SubElement(all_gazettes_tag, "diario")
        meta_gazette = ET.SubElement(gazette_tag, "meta_diario")
        ET.SubElement(meta_gazette, "url_arquivo_original").text = gazette["file_url"]
        ET.SubElement(meta_gazette, "poder").text = gazette["power"]
        ET.SubElement(meta_gazette, "edicao_extra").text = (
            "Sim" if gazette["is_extra_edition"] else "Não"
        )
        ET.SubElement(meta_gazette, "numero_edicao").text = (
            str(gazette["edition_number"])
            if str(gazette["edition_number"]) is not None
            else "Não há"
        )
        ET.SubElement(meta_gazette, "data_publicacao").text = datetime.strptime(
            gazette["date"], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

        path_arq_bucket = Path(gazette["file_path"]).with_suffix(".txt")
        with BytesIO() as file_gazette_txt:
            try:
                storage.get_file(path_arq_bucket, file_gazette_txt)
            except ClientError as e:
                logger.warning(
                    f"Erro na obtenção do conteúdo de texto do diário {path_arq_bucket}: {e}"
                )
                continue

            ET.SubElement(
                gazette_tag, "conteudo"
            ).text = file_gazette_txt.getvalue().decode("utf-8")


def try_create_zip_for_territory(
    xml_info: dict,
    database: DatabaseInterface,
    storage: StorageInterface,
):
    """
    Try calling create_zip_for_territory or give exception
    """
    try:
        create_zip_for_territory(xml_info, database, storage)
    except Exception as e:
        logger.error(
            f"Erro ao tentar criar ZIP de {xml_info['year']} para {xml_info['territory_name']} - {xml_info['state_code']}"
        )
        raise e


def create_zip_for_territory(
    xml_info: dict,
    database: DatabaseInterface,
    storage: StorageInterface,
):
    """
    Creating .zip files for the year's territories
    """

    logger.info(
        f"Gerando ZIP do municipio {xml_info['territory_name']}-{xml_info['territory_id']} no ano {xml_info['year']}"
    )

    with NamedTemporaryFile() as zip_tempfile:
        with ZipFile(zip_tempfile, "w", ZIP_DEFLATED) as zip_file:
            file_name = generate_xml_name(xml_info)
            write_file_to_zip(xml_info["xml_file_path"], file_name, zip_file)

        zip_size = round(zip_tempfile.tell() / (1024 * 1024), 2)

        territory_slug = get_territory_slug(
            xml_info["territory_name"], xml_info["state_code"]
        )
        storage_path = f"aggregates/{xml_info['state_code']}/{territory_slug}_{xml_info['territory_id']}_{xml_info['year']}.zip"
        try:
            storage.upload_file_multipart(storage_path, zip_tempfile.name)
        except Exception:
            logger.error(
                f"Não foi possível fazer o upload do zip do município {xml_info['territory_id']}:\n{traceback.format_exc()}"
            )

    dict_query_info = {
        "state_code": xml_info["state_code"],
        "territory_id": xml_info["territory_id"],
        "file_path": storage_path,
        "year": xml_info["year"],
        "hash_info": xml_info["hash_info"],
        "file_size_mb": zip_size,
        "last_updated": datetime.now(br_timezone),
    }

    database.insert(
        "INSERT INTO aggregates \
                (territory_id, state_code, year, file_path, \
                file_size_mb, hash_info, last_updated) \
                VALUES (%(territory_id)s, %(state_code)s, \
                %(year)s, %(file_path)s, %(file_size_mb)s, \
                %(hash_info)s, %(last_updated)s) \
                ON CONFLICT(file_path) \
                DO UPDATE \
                SET state_code=EXCLUDED.state_code, last_updated=EXCLUDED.last_updated, \
                hash_info=EXCLUDED.hash_info, file_size_mb=EXCLUDED.file_size_mb;",
        dict_query_info,
    )


def try_create_zip_for_state(
    state_xmls: list,
    state_code: str,
    year: int,
    database: DatabaseInterface,
    storage: StorageInterface,
):
    """
    Try calling create_zip_for_state or give exception
    """
    try:
        create_zip_for_state(state_xmls, state_code, year, database, storage)
    except Exception as e:
        logger.error(f"Erro ao tentar criar ZIP de {year} para {state_code}")
        raise e


def create_zip_for_state(
    state_xmls: list,
    state_code: str,
    year: int,
    database: DatabaseInterface,
    storage: StorageInterface,
):
    """
    Creating .zip files for the state with all its territories
    """

    logger.info(f"Gerando ZIP do estado {state_code} no ano {year}")

    with NamedTemporaryFile() as zip_tempfile:
        with ZipFile(zip_tempfile, "w", ZIP_DEFLATED) as zip_file:
            for xml_info in state_xmls:
                file_name = generate_xml_name(xml_info)
                write_file_to_zip(xml_info["xml_file_path"], file_name, zip_file)

        zip_size = round(zip_tempfile.tell() / (1024 * 1024), 2)
        hash_info = hash_file(zip_tempfile)

        zip_path = f"aggregates/{state_code}/{state_code}_{year}.zip"
        storage.upload_file_multipart(zip_path, zip_tempfile.name)

    dict_query_info = {
        "state_code": state_code,
        "territory_id": None,
        "file_path": zip_path,
        "year": year,
        "hash_info": hash_info,
        "file_size_mb": zip_size,
        "last_updated": datetime.now(br_timezone),
    }

    database.insert(
        "INSERT INTO aggregates \
                (territory_id, state_code, year, file_path, \
                file_size_mb, hash_info, last_updated) \
                VALUES (%(territory_id)s, %(state_code)s, \
                %(year)s, %(file_path)s, %(file_size_mb)s, \
                %(hash_info)s, %(last_updated)s) \
                ON CONFLICT(file_path) \
                DO UPDATE \
                SET state_code = EXCLUDED.state_code, last_updated=EXCLUDED.last_updated, \
                hash_info=EXCLUDED.hash_info, file_size_mb=EXCLUDED.file_size_mb;",
        dict_query_info,
    )


def zip_needs_upsert(xml_info: dict, database: DatabaseInterface):
    """
    Verifies if zip need an upsert to the database (update or insert)
    """

    identical_xml_in_database = list(
        database.select(
            f"""
        SELECT
            hash_info
        FROM
            aggregates
        WHERE
            hash_info='{xml_info["hash_info"]}'
            and territory_id='{xml_info["territory_id"]}'
            and year='{xml_info["year"]}'
        """
        )
    )
    return len(identical_xml_in_database) == 0


def generate_xml_name(xml_info):
    territory_slug = get_territory_slug(
        xml_info["territory_name"], xml_info["state_code"]
    )
    return f"{territory_slug}_{xml_info['territory_id']}_{xml_info['year']}.xml"


def write_file_to_zip(file_path, name_in_zip, zip_file):
    with open(file_path, "rb") as open_xml_file, zip_file.open(
        name_in_zip, "w"
    ) as xml_in_zip:
        chunk_size = 5 * 1024 * 1024
        while True:
            chunk = open_xml_file.read(chunk_size)
            if not chunk:
                break
            xml_in_zip.write(chunk)
