import simpy
import random

import math

import statistics

from typing import List

DAY_DURATION = 24 * 60
SIM_DAYS = 10

NUM_GITHUB_RUNNERS = 1

simulated_lttc = []


class Distribution:
    def __init__(self, values: List[int], step_size: int):
        """
        Generates a discrete distribution approximation from a set of input samples,
        and a discrete step size.
        """
        self.step_size = step_size

        max_index = 0
        dist = {0: 0}
        # Count occurences within step_size blocks
        for v in values:
            idx = int(v / self.step_size)
            max_index = max(idx, max_index)
            dist[idx] = dist.get(idx) + 1 if dist.get(idx) else 1
        
        self.dist = [
            dist[i] if dist.get(i) else 0 
            for i in range(0, max_index + 1)
        ]

        # Transform to cumulative sum
        self.dist = [
            sum(self.dist[0:i+1])
            for i in range(len(self.dist))
        ]

        self.max_roll = self.dist[-1]

    
    def sample(self) -> int:
        """
        Samples the distribution
        """
        roll = random.randint(0, self.max_roll)
        for i in range(len(self.dist)):
            no_chance = self.dist[i] == 0 or self.dist[i] == self.dist[i - 1]
            if roll > self.dist[i] or no_chance:
                continue
            return i * self.step_size
        

class SimulationConfiguration:
    def __init__(self, 
        sast_configuration: str,
        num_runners: int,
        pipeline_delay: Distribution,
        sast_runtime: Distribution,
        commits_per_day: int
    ):
        """
        Defines the configuration of the pipeline simulation.
        sast_configuration:             a string ('seq' or 'par') which defines whether the SAST tool runs at the same time as build and test, or before
        num_runners:                    the amount of GitHub VMs available to run builds in parralel
        pipeline_delay, sast_runtime:   distributions of our sampled metric data
        commits_per_day:                user input determining how many commits they expect to have per day
        """
        self.sast_configuration = sast_configuration
        self.num_runners = num_runners
        self.pipeline_delay = pipeline_delay
        self.sast_runtime = sast_runtime
        self.commits_per_day = commits_per_day


class SimulationState:
    def __init__(self):
        self.simulated_lttc = []
        self.successful_deployments = 0


class Pipeline:
    def __init__(self, env: simpy.Environment, conf: SimulationConfiguration):
        """
        Initialises a Pipeline simulation.
        """
        self.env = env
        self.conf = conf

        self.runner = simpy.Resource(env, conf.num_runners)
        self.cloud_deployer = simpy.Resource(env, 1)

    def deploy(self, commit: int):
        if self.conf.sast_configuration == 'par':
            yield self.env.process(self.par_deploy(commit))
        else:
            yield self.env.process(self.seq_deploy(commit))

    def seq_deploy(self, commit: int):
        # We require a GitHub runner to execute our request
        with self.runner.request() as runr:
            yield runr
            # Simulate SAST runtime
            yield self.env.timeout(self.conf.sast_runtime.sample())

            # Deploy
            with self.cloud_deployer.request() as depl:
                yield depl
                yield self.env.timeout(self.conf.pipeline_delay.sample())
    
    def par_deploy(self, commit: int):
        def run_sast():
            with self.runner.request() as runr:
                yield self.env.timeout(self.conf.sast_runtime.sample())
        
        def run_deploy():
            # Need deployer (to be only one deploying to Vercel) and GitHub runner to deploy
            with self.runner.request() as runr:
                with self.cloud_deployer.request() as depl:
                    yield self.env.all_of([runr, depl])

                    yield self.env.timeout(self.conf.pipeline_delay.sample())
        
        yield self.env.all_of([
            self.env.process(run_sast()),
            self.env.process(run_deploy())
        ])




def commit_to_pipeline(env: simpy.Environment, commit: int, pipeline: Pipeline):
    """
    Simulates a single commit to a pipeline
    """

    global simulated_lttc
    # Sample our simulated LTTC
    start_time = env.now

    yield env.process(pipeline.deploy(commit))
    
    simulated_lttc.append(env.now - start_time)


def __run_sim(env: simpy.Environment, conf: SimulationConfiguration):
    global simulated_lttc
    simulated_lttc = []
    commit = 0

    pipeline = Pipeline(env, conf)

    average_wait = DAY_DURATION / conf.commits_per_day
    while True:
        # Commit at a slightly random frequency around our deployments per day
        yield env.timeout(random.uniform(average_wait * 0.8, average_wait * 1.2))

        commit += 1
        env.process(commit_to_pipeline(env, commit, pipeline))
    


def simulate(conf: SimulationConfiguration):
    global simulated_lttc

    env = simpy.Environment()
    env.process(__run_sim(env, conf))
    env.run(until=DAY_DURATION * SIM_DAYS)

    return statistics.mean(simulated_lttc), math.ceil(len(simulated_lttc) / SIM_DAYS)

if __name__ == "__main__":
    dist = Distribution([6,6,7,7,7,7,7,8,8,9], 1)
    
    conf = SimulationConfiguration(
        'seq',
        2,
        dist,
        dist,
        100
    )

    print(simulate(conf))
    

