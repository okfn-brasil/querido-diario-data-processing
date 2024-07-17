from io import BytesIO
from database import create_database_interface
from storage import create_storage_interface
import xml.etree.cElementTree as ET
import traceback
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
from utils.hash import hash_xml, hash_zip
from xml.dom import minidom


need_update_zip_state = False

def create_aggregates_table(database):
    database._commit_changes(
        """
        CREATE TABLE IF NOT EXISTS aggregates (
            id SERIAL PRIMARY KEY ,
            territory_id VARCHAR,
            state_code VARCHAR NOT NULL,
            url_zip VARCHAR(255),
            year INTEGER,
            last_updated TIMESTAMP,
            hash_info VARCHAR(64),
            file_size REAL
        ); """)

def xml_content_generate(gazzetes_query_content:list, root, territory_id, storage):
    all_gazettes_tag = ET.SubElement(root, "diarios")

    for gazette in gazzetes_query_content:
        try:
            file_gazette_txt = BytesIO()
            path_arq_bucket = str(gazette[7])

            if path_arq_bucket.endswith(".pdf"):
                path_arq_bucket = path_arq_bucket.replace(".pdf", ".txt")
            else:
                path_arq_bucket = path_arq_bucket + ".txt"
            
            storage.get_file(path_arq_bucket, file_gazette_txt)

            gazette_tag = ET.SubElement(all_gazettes_tag, "gazette")
            meta_gazette = ET.SubElement(gazette_tag, "meta-gazette")
            ET.SubElement(meta_gazette, "url_pdf").text = gazette[8]
            ET.SubElement(meta_gazette, "poder").text = gazette[5]
            ET.SubElement(meta_gazette, "edicao_extra").text = 'Sim' if gazette[4] else 'Não'
            ET.SubElement(meta_gazette, "numero_edicao").text = str(gazette[3]) if str(gazette[3]) is not None else "Não há"
            ET.SubElement(meta_gazette, "data_diario").text = datetime.strftime(gazette[2], "%d/%m")
            ET.SubElement(gazette_tag, "conteudo").text = file_gazette_txt.getvalue().decode('utf-8')

            file_gazette_txt.close()
        except:
            print(f"Erro na obtenção do conteúdo de texto do diário do territorio {territory_id}")
            continue

def create_zip_for_state(xml_arr:list, year, state_code, database, storage):
    """
    Creating .zip files for the state with all its territories
    """

    print(f"Gerando ZIP do estado {state_code} no ano {year}")
    
    zip_path = f"aggregates/{state_code}/{state_code}-{year}.zip"

    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
        for xml_file in xml_arr:
            zip_file.writestr(f"{xml_file['territory_id']}-{xml_file['year']}.xml", xml_file['xml'].getvalue())
        
    zip_size = round(zip_buffer.getbuffer().nbytes / (1024 * 1024), 2)
    zip_buffer.seek(0)
    zip_buffer_copy = BytesIO(zip_buffer.getvalue())
    zip_buffer_copy.seek(0)
    storage.upload_zip(zip_path, zip_buffer)

    hx = hash_zip(zip_buffer_copy.read())

    dict_query_info = {
        "state_code" : state_code,
        "territory_id" : None,
        "url_zip": zip_path,
        "year": year,
        "hash_info": hx,
        "file_size": zip_size,
    }

    query_existing_aggregate = list(database.select(f"SELECT hash_info FROM aggregates \
                                                            WHERE url_zip='{zip_path}';"))

    if query_existing_aggregate and hx != query_existing_aggregate[0][0]:
        database.insert("UPDATE aggregates SET \
            state_code=%(state_code)s, last_updated=NOW(), \
            hash_info=%(hash_info)s, file_size=%(file_size)s \
            WHERE url_zip=%(url_zip)s;", dict_query_info)
    else:
        database.insert("INSERT INTO aggregates \
                (territory_id, state_code, url_zip, year, last_updated, hash_info, file_size)\
                VALUES (%(territory_id)s, %(state_code)s, %(url_zip)s, %(year)s, NOW(), \
                %(hash_info)s, %(file_size)s);", dict_query_info)

    zip_buffer.close()

def create_zip_for_territory(xml_arr:list, database, storage):
    """
    Creating .zip files for the year's territories 
    """

    global need_update_zip_state
    need_update_zip_state = False

    for xml_file in xml_arr:
        try:
            hx = hash_xml(xml_file['xml'].getvalue().decode('utf-8'))
            zip_path = f"aggregates/{xml_file['state_code']}/{xml_file['territory_id']}-{xml_file['year']}.zip"
            
            query_existing_aggregate = list(database.select(f"SELECT hash_info FROM aggregates \
                                                            WHERE url_zip='{zip_path}';"))
            
            need_update = False

            if query_existing_aggregate:
                need_update = hx != query_existing_aggregate[0][0]
                if not need_update:
                    continue

            need_update_zip_state = True

            zip_buffer = BytesIO()

            with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
                zip_file.writestr(f"{xml_file['territory_id']}-{xml_file['year']}.xml", xml_file['xml'].getvalue())
            
            zip_size = round(zip_buffer.tell() / (1024 * 1024), 2)
            zip_buffer.seek(0)

            storage.upload_zip(zip_path, zip_buffer)

            dict_query_info = {
                "state_code" : xml_file['state_code'],
                "territory_id" : xml_file['territory_id'],
                "url_zip": zip_path,
                "year": xml_file['year'],
                "hash_info": hx,
                "file_size": zip_size,
            }

            if need_update:
                database.insert("UPDATE aggregates SET \
                    territory_id=%(territory_id)s, state_code=%(state_code)s, last_updated=NOW(), \
                    hash_info=%(hash_info)s, file_size=%(file_size)s \
                    WHERE url_zip=%(url_zip)s;", dict_query_info)
            else:
                database.insert("INSERT INTO aggregates \
                    (territory_id, state_code, url_zip, year, last_updated, hash_info, file_size)\
                    VALUES (%(territory_id)s, %(state_code)s, %(url_zip)s, %(year)s, NOW(), \
                    %(hash_info)s, %(file_size)s);", dict_query_info)

            zip_buffer.close()
        except Exception as e:
            print(traceback.format_exc())

def create_aggregates_for_territories_and_states(territories_list:list, state, database, storage):
    """
    Create a .xml files for each year of gazettes for a territory  
    """
    actual_year = datetime.now().year
    base_year = 1960

    for year in range(base_year, actual_year+1):
        xml_files_arr = []

        for territories in territories_list:
            root = ET.Element("root")
            xml_file = BytesIO()

            gazzetes_query_content = list(database.select(f"SELECT * FROM gazettes\
                                            WHERE territory_id='{territories[0]}' AND\
                                            date BETWEEN '{year}-01-01' AND '{year}-12-31'\
                                            ORDER BY date ASC;"))

            if gazzetes_query_content:
                print(f"Gerando XML para cidade {territories[1]}-{territories[2]} no ano {year}")

                meta_info_tag = ET.SubElement(root, "meta")
                ET.SubElement(meta_info_tag, "localidade", name="estado").text = territories[2]
                ET.SubElement(meta_info_tag, "ano").text = str(year)
                ET.SubElement(meta_info_tag, "localidade", name="municipio").text = territories[1]
                ET.SubElement(meta_info_tag, "codigo_ibge", name="codigo_ibge").text = territories[0]

                xml_content_generate(gazzetes_query_content, root, territories[0], storage)

                # Format XML file
                xml_str = ET.tostring(root, encoding='unicode')
                format_xml = minidom.parseString(xml_str).toprettyxml(indent=" ")
                xml_bytes = format_xml.encode('utf-8')

                xml_file.write(xml_bytes)
                xml_file.seek(0)

                meta_xml={
                    "xml":xml_file,
                    "territory_id":territories[0],
                    "state_code":territories[2],
                    "year":year
                }

                xml_files_arr.append(meta_xml)
            else:
                # print(f"Nada encontrado para cidade {territories[1]}-{territories[2]} no ano {year}")
                pass
        
        create_zip_for_territory(xml_files_arr, database, storage)

        if need_update_zip_state:
            create_zip_for_state(xml_files_arr, year, state, database, storage)
        
        xml_file.close()

def create_aggregates():
    """
    Create xml for all territories available in database
    """

    database = create_database_interface()
    storage = create_storage_interface()

    print("========== Script que agrega os arquivos .txt para .xml de territórios e estados ==========")

    results_query_states = database.select("SELECT DISTINCT state_code FROM territories ORDER BY state_code ASC;")

    for res in results_query_states:
        
        results_query_territories = database.select(f"SELECT * FROM territories WHERE state_code='{res[0]}';")

        create_aggregates_table(database)

        try:
            create_aggregates_for_territories_and_states(list(results_query_territories), res[0], database, storage)
        except:
            print(traceback.format_exc())
            continue


if __name__ == "__main__":
    create_aggregates()