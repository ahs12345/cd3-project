from get_metrics import *
import json
import os

# Here we store/load our metric information to/from disk
def save_deployment_times(time_entries: List[Tuple[datetime, int]]):
    __save_time_entries('db/deployment_times.txt', time_entries)

def save_sast_times(time_entries: List[Tuple[datetime, int]]):
    __save_time_entries('db/sast_times.txt', time_entries)

def load_deployment_times() -> List[Tuple[datetime, int]]:
    return __load_time_entries('db/deployment_times.txt')

def load_sast_times() -> List[Tuple[datetime, int]]:
    return __load_time_entries('db/sast_times.txt')


def save_test_pass_rate(entry: Tuple[datetime, float]):
    ln = json.dumps({
        'timestamp' : entry[0].isoformat(),
        'result' : entry[1]
    })

    with open('db/test_results.txt', 'a') as f:
        f.write(ln + '\n')

def load_test_pass_rates() -> List[Tuple[datetime, float]]:
    datapoints: List[Tuple[datetime, float]] = []
    with open('db/test_results.txt', 'r') as f:
        for ln in f.readlines():
            ob = json.loads(ln)
            datapoints.append((
                datetime.fromisoformat(ob['timestamp']),
                float(ob['result'])
            ))
    return datapoints

def save_cvss_vulnerabilities(data: Dict[str, int]):
    ln = json.dumps({
        'timestamp' : datetime.now().isoformat(),
        'data' : data
    })
    with open('db/cvss_vulnerabilities.txt', 'a') as f:
        f.write(ln + '\n')

def load_cvss_vulnerabilities() -> List[Tuple[datetime, Dict[str, int]]]:
    datapoints: List[Tuple[datetime, Dict[str, int]]] = []
    with open('db/cvss_vulnerabilities.txt', 'r') as f:
        for ln in f.readlines():
            ob = json.loads(ln)
            datapoints.append((
                datetime.fromisoformat(ob['timestamp']),
                ob['data']
            ))
    return datapoints


def __save_time_entries(fpath: str, time_entries: List[Tuple[datetime, int]]):
    lns = [
        json.dumps({
            'timestamp' : e[0].isoformat(),
            'seconds' : e[1]
        })
        for e in time_entries
    ]

    with open(fpath, 'w') as f:
        for ln in lns:
            f.write(ln + '\n')


def __load_time_entries(fpath: str) -> List[Tuple[datetime, int]]:
    datapoints: List[Tuple[datetime, int]] = []

    with open(fpath, 'r') as f:
        for ln in f.readlines():
            ob = json.loads(ln)
            datapoints.append((
                datetime.fromisoformat(ob['timestamp']),
                int(ob['seconds'])
            ))
    return datapoints


if __name__ == "__main__":
    owner, repo, token, id, id2 = input().split()
    ghinfo = GithubInfo(owner, repo, token, id, id2)
    save_deployment_times(get_deployment_times(ghinfo))
    save_sast_times(get_sast_times(ghinfo))
    save_test_pass_rate(get_test_pass_rate(ghinfo))
    save_cvss_vulnerabilities(get_cvss_num(ghinfo))