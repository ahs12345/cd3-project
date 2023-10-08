from aggregate_metrics import *
from io_metrics import *
from get_metrics import *

from datetime import datetime

from config import *

def get_last_reload() -> str:
    out = ''
    with open('db/last_reload.txt', 'r') as f:
        out = f.readlines()[0].strip()
    return out

def reload_metrics():
    ghinfo = load_config()

    save_deployment_times(get_deployment_times(ghinfo))
    save_sast_times(get_sast_times(ghinfo))
    save_test_pass_rate(get_test_pass_rate(ghinfo))
    save_cvss_vulnerabilities(get_cvss_num(ghinfo))

    with open('db/last_reload.txt', 'w') as f:
        f.write(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))