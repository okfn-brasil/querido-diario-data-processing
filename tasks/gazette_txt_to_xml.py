# from .interfaces import DatabaseInterface, StorageInterface
from io import BytesIO
from database import create_database_interface
from storage import create_storage_interface
import xml.etree.cElementTree as ET
import hashlib, traceback, os
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED


def hash_xml(content : str):
    """
    Receives a text content of a XML file and returns its SHA-256 hash
    """

    seed_hash = bytes(os.environ['SEED_HASH'].encode('utf-8'))

    # Escolha o algoritmo de hash (no caso, SHA-256)
    algorithm = hashlib.sha256
    result_hash = hashlib.pbkdf2_hmac(algorithm().name, content.encode('utf-8'), seed_hash, 100000)

    # Converta o resultado para uma representação legível (hexadecimal)
    hash_hex = result_hash.hex()

    return hash_hex

def create_xml_for_territory_and_year(territory_info:tuple, database, storage):
    """
    Create a .xml files for each year of gazettes for a territory  
    """

    actual_year = datetime.now().year
    base_year = 1960

    for year in range(base_year, actual_year+1):
        query_content = list(database.select(f"SELECT * FROM gazettes\
                                        WHERE territory_id='{territory_info[0]}' AND\
                                        date BETWEEN '{year}-01-01' AND '{year}-12-31'\
                                        ORDER BY date ASC;"))

        if len(query_content) > 0:
            print(f"Gerando XML para cidade {territory_info[1]}-{territory_info[2]} no ano {year}")
            root = ET.Element("root")
            meta_info_tag = ET.SubElement(root, "meta")
            ET.SubElement(meta_info_tag, "localidade", name="municipio").text = territory_info[1]
            ET.SubElement(meta_info_tag, "localidade", name="estado").text = territory_info[2]
            ET.SubElement(meta_info_tag, "ano").text = str(year)
            all_gazettes_tag = ET.SubElement(root, "diarios")

            for gazette in query_content:
                try:
                    file_gazette_txt = BytesIO()
                    path_arq_bucket = str(gazette[7]).replace(".pdf",".txt") # É a posição 7 que contem o caminho do arquivo dentro do S3
                    
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
                    print(f"Erro na obtenção do conteúdo de texto do diário de {territory_info[1]}-{territory_info[2]}-{gazette[2]}")
                    continue
            
            tree = ET.ElementTree(root)

            xml_file = BytesIO()

            tree.write(xml_file, encoding='utf8', xml_declaration=True)
            xml_file.seek(0) # Volta o cursor de leitura do arquivo para o começo dele

            hx = hash_xml(xml_file.getvalue().decode('utf-8'))
            zip_path = f"aggregates/{territory_info[0]}/{year}.zip"

            query_existing_aggregate = list(database.select(f"SELECT hash_info FROM aggregates \
                                                        WHERE url_zip='{zip_path}';"))

            need_update = False

            if query_existing_aggregate:
                need_update = hx != query_existing_aggregate[0][0]

                if not need_update:
                    xml_file.close()
                    continue

            try:
                zip_buffer = BytesIO()

                with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(f"{territory_info[1]}-{territory_info[2]}-{year}.xml", xml_file.getvalue())

                zip_size = round(zip_buffer.getbuffer().nbytes / (1024 * 1024), 2)

                zip_buffer.seek(0)  # Volta o cursor de leitura do zip para o começo dele

                storage.upload_zip(zip_path, zip_buffer)

                dict_query_info = {
                    "territory_id" : territory_info[0],
                    "url_zip": zip_path,
                    "year": year,
                    "hash_info": hx,
                    "file_size": zip_size,
                }

                if need_update:
                    database.insert("UPDATE aggregates SET \
                        territory_id=%(territory_id)s, last_updated=NOW(), \
                        hash_info=%(hash_info)s, file_size=%(file_size)s \
                        WHERE url_zip=%(url_zip)s;", dict_query_info)
                else:
                    database.insert("INSERT INTO aggregates \
                        (territory_id, url_zip, year, last_updated, hash_info, file_size)\
                        VALUES (%(territory_id)s, %(url_zip)s, %(year)s, NOW(), \
                        %(hash_info)s, %(file_size)s);", dict_query_info)

                zip_buffer.close()
                xml_file.close()

            except Exception as e:
                print(f"Erro ao criar e enviar o arquivo zip: {e}")
                continue
            
        else:
            print(f"Nada encontrado para cidade {territory_info[1]}-{territory_info[2]} no ano {year}")

def create_xml_territories():
    """
    Create xml for all territories available in database
    """

    database = create_database_interface()
    storage = create_storage_interface()

    print("Script que agrega os arquivos .txt para .xml")

    results_query = database.select("SELECT * FROM territories;")
    # results_query = database.select("SELECT * FROM territories WHERE id='1718808';")

    for t in results_query:
        try:
            create_xml_for_territory_and_year(t, database, storage)
        except:
            print(traceback.format_exc())
            continue


if __name__ == "__main__":
    create_xml_territories()