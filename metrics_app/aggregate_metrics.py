from io_metrics import *
from config import *
from typing import Callable

def aggregate_deployment_freqency(duration: timedelta, deployment_times: List[Tuple[datetime, float]]) -> List[int]:
    # Aggregate our deployment times into deployment freqency over time, grouping by 'duration'.
    # out[0] is past duration, out[1] is 1 duration ago, etc
    return __aggregate_metric_over_duration(
        duration,
        deployment_times,
        0,
        lambda a, b: a + 1
    )


def aggregate_deployment_time(duration: timedelta, deployment_times: List[Tuple[datetime, int]]) -> List[int]:
    # Get average deployment time grouped by duration
    aggregate_tally = aggregate_deployment_freqency(duration, deployment_times)
    aggregate_sum = __aggregate_metric_over_duration(
        duration,
        deployment_times,
        0,
        lambda a, b: a + b
    )

    # return averages
    return [int(sum / tally) if tally > 0 else None for sum, tally in zip(aggregate_sum, aggregate_tally)]

def aggregate_test_results(duration: timedelta, test_results: List[Tuple[datetime, float]]) -> List[float]:
    aggregate_tally = aggregate_deployment_freqency(duration, test_results)
    aggregate_sum = __aggregate_metric_over_duration(
        duration,
        test_results,
        0.0,
        lambda a, b: a + b
    )

    return [sum / float(tally) if tally > 0 else None for sum, tally in zip(aggregate_sum, aggregate_tally)]



def aggregate_cvss_vulnerabilities(duration: timedelta, datapoints) -> List[Dict[str, int]]:
    aggregate_tally = aggregate_deployment_freqency(duration, datapoints)
    aggregate_sum = __aggregate_metric_over_duration(
        duration,
        datapoints,
        {"none": 0, "low": 0, "medium": 0, "high": 0, "critical": 0},
        __merge_dict
    )

    out = []
    for dict, tally in zip(aggregate_sum, aggregate_tally):

        if tally > 0:
            new_dict = {key: (value / tally) for key, value in dict.items()}
            out.append(new_dict)
        else:
            out.append(None)

    return out

def __aggregate_metric_over_duration(duration: timedelta, collection: List, default, operation: Callable) -> List:
    out: List = [default]
    until = datetime.combine(collection[0][0] - duration, time.max) if len(collection) > 0 else None
    for entry in collection:
        if entry[0] > until:
            out[-1] = operation(out[-1], entry[1])
        else:
            new_until = datetime.combine(entry[0] - duration, time.max)
            diff = until - new_until
            while (diff > duration):
                out.append(default)
                diff -= duration

            until = new_until
            out.append(operation(default, entry[1]))
    return out

#takes sum number of vulnerabilities for each day
def __merge_dict(dict1, dict2):
    for key in dict1:
        dict1[key] += dict2[key]
    
    return dict1