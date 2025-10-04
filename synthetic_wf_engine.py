"""
Synthetic Workflow Simulator (Synthetic-WF)
A custom mini-workflow engine implementing all plan requirements.
"""
import json
import subprocess
import threading
import time
from collections import deque
from abc import ABC, abstractmethod


# ============================================================================
# MODELS
# ============================================================================

class Step:
    """Represents a single step in the workflow."""
    
    def __init__(self, step_id: str, command: str):
        self.id = step_id
        self.command = command
        self.dependencies = []
        self.condition = None
        self.failure_strategy = None
        self.parallel_with = []  # Hint for parallel execution
        self.status = "PENDING"  # PENDING, READY, RUNNING, SUCCESS, FAILED, SKIPPED
        self.retry_count = 0


class Workflow:
    """Represents the entire workflow as a graph structure."""
    
    def __init__(self, name: str):
        self.name = name
        self.steps = {}  # Dictionary of step_id to Step objects
        self.inverse_dependencies = {}  # Dictionary of step_id to list of dependent steps
    
    def add_step(self, step: Step):
        """Add a step to the workflow."""
        self.steps[step.id] = step
        self.inverse_dependencies[step.id] = []
    
    def add_dependency(self, dependent_id: str, dependency_id: str):
        """Add a dependency between steps."""
        if dependent_id in self.steps and dependency_id in self.steps:
            self.steps[dependent_id].dependencies.append(dependency_id)
            self.inverse_dependencies[dependency_id].append(dependent_id)


# ============================================================================
# DSL PARSER
# ============================================================================

def parse_workflow(file_path: str) -> Workflow:
    """Parse a workflow definition file and return a Workflow object."""
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Support both formats: {"workflow": "name", "steps": [...]} and [...]
    workflow_name = "default"
    if isinstance(data, dict):
        workflow_name = data.get("workflow", "default")
        if "steps" in data:
            data = data["steps"]
        else:
            raise ValueError("No steps found in workflow definition")
    
    workflow = Workflow(workflow_name)
    
    # First pass: Create all steps
    for step_def in data:
        step_id = step_def["step_id"]
        command = step_def["run"]
        
        step = Step(step_id, command)
        
        # Add optional attributes
        if "if" in step_def:
            step.condition = step_def["if"]
        if "on_failure" in step_def:
            step.failure_strategy = step_def["on_failure"]
        if "parallel_with" in step_def:
            step.parallel_with = step_def["parallel_with"]
        
        workflow.add_step(step)
    
    # Second pass: Add dependencies
    for step_def in data:
        step_id = step_def["step_id"]
        if "depends_on" in step_def:
            for dep_id in step_def["depends_on"]:
                workflow.add_dependency(step_id, dep_id)
    
    return workflow


def validate_workflow(workflow: Workflow) -> bool:
    """Validate workflow structure for cycles."""
    visited = set()
    temp_visited = set()
    
    def has_cycle(step_id):
        if step_id in temp_visited:
            return True
        if step_id in visited:
            return False
        
        temp_visited.add(step_id)
        step = workflow.steps[step_id]
        
        for dep_id in step.dependencies:
            if has_cycle(dep_id):
                return True
        
        temp_visited.remove(step_id)
        visited.add(step_id)
        return False
    
    for step_id in workflow.steps:
        if has_cycle(step_id):
            raise ValueError(f"Cycle detected in workflow involving step {step_id}")
    
    return True


# ============================================================================
# SCHEDULING STRATEGIES
# ============================================================================

class SchedulingStrategy(ABC):
    """Abstract base class for scheduling strategies."""
    
    @abstractmethod
    def get_next_steps(self, ready_steps: list) -> list:
        """Return the next steps to execute based on the strategy."""
        pass


def _calculate_levels(workflow: Workflow):
    """Calculate depth level for each step."""
    levels = {}
    
    def get_level(step_id):
        if step_id in levels:
            return levels[step_id]
        
        step = workflow.steps[step_id]
        if not step.dependencies:
            levels[step_id] = 0
        else:
            levels[step_id] = 1 + max(get_level(dep) for dep in step.dependencies)
        
        return levels[step_id]
    
    for step_id in workflow.steps:
        get_level(step_id)
    
    return levels


class BreadthFirstStrategy(SchedulingStrategy):
    """Breadth-first execution strategy - processes by levels."""
    
    def __init__(self, workflow: Workflow):
        self.levels = _calculate_levels(workflow)
    
    def get_next_steps(self, ready_steps: list) -> list:
        if not ready_steps:
            return []
        # Sort by level (shallower first)
        return [min(ready_steps, key=lambda s: self.levels[s.id])]


class DepthFirstStrategy(SchedulingStrategy):
    """Depth-first execution strategy - prioritizes deeper paths."""
    
    def __init__(self, workflow: Workflow):
        self.levels = _calculate_levels(workflow)
    
    def get_next_steps(self, ready_steps: list) -> list:
        if not ready_steps:
            return []
        # Sort by level (deeper first)
        return [max(ready_steps, key=lambda s: self.levels[s.id])]


# ============================================================================
# WORKFLOW ENGINE
# ============================================================================

class WorkflowEngine:
    """Engine for executing workflow graphs."""
    
    def __init__(self, workflow: Workflow, strategy=None, max_parallel=1):
        self.workflow = workflow
        self.ready_queue = deque()
        self.strategy = strategy
        self.max_parallel = max_parallel
        self.running_threads = []
        self.lock = threading.Lock()
        self.execution_order = []
    
    def execute(self):
        """Execute the workflow."""
        print(f"Starting workflow: {self.workflow.name}")
        self._update_ready_queue()
        
        if self.max_parallel == 1:
            self._execute_sequential()
        else:
            self._execute_parallel()
        
        print(f"Completed workflow: {self.workflow.name}")
        print("Execution order:", " -> ".join(self.execution_order))
    
    def _get_next_step(self):
        """Get next step to execute based on strategy."""
        if self.strategy:
            ready_steps = list(self.ready_queue)
            next_steps = self.strategy.get_next_steps(ready_steps)
            return next_steps[0] if next_steps else None
        return self.ready_queue.popleft() if self.ready_queue else None
    
    def _execute_sequential(self):
        """Execute workflow sequentially."""
        while self.ready_queue:
            step = self._get_next_step()
            if not step:
                break
            
            if step in self.ready_queue:
                self.ready_queue.remove(step)
            
            step.status = "RUNNING"
            success = self._execute_step(step)
            
            if not success and step.status == "FAILED":
                self._skip_dependents(step.id)
            
            self._update_ready_queue()
            self.visualize_workflow()
    
    def _execute_parallel(self):
        """Execute workflow with parallel support."""
        while self.ready_queue or self.running_threads:
            self.running_threads = [t for t in self.running_threads if t.is_alive()]
            
            while (len(self.running_threads) < self.max_parallel and self.ready_queue):
                step = self._get_next_step()
                if not step:
                    break
                
                if step in self.ready_queue:
                    self.ready_queue.remove(step)
                
                step.status = "RUNNING"
                thread = threading.Thread(target=self._execute_step_threaded, args=(step,))
                thread.start()
                self.running_threads.append(thread)
            
            time.sleep(0.1)
            with self.lock:
                self.visualize_workflow()
    
    def _execute_step(self, step: Step) -> bool:
        """Execute a step by running its command."""
        print(f"Starting step {step.id}: {step.command}")
        self.execution_order.append(step.id)
        
        try:
            result = subprocess.run(step.command, shell=True, check=True,
                                  capture_output=True, text=True)
            success = result.returncode == 0
            if result.stdout:
                print(f"[{step.id}] {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            success = False
        
        if success:
            step.status = "SUCCESS"
        else:
            if step.failure_strategy and step.failure_strategy.startswith("retry:"):
                max_retries = int(step.failure_strategy.split(":")[1].strip())
                if step.retry_count < max_retries:
                    step.retry_count += 1
                    step.status = "PENDING"
                    return False
            
            step.status = "FAILED"
        
        return success
    
    def _execute_step_threaded(self, step: Step):
        """Execute a step in a separate thread."""
        success = self._execute_step(step)
        
        with self.lock:
            if not success and step.status == "FAILED":
                self._skip_dependents(step.id)
            self._update_ready_queue()
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a step's condition."""
        if not condition:
            return True
        
        parts = condition.replace("==", " == ").split()
        if len(parts) >= 3:
            var_name = parts[0]
            expected_value = parts[2].strip("'\"")
            
            if var_name.startswith(("status_", "result_")):
                step_id = var_name.split("_", 1)[1]
                if step_id in self.workflow.steps:
                    actual_status = self.workflow.steps[step_id].status
                    return actual_status.lower() == expected_value.lower()
        
        return True
    
    def _update_ready_queue(self):
        """Update the queue of steps ready to execute."""
        for step in self.workflow.steps.values():
            if step.status != "PENDING":
                continue
            
            deps_satisfied = all(
                self.workflow.steps[dep_id].status == "SUCCESS"
                for dep_id in step.dependencies
            )
            
            if deps_satisfied and self._evaluate_condition(step.condition):
                step.status = "READY"
                self.ready_queue.append(step)
            elif deps_satisfied and step.condition and not self._evaluate_condition(step.condition):
                step.status = "SKIPPED"
    
    def _skip_dependents(self, step_id: str):
        """Mark all dependent steps as SKIPPED."""
        to_skip = deque([dep_id for dep_id in self.workflow.inverse_dependencies[step_id]])
        skipped = set()
        
        while to_skip:
            skip_id = to_skip.popleft()
            if skip_id in skipped:
                continue
            
            skip_step = self.workflow.steps[skip_id]
            if skip_step.status in ["PENDING", "READY"]:
                skip_step.status = "SKIPPED"
                skipped.add(skip_id)
                if skip_step in self.ready_queue:
                    self.ready_queue.remove(skip_step)
                to_skip.extend(self.workflow.inverse_dependencies[skip_id])
    
    def visualize_workflow(self):
        """Display current workflow status in a table format."""
        print("\n" + "="*80)
        print(f"{'Step ID':<10} {'Status':<10} {'Dependencies':<15} {'Command':<25} {'Retries':<8}")
        print("-"*80)
        
        for step_id, step in self.workflow.steps.items():
            deps = ", ".join(step.dependencies) if step.dependencies else "N/A"
            deps = deps[:12] + "..." if len(deps) > 15 else deps
            command = step.command[:22] + "..." if len(step.command) > 25 else step.command
            
            print(f"{step_id:<10} {step.status:<10} {deps:<15} {command:<25} {step.retry_count:<8}")
        
        print("="*80)


# ============================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================

def run_workflow(file_path: str, strategy_name: str = "bfs", parallel: bool = False):
    """Main function to run a workflow with specified strategy."""
    
    # Parse and validate workflow
    workflow = parse_workflow(file_path)
    validate_workflow(workflow)
    
    # Choose strategy
    strategy = None
    if strategy_name.lower() == "bfs":
        strategy = BreadthFirstStrategy(workflow)
    elif strategy_name.lower() == "dfs":
        strategy = DepthFirstStrategy(workflow)
    
    # Create and run engine
    max_parallel = 3 if parallel else 1
    engine = WorkflowEngine(workflow, strategy, max_parallel)
    engine.execute()
    
    # Show final status
    print("\nFinal status:")
    for step_id, step in workflow.steps.items():
        print(f"Step {step_id}: {step.status}")


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_strategies():
    """Test different scheduling strategies."""
    print("=== Testing BFS Strategy ===")
    run_workflow("example_workflow.json", "bfs")
    
    print("\n=== Testing DFS Strategy ===")
    run_workflow("example_workflow.json", "dfs")
    
    print("\n=== Testing Parallel Execution ===")
    run_workflow("example_workflow.json", "bfs", parallel=True)
    
    print("\n=== Testing Error Handling ===")
    run_workflow("test_workflow.json", "bfs")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_strategies()
        else:
            run_workflow(sys.argv[1])
    else:
        # Default execution
        run_workflow("example_workflow.json", "bfs")