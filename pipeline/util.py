import mlflow
import mlflow.tracking as tracking
from mlflow.entities.metric import Metric

from pyformance.reporters.reporter import Reporter


def get_or_create_experiment_id(experiment_name):
    experiment_id = next((e.experiment_id
                          for e in tracking._get_store().list_experiments()
                          if e.name == experiment_name), None)
    if experiment_id is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    return experiment_id


class MlflowReporter(Reporter):
    def __init__(self,
                 registry=None,
                 reporting_interval=30,
                 clock=None,
                 active_run=None):
        super(MlflowReporter, self).__init__(registry, reporting_interval,
                                             clock)
        self.active_run = active_run

    def report_now(self, registry=None, timestamp=None):
        registry = registry or self.registry
        timestamp = timestamp or int(round(self.clock.time()))
        active_run = self.active_run or mlflow.active_run()
        metrics = (registry or self.registry).dump_metrics()

        for mkey, mdict in metrics.items():
            for mname, mvalue in mdict.items():
                active_run.log_metric(
                    Metric(f"{mkey}_{mname}", mvalue, timestamp))
