from typing import Dict, List

from requests import Response, get

from collections import namedtuple

from datetime import datetime, timedelta
from dateutil import parser
import re
import zipfile
import io



class GithubInfo:
    def __init__(self, owner: str, repo: str, token: str, deployment_workflow_id: str, codeql_workflow_id: str):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.deployment_workflow_id = deployment_workflow_id
        self.codeql_workflow_id = codeql_workflow_id
    
    def headers(self) -> Dict[str, str]:
        return {
            'Accept':               'application/vnd.github+json',
            'Authorization':        'Bearer ' + self.token,
            'X-GitHub-Api-Version': '2022-11-28'
        }
    
    def repo_path(self) -> str:
        return self.owner + '/' + self.repo

def get_deployment_frequency(info: GithubInfo, duration: timedelta) -> int:
    response: Response = get(
        'https://api.github.com/repos/' + info.repo_path() + '/actions/workflows/' + info.deployment_workflow_id + '/runs',
        headers=info.headers()
    )

    now: datetime = datetime.now()

    # Get the time ended of all workflow runs
    end_times:   List[datetime] = [parser.isoparse(r['updated_at']).replace(tzinfo=None) 
                                   for r in response.json()['workflow_runs']]

    count = len(list(filter(
        lambda t: ((now - t) < duration),
        end_times
    )))

    return count

def get_deployment_times(info: GithubInfo) -> List[datetime]:
    response: Response = get(
        'https://api.github.com/repos/' + info.repo_path() + '/actions/workflows/' + info.deployment_workflow_id + '/runs',
        headers=info.headers()
    )

    # Get the time ended of all workflow runs
    start_times: List[datetime] = [parser.isoparse(r['created_at']).replace(tzinfo=None) 
                                   for r in response.json()['workflow_runs']]

    end_times:   List[datetime] = [parser.isoparse(r['updated_at']).replace(tzinfo=None) 
                                   for r in response.json()['workflow_runs']]

    lead_times:  List[datetime] = [end_times[i] - start_times[i]
                                   for i in range(len(start_times))]

    return lead_times

def get_test_output(info: GithubInfo) -> str:
    response: Response = get(
        'https://api.github.com/repos/' + info.repo_path() + '/actions/workflows/' + info.deployment_workflow_id + '/runs',
        headers=info.headers()
    )
    latestRunId = response.json()['workflow_runs'][0]['id']

    logUrl = 'https://api.github.com/repos/' + info.repo_path() + '/actions/runs/' + str(latestRunId) + '/logs'
    
    logResponse = get(logUrl, headers=info.headers())


    with zipfile.ZipFile(io.BytesIO(logResponse.content)) as z:
        all_contents = []
        for filename in z.namelist():
            with z.open(filename) as f:
                file_content = f.read().decode('utf-8')
                all_contents.append(file_content)

    merged_content = "\n".join(all_contents)

    return merged_content

def parse_test_pass_rate(log: str) -> str:
    files_pattern = re.compile(r">> (\d+) files")
    error_pattern = re.compile(r">> (\d+) errors")

    files_match = files_pattern.search(log)
    error_match = error_pattern.search(log)

    if files_match:
        return "100%"

    elif error_match:
        totalFiles = 132
        errors = int(error_match.group(1))
        passRate = (totalFiles - errors) / totalFiles * 100
        return str(passRate) + "%"
    
    return "0%" 



def get_sast_times(info: GithubInfo) -> List[datetime]:
    response: Response = get(
        'https://api.github.com/repos/' + info.repo_path() + '/actions/workflows/' + info.codeql_workflow_id + '/runs',
        headers=info.headers()
    )

    # Get the time ended of all workflow runs
    start_times: List[datetime] = [parser.isoparse(r['created_at']).replace(tzinfo=None) 
                                   for r in response.json()['workflow_runs']]

    end_times:   List[datetime] = [parser.isoparse(r['updated_at']).replace(tzinfo=None) 
                                   for r in response.json()['workflow_runs']]

    lead_times:  List[datetime] = [end_times[i] - start_times[i]
                                   for i in range(len(start_times))]

    return lead_times

def get_cvss_num(info: GithubInfo):
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

owner, repo, token, id, id2 = input().split()
ghinfo = GithubInfo(owner, repo, token, id, id2)

# Get deployments/month
count = get_deployment_frequency(
    ghinfo,
    timedelta(weeks=4)
)

lead_times = get_deployment_times(ghinfo)

sast_times = get_sast_times(ghinfo)

cvss_num = get_cvss_num(ghinfo)

test_log = get_test_output(ghinfo)
test_pass_rate = parse_test_pass_rate(test_log)

print("Deployment count last 4 weeks: ", count)
print("Deployment time of last workflow: ", lead_times[0])
print("Test Pass Rate: ", test_pass_rate)
print("Last SAST tool runtime: ", sast_times[0])
print("Number of open vulnerabilities: ", cvss_num)

