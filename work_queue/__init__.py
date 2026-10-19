"""
Fila de extração de diários (Celery + Redis)

Alternativa ao pipeline sequencial `gazette_texts` (CronJob), que continua
igual e serve de baseline. O produtor (`-p enqueue_extraction`) enfileira só o
id de cada diário não processado; os workers extraem e indexam um diário por
vez; `-p themes_from_queue` roda os excertos temáticos dos diários indexados.

O pacote se chama `work_queue`, e não `queue`, para não colidir com o módulo
`queue` da biblioteca padrão.
"""
