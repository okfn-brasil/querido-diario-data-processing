from importlib import import_module

AVAILABLE_TASKS = {
    "create_aggregates": "tasks.gazette_txt_to_xml",
    "create_gazettes_index": "tasks.create_index",
    "create_aggregates_table": "tasks.create_aggregates_table",
    "create_themed_excerpts_index": "tasks.create_index",
    "embedding_rerank_excerpts": "tasks.gazette_excerpts_embedding_reranking",
    "extract_text_from_gazettes": "tasks.gazette_text_extraction",
    "extract_themed_excerpts_from_gazettes": "tasks.gazette_themed_excerpts_extraction",
    "get_gazettes_to_be_processed": "tasks.list_gazettes_to_be_processed",
    "get_themes": "tasks.gazette_themes_listing",
    "get_territories": "tasks.list_territories",
    "tag_entities_in_excerpts": "tasks.gazette_excerpts_entities_tagging",
}


def run_task(task_name: str, *args, **kwargs):
    module = AVAILABLE_TASKS[task_name]
    mod = import_module(module)
    task = getattr(mod, task_name)
    return task(*args, **kwargs)
