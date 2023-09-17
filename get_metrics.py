from typing import Dict, List

from requests import Response, get

from collections import namedtuple

from datetime import datetime, timedelta
from dateutil import parser



class GithubInfo:
    def __init__(self, owner: str, repo: str, token: str, deployment_workflow_id: str):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.deployment_workflow_id = deployment_workflow_id
    
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

owner, repo, token, id = input().split()
ghinfo = GithubInfo(owner, repo, token, id)

# Get deployments/month
count = get_deployment_frequency(
    ghinfo,
    timedelta(weeks=4)
)

lead_times = get_deployment_times(
    ghinfo
)

print("Deployment count last 4 weeks: ", count)
print("Deployment time of last workflow: ", lead_times[0])
