
import unicodedata


def get_territorie_info(state: str, name: str, territories: list):

    state = state.strip()
    name = limpar_name(name)

    for territorie in territories:
        territorie_name = limpar_name(territorie["territory_name"])
        if territorie["state"].lower() == state.lower() and territorie_name == name:

            return territorie["id"], territorie["territory_name"], territorie["state_code"]


def limpar_name(name: str):

    processamento_2 = name.replace("'", "")
    processamento_2 = unicodedata.normalize("NFD", processamento_2)
    processamento_2 = processamento_2.encode("ascii", "ignore").decode("utf-8")
    processamento_2 = processamento_2.lower()

    processamento_2 = "major isidoro" if processamento_2 == "major izidoro" else processamento_2

    return processamento_2
