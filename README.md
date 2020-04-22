# Artificial Intelligence Project
## Objective of the Project
The aim of the project is the implementation (using Python 2.7 as interpreter) of a Planner for solving an Artificial Intelligence planning problem with SAT algorithms (**SAT based planner**).

Given an instance specified by the initial and the goal states, as well as the actions that may be performed and a horizon length, the algorithm exploits the frame axioms and builds a Propositional Formula. If the latter is satisfiable, a SAT solver will find an assignment which would be translated into the desired plan to reach the objective. Otherwise the compiler will generate a new encoding reflecting a longer plan length.

## How to run
Add folder domain in the current folder
```
../Artificial_Intelligence_project/domains
```
and bin and enhsp inside the folder code
```
../Artificial_Intelligence_project/code/bin
../Artificial_Intelligence_project/code/enhsp
```
Enter enhsp folder and perform the following commands:
```./install``` and ```./compile```

Moreover in bin folder: ```./validate```

Run the project using **Python 2.7** as interpreter. 
From terminal with command:
```
plan.py [-h] [-domain DOMAIN] [-linear] [-parallel] [-pprint]
```
Or  loading the following configuration in *PyCharm*:

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
