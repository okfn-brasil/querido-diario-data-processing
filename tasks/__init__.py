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


# Compatibility functions for tests
def extract_text_pending_gazettes(
    database,
    storage,
    index,
    text_extractor,
    territories=None
):
    """Extract text from pending gazettes - compatibility wrapper"""
    from tasks.gazette_text_extraction import extract_text_from_gazettes
    
    pending_gazettes = database.get_pending_gazettes() if hasattr(database, 'get_pending_gazettes') else []
    territories = territories or []
    
    return extract_text_from_gazettes(
        pending_gazettes,
        territories,
        database,
        storage,
        index,
        text_extractor
    )


def upload_gazette_raw_text(
    storage,
    gazette_id,
    content,
    file_key=None
):
    """Upload gazette raw text - compatibility wrapper"""
    # This is a placeholder function for test compatibility
    if hasattr(storage, 'upload_content'):
        return storage.upload_content(content, file_key or f"{gazette_id}.txt")
    return None
