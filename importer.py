import csv

from itertools import islice
from elasticsearch import Elasticsearch, RequestError
from elasticsearch.helpers import bulk


def import_headlines():
    es_client = Elasticsearch()

    es_client.indices.delete("india-news-headlines", ignore=[400, 404])
    es_client.indices.create("india-news-headlines")

    with open("india-news-headlines.csv") as f:
        reader = csv.reader(f)
        header = next(reader)
        while True:
            s = islice(reader, 100000)
            actions = [{
                "_index": "india-news-headlines",
                "_type": "_doc",
                "date": row[0],
                "category": row[1],
                "headline": row[2]
            } for row in s]

            if actions:
                bulk(client=es_client, actions=actions)
                print(f"{len(actions)} docs indexed")
            else:
                break

    es_client.indices.refresh("india-news-headlines")
