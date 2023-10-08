from typing import Dict, List, Tuple

from requests import Response, get

from collections import namedtuple

from datetime import datetime, timedelta
from dateutil import parser
import re
import zipfile
import io

from config import GithubInfo

def get_deployment_times(info: GithubInfo) -> List[Tuple[datetime, int]]:
    response: Response = get(
        'https://api.github.com/repos/' + info.repo_path() + '/actions/workflows/' + info.deployment_workflow_id + '/runs',
        headers=info.headers()
    )

    return __parse_duration_response(response)

def __get_test_output(info: GithubInfo) -> Tuple[datetime, str]:
    #gets the output from the log of the latest run

    response: Response = get(
        'https://api.github.com/repos/' + info.repo_path() + '/actions/workflows/' + info.deployment_workflow_id + '/runs',
        headers=info.headers()
    )
    latestRun = response.json()['workflow_runs'][0]

    latestRunId = latestRun['id']
    latestRunTime = parser.isoparse(latestRun['updated_at']).replace(tzinfo=None)

    logUrl = 'https://api.github.com/repos/' + info.repo_path() + '/actions/runs/' + str(latestRunId) + '/logs'
    
    logResponse = get(logUrl, headers=info.headers())


    with zipfile.ZipFile(io.BytesIO(logResponse.content)) as z:
        all_contents = []
        for filename in z.namelist():
            with z.open(filename) as f:
                file_content = f.read().decode('utf-8')
                all_contents.append(file_content)

    merged_content = "\n".join(all_contents)

    return latestRunTime, merged_content

def get_test_pass_rate(info: GithubInfo) -> Tuple[datetime, float]:
    runtime, log = __get_test_output(info)

    #parses the log, checking for errors to calculate the pass rate
    files_pattern = re.compile(r">> (\d+) files")
    error_pattern = re.compile(r">> (\d+) errors")

    files_match = files_pattern.search(log)
    error_match = error_pattern.search(log)

    if files_match:
        return runtime, 100.0

    elif error_match:
        total_files = 132
        errors = int(error_match.group(1))
        pass_rate = (total_files - errors) / total_files * 100
        return runtime, pass_rate
    
    return runtime, 0



def get_sast_times(info: GithubInfo) -> List[Tuple[datetime, int]]:
    response: Response = get(
        'https://api.github.com/repos/' + info.repo_path() + '/actions/workflows/' + info.codeql_workflow_id + '/runs',
        headers=info.headers()
    )

    return __parse_duration_response(response)

def get_cvss_num(info: GithubInfo) -> Dict[str, int]:
    page = 1
    page_len = 1
    cvss_num = {"none": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
    while page_len != 0:
        response: Response = get(
            'https://api.github.com/repos/' + info.repo_path() + '/code-scanning/alerts?per_page=100&state=open&page=' + str(page),
            headers=info.headers()
        )
        for r in response.json():
            cvss_num[r['rule']['security_severity_level']] += 1

        page_len = len(response.json())
        page += 1

    return cvss_num


def __parse_duration_response(response: Response) -> List[Tuple[datetime, int]]:
    # Get the time ended of all workflow runs
    start_times: List[datetime] = [parser.isoparse(r['created_at']).replace(tzinfo=None) 
                                   for r in response.json()['workflow_runs']]

    end_times:   List[datetime] = [parser.isoparse(r['updated_at']).replace(tzinfo=None) 
                                   for r in response.json()['workflow_runs']]

    lead_times:  List[Tuple[datetime, int]] = [(start, (end - start).total_seconds())
                                               for start, end in zip(start_times, end_times)]

    return lead_times


def fetch():
    owner, repo, token, id, id2 = input().split()
    ghinfo = GithubInfo(owner, repo, token, id, id2)

    lead_times = get_deployment_times(ghinfo)

    sast_times = get_sast_times(ghinfo)

    # cvss_num = get_cvss_num(ghinfo)

    test_pass_rate = get_test_pass_rate(ghinfo)


    print("Deployment time of last workflow: ", lead_times[0])
    print("Test Pass Rate: ", test_pass_rate)
    print("Last SAST tool runtime: ", sast_times[0])
    # print("Number of open vulnerabilities: ", cvss_num)


if __name__ == "__main__":
    fetch()
