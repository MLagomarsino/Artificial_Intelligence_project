# Artificial Intelligence Project
## Objective of the Project
The aim of the project is the implementation (using Python 2.7 as interpreter) of a Planner for solving an Artificial Intelligence planning problem with SAT algorithms (**SAT based planner**).

Given an instance specified by the initial and the goal states, as well as the actions that may be performed and a horizon length, the algorithm exploits the frame axioms and builds a Propositional Formula. The boolean formula is solved using  [Minisat](http://minisat.se/). If the latter is satisfiable, the [ENHSP](https://bitbucket.org/enricode/the-enhsp-planner/src/master/) will find an assignment which would be translated into the desired plan (a sequence of actions) to reach the objective. Otherwise a new encoding will be generated reflecting a longer plan length.

## How to run
Clone the repository:
```bash
git clone https://github.com/MLagomarsino/Artificial_Intelligence_project.git
```
Install the required libraries and the Minisat solver:
```bash
cd ~/Artificial_Intelligence_project
pip install -r z3
pip install -r satispy
sudo apt-get update
sudo apt-get install minisat
```
From the workspace folder, install and compile the ENHSP module with the following commands:
```bash
cd code/enhsp
./install
./compile
```
Moreover in bin folder:
```bash
cd ..
cd bin
./validate
```
Run the project using **Python 2.7** as interpreter. 
From terminal with command:
```
plan.py [-h] [-domain <path_pddl_domain> <path_pddl_problem>] [-linear] [-parallel] [-pprint]
```
Or loading for example the following configuration in *PyCharm*:

Script path: 
``` ../Artificial_Intelligence_project/code/plan.py ```

Parameters: 
``` -domain ../Artificial_Intelligence_project/domains/blockworld/domain.pddl ../Artificial_Intelligence_project/domains/blockworld/instances/pb3.pddl ```

Working directory: 
``` ../Artificial_Intelligence_project/code ```

## Author
| Name           | ID        | E-mail                                                         |
| ---------------- | -------------- | ---------------------------------------------------------------- |
| Marta Lagomarsino | 4213518 | marta.lago@hotmail.it |
