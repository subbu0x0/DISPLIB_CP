def add_start_lb(train_operations):
    start_lb_operations = {}
    for op_index, op_data in enumerate(train_operations):
        min_duration = op_data.get("min_duration", 0)
        successors = op_data.get("successors", []) 
        if op_index == 0:
            start_lb_operations[op_index] = op_data.get("start_lb", 0)
        start_lb = start_lb_operations[op_index]
        for succ in successors:
            start_lb_succ = train_operations[succ].get("start_lb", 0)
            start_lb_operations[succ] = max(start_lb_succ,start_lb + min_duration)
        if len(successors) == 0:
            return start_lb_operations