import os

from celery import Celery

# O Celery dá prioridade a CELERY_BROKER_URL sobre o broker passado abaixo, e o
# app-config do deployment (compartilhado com o backend) define essa variável
# com o Redis do backend, que descarta chaves quando a memória enche. A fila
# tem que usar o Redis dedicado (ADR-0009), o mesmo de redis_keys e do KEDA
os.environ["CELERY_BROKER_URL"] = os.environ["QUEUE_BROKER_URL"]

app = Celery("qd_data_processing", broker=os.environ["QUEUE_BROKER_URL"])
app.conf.update(
    task_default_queue="extraction",
    # Só confirma a mensagem depois de processar o diário
    task_acks_late=True,
    # Pod morto no meio do processamento -> mensagem volta para a fila
    task_reject_on_worker_lost=True,
    # Uma mensagem por vez, para a fila refletir o backlog real (escala do KEDA)
    worker_prefetch_multiplier=1,
    task_ignore_result=True,
    # Tem que ser maior que o tempo do diário mais demorado: depois dele, uma
    # mensagem não confirmada volta para a fila. Só é reduzido no cenário R1
    # (worker morto sem SIGTERM), ver ADR-0009
    broker_transport_options={
        "visibility_timeout": int(os.environ.get("QUEUE_VISIBILITY_TIMEOUT", 2 * 3600))
    },
)
app.autodiscover_tasks(["work_queue"])
