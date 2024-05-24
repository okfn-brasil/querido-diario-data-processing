# from .interfaces import DatabaseInterface, StorageInterface
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
    for g in database.select("SELECT * FROM gazettes LIMIT 10;"):   # Precisa do ponto e vírgula no final
        print(g)    # É a posição 7 que conetm o caminho do arquivo dentro do S3
        print("\n")

    # Deleta um arquivo do S3, funciona
    storage.delete_file("2933604/2024")

    # Faz a copia de um arquivo de um lugar para outro, funciona mas levanta uma exceção
    storage.copy_file("2933604/2024-03-01/efbc33795f0b37296a01bad5187eb8a326dbe66b.txt", "2933604/2024/")


    pass    

if __name__ == "__main__":
    organize_files_by_city_and_date()