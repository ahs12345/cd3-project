from aggregate_metrics import *
from io_metrics import *
from get_metrics import *

from datetime import datetime

from config import *

from simulate import *

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

    return ("graph", 0)

def simulate_pipeline(commits, conf):
    ghinfo = load_config()

    deploy_runtimes = {x[0]: x[1] for x in load_deployment_times()}
    sast_runtimes = {x[0]: x[1] for x in load_sast_times()}
    test_pass_rates = {x[0]: x[1] for x in load_test_pass_rates()}
    none_vals = [x[1]['none'] for x in load_cvss_vulnerabilities()]
    low_vals = [x[1]['low'] for x in load_cvss_vulnerabilities()]
    medium_vals = [x[1]['medium'] for x in load_cvss_vulnerabilities()]
    high_vals = [x[1]['high'] for x in load_cvss_vulnerabilities()]
    crtical_vals = [x[1]['critical'] for x in load_cvss_vulnerabilities()]

    sast_dist = Distribution(sast_runtimes.values(), 10)
    depl_dist = Distribution(deploy_runtimes.values(), 10)
    test_dist = Distribution(test_pass_rates.values(), 10)
    none_dist = Distribution(none_vals, 10)
    low_dist = Distribution(low_vals, 10)
    medium_dist = Distribution(medium_vals, 10)
    high_dist = Distribution(high_vals, 10)
    critical_dist = Distribution(crtical_vals, 10)


    sim_conf = SimulationConfiguration(
        conf,
        2,
        depl_dist,
        sast_dist,
        test_dist,
        none_dist,
        low_dist,
        medium_dist,
        high_dist,
        critical_dist,
        int(commits)
    )

    lttc, depl_freq, test_pass, none_sim, low_sim, medium_sim, high_sim, critical_sim = simulate(sim_conf)


    return ("simulate", lttc, depl_freq, test_pass, none_sim, low_sim, medium_sim, high_sim, critical_sim)