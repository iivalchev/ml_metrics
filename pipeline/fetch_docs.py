import mlflow
import json
import os
from elasticsearch import Elasticsearch
from pipeline.util import get_or_create_experiment_id
from pipeline.util import MlflowReporter
from pyformance.registry import MetricsRegistry
from pyformance.reporters.influx import InfluxReporter

mlflow.set_tracking_uri("http://127.0.0.1:5000")


def fetch_docs(base_path, es_host, es_index, es_query=None, limit=-1):
    exp_name = "fetch_docs"
    exp_path = f"{base_path}/{exp_name}"
    os.makedirs(exp_path, exist_ok=True)

    run = mlflow.start_run(experiment_id=get_or_create_experiment_id(exp_name))
    docs_path = f"{exp_path}/{run.run_info.run_uuid}"

    registry = MetricsRegistry()

    mlflow_reporter = MlflowReporter(
        registry=registry, active_run=run, reporting_interval=10)
    mlflow_reporter.start()

    influx_reporter = InfluxReporter(
        registry=registry, reporting_interval=10, autocreate_database=True)
    influx_reporter.start()

    try:
        mlflow.log_param("docs_path", docs_path)
        mlflow.log_param("es_host", es_host)
        mlflow.log_param("es_index", es_index)
        mlflow.log_param("es_query", es_query)

        _write_docs(
            _get_docs_scrolled(registry, es_host, es_index, es_query, limit),
            docs_path)

        influx_reporter.report_now()
        mlflow_reporter.report_now()

        mlflow.end_run()
    except Exception as e:
        mlflow.end_run("FAILED")
        raise e
    finally:
        influx_reporter.stop()
        mlflow_reporter.stop()

    return run


def _get_docs_scrolled(registry, es_host, es_index, es_query=None, limit=-1):
    es_hits_meter = registry.meter("es_hits")
    es_scroll_timer = registry.timer("es_scroll")

    es_client = Elasticsearch(es_host)
    r = es_client.search(
        index=es_index, body=es_query, scroll="1m")
    total_hits = 0

    while True:
        hits = r["hits"]["hits"]
        n_hits = len(hits)
        total_hits += n_hits

        if n_hits == 0:
            break

        es_hits_meter.mark(n_hits)

        yield [doc["_source"] for doc in hits]

        if limit >= 0 and total_hits > limit:
            break

        scroll_id = r.get("_scroll_id", None)
        if scroll_id is None:
            break

        tx = es_scroll_timer.time()
        r = es_client.scroll(scroll_id, scroll="1m")
        tx.stop()


def _write_docs(scrolls, path):
    with open(path, "w") as f:
        for docs in scrolls:
            for doc in docs:
                f.write("%s\n" % json.dumps(doc))
