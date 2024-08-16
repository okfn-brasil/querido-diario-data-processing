import traceback
import xml.etree.cElementTree as ET
import logging
from datetime import datetime, timedelta
from io import BytesIO
from xml.dom import minidom
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path

from .utils import hash_content, zip_needs_upsert, get_territory_slug
from .interfaces import StorageInterface,DatabaseInterface

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
br_timezone = timedelta(hours=-3)


def create_aggregates(database:DatabaseInterface, storage:StorageInterface):
    """
    Create xml for all territories available in database
    """
    logger.info("Agregando os arquivos TXT para XML de territórios e estados...")

    results_query_states = list(database.select("""SELECT 
                                                        t.state_code AS code, 
                                                        json_agg(json_build_object('id',t.id, 'name',t.name)) 
                                                    FROM 
                                                        territories t 
                                                    WHERE
                                                        t.id in (SELECT DISTINCT 
                                                                    territory_id 
                                                                FROM 
                                                                    gazettes
                                                                WHERE
                                                                    territory_id NOT LIKE '%00000'
                                                                )
                                                       GROUP BY 
                                                        code
                                                    """
                                                    ))

    for state, territories_list in results_query_states:
        try:
            create_aggregates_for_territories_and_states(territories_list, state, database, storage)
        except Exception as e:
            logger.error(f"Erro ao tentar processar municípios de {state}: {e}\n{traceback.format_exc()}")
            
            continue
        

def create_aggregates_for_territories_and_states(territories_list:list, state:str, database:DatabaseInterface, storage:StorageInterface):
    """
    Create a .xml files for each year of gazettes for a territory  
    """
    
    xml_files_dict = {}
    arr_years_update = []

    for territory in territories_list:
        query_content_gazzetes_for_territory = list(database.select(f"""SELECT
                                                                        date_part('Year', g.date) AS year,
                                                                        json_agg(g.*)
                                                                    FROM 
                                                                        gazettes g 
                                                                    WHERE
                                                                        g.territory_id='{territory['id']}'
                                                                        and g.processed=true
                                                                    GROUP BY 
                                                                        year
                                                                    """
                                                                    ))

        for year, list_gazzetes_content in query_content_gazzetes_for_territory:
            year = str(int(year))

            meta_xml = xml_content_generate(state, year, territory, list_gazzetes_content, storage)

            xml_files_dict.setdefault(year, []).append(meta_xml)

            territory_slug = get_territory_slug(meta_xml['territory_name'], state)
            zip_path = f"aggregates/{meta_xml['state_code']}/{territory_slug}_{meta_xml['territory_id']}_{meta_xml['year']}.zip"
            hx = hash_content(meta_xml['xml'])

            logger.debug(f"Content hash for xml file of {zip_path}: {hx}")

            need_update_territory_zip = zip_needs_upsert(hx, zip_path, database)

            if need_update_territory_zip:
                if year not in arr_years_update:
                    arr_years_update.append(year)
                create_zip_for_territory(hx, zip_path, meta_xml, database, storage)

    if arr_years_update:
        create_zip_for_state(xml_files_dict, arr_years_update, state, database, storage)
        
        
def create_zip_for_state(xmls_years_dict:dict, arr_years_update:list, state_code, database:DatabaseInterface, storage:StorageInterface):
    """
    Creating .zip files for the state with all its territories
    """

    for year in arr_years_update:
        logger.info(f"Gerando ZIP do estado {state_code} no ano {year}")
        
        xmls = xmls_years_dict[year]
        
        zip_path = f"aggregates/{state_code}/{state_code}_{year}.zip"

        zip_buffer = BytesIO()

        with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
            for xml_file in xmls:
                territory_slug = get_territory_slug(xml_file['territory_name'], xml_file['state_code'])
                zip_file.writestr(f"{territory_slug}_{xml_file['territory_id']}_{xml_file['year']}.xml", xml_file['xml'])
            
        zip_size = round(zip_buffer.getbuffer().nbytes / (1024 * 1024), 2)
        zip_buffer.seek(0)
        zip_buffer_copy = BytesIO(zip_buffer.getvalue())
        zip_buffer_copy.seek(0)
        storage.upload_content(zip_path, zip_buffer)

        hx = hash_content(zip_buffer_copy.read())

        logger.debug(f"Content hash for {zip_path}: {hx}")

        dict_query_info = {
            "state_code" : state_code,
            "territory_id" : None,
            "file_path": zip_path,
            "year": year,
            "hash_info": hx,
            "file_size_mb": zip_size,
            "last_updated": datetime.utcnow() + br_timezone,
        }

        database.insert("INSERT INTO aggregates \
                    (territory_id, state_code, year, file_path, \
                    file_size_mb, hash_info, last_updated) \
                    VALUES (%(territory_id)s, %(state_code)s, \
                    %(year)s, %(file_path)s, %(file_size_mb)s, \
                    %(hash_info)s, %(last_updated)s) \
                    ON CONFLICT(file_path) \
                    DO UPDATE \
                    SET state_code = EXCLUDED.state_code, last_updated=EXCLUDED.last_updated, \
                    hash_info=EXCLUDED.hash_info, file_size_mb=EXCLUDED.file_size_mb;", dict_query_info)

        zip_buffer.close()


def create_zip_for_territory(hx:str, zip_path:str, xml_file:dict, database:DatabaseInterface, storage:StorageInterface):
    """
    Creating .zip files for the year's territories 
    """

    logger.info(f"Gerando ZIP do municipio {xml_file['territory_name']}-{xml_file['territory_id']} no ano {xml_file['year']}")

    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
        territory_slug = get_territory_slug(xml_file['territory_name'], xml_file['state_code'])
        zip_file.writestr(f"{territory_slug}_{xml_file['territory_id']}_{xml_file['year']}.xml", xml_file['xml'])
    
    zip_size = round(zip_buffer.tell() / (1024 * 1024), 2)
    zip_buffer.seek(0)

    try:
        storage.upload_content(zip_path, zip_buffer)
    except ClientError as e:
        logger.error(f"Não foi possível fazer o upload do zip do município {xml_file['territory_id']}:\n{traceback.format_exc()}")
        
        zip_buffer.close()

    dict_query_info = {
        "state_code" : xml_file['state_code'],
        "territory_id" : xml_file['territory_id'],
        "file_path": zip_path,
        "year": xml_file['year'],
        "hash_info": hx,
        "file_size_mb": zip_size,
        "last_updated": datetime.utcnow() + br_timezone,
    }

    database.insert("INSERT INTO aggregates \
                (territory_id, state_code, year, file_path, \
                file_size_mb, hash_info, last_updated) \
                VALUES (%(territory_id)s, %(state_code)s, \
                %(year)s, %(file_path)s, %(file_size_mb)s, \
                %(hash_info)s, %(last_updated)s) \
                ON CONFLICT(file_path) \
                DO UPDATE \
                SET state_code=EXCLUDED.state_code, last_updated=EXCLUDED.last_updated, \
                hash_info=EXCLUDED.hash_info, file_size_mb=EXCLUDED.file_size_mb;", dict_query_info)

    zip_buffer.close()


def xml_content_generate(state:str, year:str, territory:dict, list_gazzetes_content:list, storage:StorageInterface):
    """
    Generates xml file with gazzetes content  
    """
    
    root = ET.Element("root")
    xml_file = BytesIO()

    logger.info(f"Gerando XML para cidade {territory['name']}-{state} no ano {year}")
    
    meta_info_tag = ET.SubElement(root, "meta")
    ET.SubElement(meta_info_tag, "uf").text = state
    ET.SubElement(meta_info_tag, "ano_publicacao").text = str(year)
    ET.SubElement(meta_info_tag, "municipio").text = territory['name']
    ET.SubElement(meta_info_tag, "municipio_codigo_ibge").text = territory['id']
    all_gazettes_tag = ET.SubElement(root, "diarios")

    for gazette in list_gazzetes_content:
        file_gazette_txt = BytesIO()
        path_arq_bucket = Path(gazette['file_path']).with_suffix(".txt")
        
        try:
            storage.get_file(path_arq_bucket, file_gazette_txt)
        except ClientError as e:
            logger.warning(f"Erro na obtenção do conteúdo de texto do diário do territorio {path_arq_bucket}: {e}")
            file_gazette_txt.close()

            continue

        gazette_tag = ET.SubElement(all_gazettes_tag, "diario")
        meta_gazette = ET.SubElement(gazette_tag, "meta_diario")
        ET.SubElement(meta_gazette, "url_arquivo_original").text = gazette['file_url']
        ET.SubElement(meta_gazette, "poder").text = gazette['power']
        ET.SubElement(meta_gazette, "edicao_extra").text = 'Sim' if gazette['is_extra_edition'] else 'Não'
        ET.SubElement(meta_gazette, "numero_edicao").text = str(gazette['edition_number']) if str(gazette['edition_number']) is not None else "Não há"
        ET.SubElement(meta_gazette, "data_publicacao").text = datetime.strftime((datetime.strptime(gazette['date'], "%Y-%m-%d").date()), "%d/%m")
        ET.SubElement(gazette_tag, "conteudo").text = file_gazette_txt.getvalue().decode('utf-8')

        file_gazette_txt.close()
    
    # Format XML file
    xml_str = ET.tostring(root, encoding='unicode')
    format_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    xml_bytes = format_xml.encode('utf-8')

    xml_file.write(xml_bytes)
    xml_file.seek(0)

    data = {
        "xml":xml_file.getvalue(),
        "territory_id":territory['id'],
        "territory_name":territory['name'],
        "state_code":state,
        "year":year,
    }

    xml_file.close()

    return data