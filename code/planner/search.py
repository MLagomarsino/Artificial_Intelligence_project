from planner import plan
from planner import encoder
import utils


class Search():
    def __init__(self, encoder, initial_horizon):
        self.encoder = encoder
        self.horizon = initial_horizon
        self.found = False


class LinearSearch(Search):

    def do_search(self):
        # Override initial horizon
        self.horizon = 1

        print('Start linear search')
        # Implement linear search here and return a plan

        while not self.found:
            pass

        # Must return a plan object
        # when plan is found
