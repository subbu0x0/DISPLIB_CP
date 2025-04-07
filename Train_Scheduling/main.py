# Load problem instance (replace with your file path if needed)
from train_scheduling import solve_displib_problem
import os
import json
import glob
import traceback


def process_problem_files(directory_path):
    # Logging setup
    log_file = os.path.join(directory_path, 'solve_log.txt')
    
    # Create solutions directory
    solutions_dir = os.path.join(directory_path, 'solutions')
    os.makedirs(solutions_dir, exist_ok=True)
    
    # Open log file
    with open(log_file, 'w') as log:
        # Find all JSON problem files
        problem_files = glob.glob(os.path.join(directory_path, '*.json'))
        
        # Track results
        total_problems = len(problem_files)
        solved_problems = 0
        failed_problems = 0
        
        # Process each problem file
        for file_path in problem_files:
            try:
                # Skip solution files if they exist
                if '_solution' in file_path:
                    continue
                
                # Read problem file
                with open(file_path, 'r') as f:
                    problem_data = json.load(f)
                
                # Solve the problem
                solution = solve_displib_problem(problem_data)
                
                # Generate solution filename
                file_name = os.path.basename(file_path).split('.')[0] + '_solution.json'
                solution_path = os.path.join(solutions_dir, file_name)
                
                # Save solution
                with open(solution_path, "w") as json_file:
                    json.dump(solution, json_file, indent=4)
                
                # Log success
                log.write(f"Solved: {file_path}\n")
                solved_problems += 1
                print(f"Solved: {file_path}")
            
            except Exception as e:
                # Log error details
                log.write(f"Failed: {file_path}\n")
                log.write(f"Error: {str(e)}\n")
                log.write(f"Traceback:\n{traceback.format_exc()}\n\n")
                failed_problems += 1
                print(f"Failed to solve: {file_path}")
        
        # Summary log
        log.write("\n--- SUMMARY ---\n")
        log.write(f"Total Problems: {total_problems}\n")
        log.write(f"Solved: {solved_problems}\n")
        log.write(f"Failed: {failed_problems}\n")
    
    print("Batch solving complete. Check solve_log.txt for details.")

# Run the batch solver

directory_path = 'Train_Scheduling/Phase1'
process_problem_files(directory_path)