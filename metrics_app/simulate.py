import simpy
import random

import statistics

from typing import List

DAY_DURATION = 24 * 60
SIM_DAYS = 10

NUM_GITHUB_RUNNERS = 2

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


class Pipeline:
    def __init__(self, env: simpy.Environment, num_runners: int, lttc_dist: Distribution):
        """
        Initialises a Pipeline simulation. num_runners determines
        how many GitHub cloud servers can run the pipeline in parralel.
        """
        self.env = env
        self.runner = simpy.Resource(env, num_runners)
        self.lttc_dist = lttc_dist
    
    def deploy(self, commit: int):
        yield self.env.timeout(self.lttc_dist.sample())


def commit_to_pipeline(env: simpy.Environment, commit: int, pipeline: Pipeline):
    """
    Simulates a single commit to a pipeline
    """

    global simulated_lttc
    # Sample our simulated LTTC
    start_time = env.now

    # We require a GitHub runner to execute our request
    with pipeline.runner.request() as request:
        yield request
        yield env.process(pipeline.deploy(commit))
    
    simulated_lttc.append(env.now - start_time)


def __run_sim(env: simpy.Environment, deployments_per_day: int, lttc_dist: Distribution):
    global simulated_lttc
    simulated_lttc = []
    commit = 0

    pipeline = Pipeline(env, NUM_GITHUB_RUNNERS, lttc_dist)

    average_wait = DAY_DURATION / deployments_per_day
    while True:
        # Commit at a slightly random frequency around our deployments per day
        yield env.timeout(random.uniform(average_wait * 0.8, average_wait * 1.2))

        commit += 1
        env.process(commit_to_pipeline(env, commit, pipeline))
    


def simulate(deployments_per_day: int, lttc_dist: Distribution):
    global simulated_lttc

    env = simpy.Environment()
    env.process(__run_sim(env, deployments_per_day, lttc_dist))
    env.run(until=DAY_DURATION * SIM_DAYS)

    return statistics.mean(simulated_lttc)

if __name__ == "__main__":
    dist = Distribution([6,6,7,7,7,7,7,8,8,9], 1)
    
    print(simulate(24, dist))
    

