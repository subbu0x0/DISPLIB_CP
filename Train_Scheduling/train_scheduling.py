from ortools.sat.python import cp_model
from add_predecessors import add_predecessors
from get_resource_data import get_resource_data
from add_start_lb import add_start_lb
from add_start_ub import add_start_ub
import json
import os


def solve_displib_problem(problem_json):

    model = cp_model.CpModel()

    trains = problem_json["trains"]
    objective_components = problem_json["objective"]

    start_lb_trains = []
    start_ub_trains = []

    trains = add_predecessors(trains) # Add predecessors to the train operations

    train_vars = {} # Dictionary to store the variables for each operation of each train

    min_duration_trains, release_time_resources, resource_vars = get_resource_data(trains) # Get the resource data

    LARGE_INTEGER = 2*(sum(min_duration_trains) + sum(release_time_resources.values())) # Large integer to use as upper bound for variables
    #print(resource_vars)

    for train_index, train_operations in enumerate(trains):

        train_vars[train_index] = {}

        start_lb_trains.append(add_start_lb(train_operations)) # Get the lower bound for the start time of each operation
        start_ub_trains.append(add_start_ub(train_operations,LARGE_INTEGER)) # Get the upper bound for the start time of each operation

        for op_index,op_data in enumerate(train_operations):

            start_lb = start_lb_trains[train_index][op_index]
            start_ub = start_ub_trains[train_index][op_index]

            min_duration = op_data.get("min_duration", 0)

            train_vars[train_index][op_index] = {}

            train_vars[train_index][op_index]["start_time"] = model.NewIntVar(start_lb, start_ub, f"train_{train_index}_op_{op_index}_start")
            train_vars[train_index][op_index]["active"] = model.NewBoolVar(f"active_{train_index}_{op_index}")
            train_vars[train_index][op_index]["end_time"] = model.NewIntVar(start_lb + min_duration, LARGE_INTEGER, f"train_{train_index}_op_{op_index}_end")

        last_op_index = len(train_operations) - 1
        model.Add(train_vars[train_index][last_op_index]["active"] == 1) # Last operation of each train is active
        model.Add(train_vars[train_index][0]["active"] == 1) # First operation of each train is active
    # 2. Add Successor Constraints

    def add_successor_constraints(train_operations, train_index):

        for op_index, op_data in enumerate(train_operations):

            successors = op_data.get("successors", [])
            min_duration = op_data.get("min_duration", 0)

            active_ij = train_vars[train_index][op_index]["active"]
            start_time_ij = train_vars[train_index][op_index]["start_time"]
            end_time_ij = train_vars[train_index][op_index]["end_time"]

            if not successors: # last operation has no successors
                continue

            successor_vars = [train_vars[train_index][succ_op]["active"] for succ_op in successors]
            model.Add(sum(successor_vars) == 1).OnlyEnforceIf(active_ij) # Only one successor can be active


            model.Add(end_time_ij - start_time_ij >= min_duration).OnlyEnforceIf(active_ij) # Operation must take at least min_duration


            for k,successor in enumerate(successors):

                active_ik = train_vars[train_index][successor]["active"]
                start_time_ik = train_vars[train_index][successor]["start_time"]

                
                resources_k = train_operations[successor].get("resources", [])

                model.Add(start_time_ik == end_time_ij).OnlyEnforceIf([active_ij,active_ik]) # Successor starts immediately after the current operation
                
                
                count = 0 # Count to check if all resources needed for the successor are shared with other operations
                for resource_data in resources_k:

                    resource = resource_data["resource"]

                    if len(resource_vars[resource]) > 1: # If the resource is shared with other operations
                        count = 1
                        break
                if(count == 0): # If the resource is not shared with other operations
                    model.Add(end_time_ij == start_time_ij + min_duration).OnlyEnforceIf([active_ik,active_ij]) 

    for train_index, train_operations in enumerate(trains):
        add_successor_constraints(train_operations, train_index)


    # 3. Add Resource Constraints
    for resource in resource_vars:

        operations_R = resource_vars[resource] # Operations that use the resource
        release_time_R = release_time_resources[resource] # Release time of the resource

        l = len(operations_R)

        if(l == 1): # If only one operation uses the resource
            continue

        for i in range(l):

            op1_data = operations_R[i]
            
            train1_idx = op1_data["train"]
            op1_idx = op1_data["operation"]

            start1 = train_vars[train1_idx][op1_idx]["start_time"]
            active1 = train_vars[train1_idx][op1_idx]["active"]
            end1 = train_vars[train1_idx][op1_idx]["end_time"]

            for j in range(i + 1, l):
                
                op2_data = operations_R[j]

                if train1_idx == op2_data["train"]:
                    continue # Only add constraints for operations from *different* trains

                train2_idx = op2_data["train"]
                op2_idx = op2_data["operation"]

                start2 = train_vars[train2_idx][op2_idx]["start_time"]
                active2 = train_vars[train2_idx][op2_idx]["active"]
                end2 = train_vars[train2_idx][op2_idx]["end_time"]

                # Ensure no overlap: op1 finishes before op2 starts OR op2 finishes before op1 starts
                y = model.NewBoolVar(f"resource_order_{train1_idx}_{op1_idx}_{train2_idx}_{op2_idx}_{resource}") # Variable to check if op1 finishes before op2 starts

                model.Add(start1 > end2+ release_time_R).OnlyEnforceIf([y, active1, active2])
                model.Add(start2 > end1 + release_time_R).OnlyEnforceIf([y.Not(), active1, active2])
        

    # 4. Define Objective Function
    objective_expr = 0
    for obj_component in objective_components:
        if obj_component["type"] == "op_delay":
            train_index = obj_component["train"]
            op_index = obj_component["operation"]
            threshold = obj_component.get("threshold", 0)
            coeff = obj_component.get("coeff", 0)
            increment = obj_component.get("increment", 0)
            delay = model.NewIntVar(0, LARGE_INTEGER, f"delay_train_{train_index}_op_{op_index}")
            model.Add(delay == train_vars[train_index][op_index]["start_time"] - threshold)
            delayed_cost = model.NewBoolVar(f"delayed_cost_{train_index}_{op_index}")
            model.Add(delay > 0 ).OnlyEnforceIf(delayed_cost)
            model.Add(delay <=0 ).OnlyEnforceIf(delayed_cost.Not())
            max_val = model.NewIntVar(0, LARGE_INTEGER, f"max_val_{train_index}_{op_index}")
            model.AddMaxEquality(max_val, [0, delay])
            cost = model.NewIntVar(0, LARGE_INTEGER, f"cost_{train_index}_{op_index}")
            model.Add(cost == coeff * max_val + increment * delayed_cost)
            objective_expr += cost

    if objective_components: # Only Minimize if objective is defined
        model.Minimize(objective_expr)

    #print(model)
    # 5. Call Constraint Solver
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 600
    status = solver.Solve(model)

    # 6. Process the Solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        events = []
        for train_index, train_operations in enumerate(trains):
            for op_index, op_data in enumerate(train_operations):
                start_time = solver.Value(train_vars[train_index][op_index]["start_time"])
                active = solver.Value(train_vars[train_index][op_index]["active"])
                if active:
                    events.append({"time": start_time, "train": train_index, "operation": op_index})
        events = sorted(events, key=lambda x: x["time"])

        return {
            "objective_value": solver.ObjectiveValue(),
            "events": events,
        }
    else:
        return None  # No solution found
    
