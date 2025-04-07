def add_predecessors(trains):
    """Add predecessor information to each operation based on successors."""
    for train_index, train_operations in enumerate(trains):
        for op_index, op_data in enumerate(train_operations):
            trains[train_index][op_index]["predecessors"] = []
    for train_index, train_operations in enumerate(trains):
        for op_index, op_data in enumerate(train_operations):          
            successors = op_data.get("successors", [])
            for succ_op in successors:
                # Assign the current operation as the predecessor of its successors
                trains[train_index][succ_op]["predecessors"].append(op_index)
    return trains