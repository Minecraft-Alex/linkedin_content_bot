import schedule
from typing import Callable, Dict

class PostScheduler:
    def __init__(self, config: Dict):
        self.config = config

    def schedule_posts(self, job: Callable):
        frequency = self.config['schedule']['frequency']
        time = self.config['schedule']['time']

        if frequency == 'daily':
            schedule.every().day.at(time).do(job)
        elif frequency == 'weekly':
            schedule.every().week.at(time).do(job)
        # Add more scheduling options as needed
