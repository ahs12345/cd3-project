import os

from typing import Dict

class GithubInfo:
    def __init__(self, repo_owner: str, repo_name: str, github_pat: str, deployment_workflow_id: str, security_workflow_id: str):
        self.owner = repo_owner
        self.repo = repo_name
        self.token = github_pat
        self.deployment_workflow_id = deployment_workflow_id
        self.codeql_workflow_id = security_workflow_id
    
    def headers(self) -> Dict[str, str]:
        return {
            'Accept':               'application/vnd.github+json',
            'Authorization':        'Bearer ' + self.token,
            'X-GitHub-Api-Version': '2022-11-28'
        }
    
    def repo_path(self) -> str:
        return self.owner + '/' + self.repo

def load_config() -> GithubInfo:
    if not os.path.exists('user.cfg'):
        print('Error: user.cfg file not found. Please follow instructions in user_template.cfg.')
        exit()
    
    cfg_dict = {}
    # Parse cfg file
    with open('user.cfg', 'r') as f:
        for ln in f.readlines():
            if ln.startswith('#'):
                continue
            if not ln[0].isalnum():
                continue
            
            key = ln.split(':')[0].strip()
            value = ln.split(':')[1].strip()

            cfg_dict[key] = value
    
    # Load the config into a GithubInfo object
    return GithubInfo(**cfg_dict)