# from .interfaces import DatabaseInterface, StorageInterface
from io import BytesIO
from database import create_database_interface
from storage import create_storage_interface

def organize_files_by_city_and_date():
    """
    Organize the files in the S3 bucket by city and date
    """
    database = create_database_interface()
    storage = create_storage_interface()

    print("TESTE - Script que agrega os arquivos .txt para .xml")

    # Imprime cada resultado da query do banco de dados
    for g in database.select("SELECT * FROM gazettes WHERE date BETWEEN '2024-04-20' AND '2024-05-01' LIMIT 10;"):   # Precisa do ponto e vírgula no final
        arquivo = BytesIO()
        path_arq_bucket = str(g[7]).replace(".pdf",".txt")
        
        storage.get_file(path_arq_bucket, arquivo)  # É a posição 7 que conetm o caminho do arquivo dentro do S3

        # print(arquivo.getvalue().decode('utf-8'))
   
        print("\n---------------------------------------------\n")

        # Faz a copia do arquivo txt para pasta no S3
        path_bucket_separado = path_arq_bucket.split("/")
        path_bucket_separado[1] = str(g[2].year)

        path_novo_bucket = "/".join(path_bucket_separado)
        print(path_novo_bucket)
        storage.copy_file(path_arq_bucket, path_novo_bucket)


    # Deleta um arquivo do S3, funciona
    # storage.delete_file("1718808/2024/460131dd7666d09566983792e85ef8f23bbe024c.txt")

    # # Faz a copia de um arquivo de um lugar para outro, funciona mas levanta uma exceção
    # storage.copy_file("1718808/2024-04-01/460131dd7666d09566983792e85ef8f23bbe024c.txt", "1718808/2024/460131dd7666d09566983792e85ef8f23bbe024c.txt")



    # print(arquivo.getvalue().decode('utf-8'))

    pass    

if __name__ == "__main__":
    organize_files_by_city_and_date()