def add_start_ub(train_operations,LARGE_INTEGER):
    start_ub_operations = {}
    length_train = len(train_operations)
    op_index = length_train - 1
    while(op_index):
        op_data = train_operations[op_index]
        predecessors = op_data.get("predecessors", [])
        if op_index == length_train - 1:
            start_ub_operations[op_index] = op_data.get("start_ub", LARGE_INTEGER)
        start_ub = start_ub_operations[op_index]
        for pred in predecessors:
            start_ub_pred = train_operations[pred].get("start_ub", LARGE_INTEGER)
            min_duration_pred = train_operations[pred].get("min_duration", 0)
            start_ub_operations[pred] = min(start_ub_pred,start_ub-min_duration_pred)
        op_index = op_index - 1
    return start_ub_operations