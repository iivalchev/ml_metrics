from pipeline.fetch_docs import fetch_docs


def main():
    fetch_docs_step = fetch_docs(
        "/home/ivalchev/talks/ml_metrics/data",
        es_host="localhost",
        es_index="india-news-headlines",
        es_query={
            "query": {
                "constant_score": {
                    "filter": {
                        "bool": {
                            "must_not": {
                                "term": {
                                    "category": "unknown"
                                }
                            }
                        }
                    }
                }
            }
        },
        limit=200000)

    # TODO add more steps of the pipeline


if __name__ == "__main__":
    main()
