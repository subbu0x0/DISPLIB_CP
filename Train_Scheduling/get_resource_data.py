def get_resource_data(trains):
    resource_vars = {}
    min_duration_trains = []
    release_time_resources = {}
    for train_index, train_operations in enumerate(trains):
        min_duration = 0
        for op_index, op_data in enumerate(train_operations):
            resources = op_data.get("resources", [])
            min_duration += op_data.get("min_duration", 0)
            for resource_data in resources:
                resource = resource_data["resource"]
                release_time = resource_data.get("release_time", 0)
                if resource not in release_time_resources:
                    release_time_resources[resource] = release_time
                if resource not in resource_vars:
                    resource_vars[resource] = []
                resource_vars[resource].append({
                    "train": train_index,
                    "operation": op_index,
                })
        min_duration_trains.append(min_duration)
    return min_duration_trains, release_time_resources, resource_vars