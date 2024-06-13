# from .interfaces import DatabaseInterface, StorageInterface
from io import BytesIO
from database import create_database_interface
from storage import create_storage_interface
import xml.etree.cElementTree as ET
import hashlib


def hash_text(text):
    """
    Receives a text and returns its SHA-256 hash of a text content
    """
    # Cria um objeto sha256
    hasher = hashlib.sha256()

    # Atualiza o objeto com o texto codificado em UTF-8
    hasher.update(text.encode('utf-8'))

    # Obtém o hash hexadecimal
    return hasher.hexdigest()

def txt_to_xml(path_xml, txt: str, meta_info: dict, storage):
    """
    Transform a .txt file into a .xml file and upload it to the storage bucket
    """
    # Cria uma tag (elemento) chamado 'root' e um subelemento deste chamado 'doc'
    root = ET.Element("root")
    meta_info_tag = ET.SubElement(root, "meta")

    # Cria um subelemento do 'doc' chamado 'field1' e 'field2' com atributos 'name' e um texto
    ET.SubElement(meta_info_tag, "data", name="dia").text = meta_info['dia']
    ET.SubElement(meta_info_tag, "data", name="mes").text = meta_info['mes']

    ET.SubElement(meta_info_tag, "localidade", name="municipio").text = "some vlaue2"
    ET.SubElement(meta_info_tag, "localidade", name="estado").text = "estado"
    ET.SubElement(meta_info_tag, "criado_em").text = "criado_em"

    gazettes_tag = ET.SubElement(root, "gazettes")
    
    ET.SubElement(gazettes_tag, "gazette").text = txt
    
    # Adiciona a uma árvore de elementos XML (ou seja, o elemento 'root' onde contém todo o documento)
    # e o adiciona a um arquivo binário que será enviado para o storage bucket em formato .xml
    tree = ET.ElementTree(root)

    file_xml = BytesIO()

    tree.write(file_xml, encoding='utf-8', xml_declaration=True)
    file_xml.seek(0) # Volta o cursor de leitura do arquivo para o começo dele

    content_file_xml = file_xml.getvalue().decode('utf-8')

    storage.upload_content(path_xml, content_file_xml)
    

def organize_files_by_city_and_date():
    """
    Organize the files in the S3 bucket by city and date
    """
    database = create_database_interface()
    storage = create_storage_interface()

    print("TESTE - Script que agrega os arquivos .txt para .xml")

    results_query = database.select("SELECT g.*, t.name, t.state_code FROM gazettes AS g\
                                    JOIN territories AS t ON g.territory_id = t.id;")

    # Imprime cada resultado da query do banco de dados
    for resultado in results_query:   # Precisa do ponto e vírgula no final
        try:
            arquivo = BytesIO()
            path_arq_bucket = str(resultado[7]).replace(".pdf",".txt") # É a posição 7 que contem o caminho do arquivo dentro do S3
            
            storage.get_file(path_arq_bucket, arquivo)  # Pega o conteúdo do objeto do arquivo do S3 e coloca no BytesIO

            dict_gazzete_info = {
                "dia": str(resultado[2].day),
                "mes": str(resultado[2].month),
                "ano": str(resultado[2].year),
                "municipio": resultado[-2],
                "estado": resultado[-1],
            }
            
            # print(arquivo.getvalue().decode('utf-8')) # Imprime o conteúdo do arquivo com codificação utf-8

            print("\n---------------------------------------------\n")

            # Faz a copia do arquivo txt para pasta no S3
            path_bucket_separado = path_arq_bucket.split("/")
            path_bucket_separado[1] = str(resultado[2].year)

            path_novo_bucket = "/".join(path_bucket_separado)
            print(path_novo_bucket)

            storage.copy_file(path_arq_bucket, path_novo_bucket)

            arquivo.close()
            
        except:
            continue

    path_xml = "/".join(path_novo_bucket.split("/")[:-1]) + f"/{dict_gazzete_info['municipio']}-{dict_gazzete_info['estado']}.xml"

    print(path_xml)

    txt_to_xml(path_xml, "teste", dict_gazzete_info, storage)


if __name__ == "__main__":
    organize_files_by_city_and_date()