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

        # Override initial horizon (M: estimate the number of actions to reach the goal)
        # self.horizon = 1

        print('Start linear search')
        # Implement linear search here
        # and return a plan

        # M: initialize plan

        while not self.found:

            # M: check preconditions of our task match the ones of given action
            # the effect matches the goal?
            # if yes -> self.found = True and return plan

            # if no -> update the preconditions

            print(self.encoder.actions[0].name)
            pass

        ## Must return a plan object
        ## when plan is found
