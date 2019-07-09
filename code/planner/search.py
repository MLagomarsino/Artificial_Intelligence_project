from planner import plan
from planner import encoder
import utils
from encoder import Encoder


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
        # Implement linear search here and return a plan

        while not self.found:

            # chiama metodo encode di encoder passando un orizzonte e ottengo la formula booleana
            planning_formula = self.encoder.encode(self.horizon)

            # risolverla -> importa CDCL o altro solver e provare a fargliela risolvere
            # se ho un assegnamento (esiste sol)

            # esco dal ciclo
            # self.found = True

            # faccio traduzione inversa
            # a un numero corrisponde azione a certo step

            # incremento horizon
            self.horizon += 1

            print(self.encoder.actions[0].name)
            # pass

        # Must return a plan object
        # when plan is found
