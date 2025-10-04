# Synthetic Workflow Simulator (Synthetic-WF)

## Project Status: ✅ COMPLETED (All Plan Requirements Met)

This project implements a custom mini-workflow engine in Python that defines, parses, and executes workflows based on a custom Domain Specific Language (DSL).

## ✅ Implemented Features

### 1. Custom DSL Parser
- **JSON-based DSL** for workflow definitions
- **Validation** of workflow structure and dependencies
- **Cycle detection** to ensure DAG structure

### 2. Core Engine
- **Step execution** with command simulation
- **Dependency management** with proper ordering
- **Status tracking** (PENDING, READY, RUNNING, SUCCESS, FAILED, SKIPPED)
- **Dynamic branching** with condition evaluation
- **Error handling** with retry and skip strategies

### 3. Scheduling Strategies
- **Breadth-First Strategy** - processes steps level by level
- **Depth-First Strategy** - prioritizes deeper dependencies first
- **Parallel Strategy** - controls maximum parallel execution

### 4. Visualization
- **Real-time status viewer** showing workflow state
- **Console-based table** with step details
- **Execution logging** with chronological order

### 5. Error Handling
- **Retry mechanism** with configurable retry counts
- **Skip dependents** strategy for failed steps
- **Condition-based execution** for dynamic branching

### 6. Parallel Execution
- **True parallel execution** using threading
- **Concurrent step processing** for independent steps
- **Thread-safe status updates** with proper locking

## 🚀 How to Run

### Basic Execution
```bash
python synthetic_wf_engine.py
```

### Test Different Strategies
```bash
python synthetic_wf_engine.py test
```

### Run Specific Workflow
```bash
python synthetic_wf_engine.py example_workflow.json
```

## 📁 Project Structure

```
assignment_1/
├── synthetic_wf_engine.py      # Complete implementation (single file)
├── example_workflow.json       # Example workflow
├── test_workflow.json         # Error handling test
├── plan.md                    # Original project plan
└── README.md                  # This file
```

## 📋 DSL Format

The workflow DSL uses JSON format:

```json
{
  "workflow": "WorkflowName",
  "steps": [
    {
      "step_id": "A",
      "run": "echo 'Running task A'",
      "on_failure": "skip_dependents"
    },
    {
      "step_id": "B",
      "run": "echo 'Running task B'",
      "depends_on": ["A"],
      "if": "status_A == 'success'"
    }
  ]
}
```

### Supported Fields
- `step_id`: Unique identifier
- `run`: Command to execute
- `depends_on`: List of dependency step IDs
- `if`: Condition for execution
- `on_failure`: Error handling strategy (`skip_dependents` or `retry: N`)
- `parallel_with`: Hint for parallel execution

## 🧪 Test Results

### Example Workflow Execution
```
Step ID    Status     Dependencies    Command                   Retries 
A          SUCCESS    N/A             echo 'Running task A'     0       
B          SUCCESS    A               echo 'Running task B'     0       
C          SUCCESS    A               echo 'Running task C'     0       
D          SUCCESS    N/A             echo 'Running task D'     0       
E          SUCCESS    B, C            echo 'Running task E'     0       
```

### Execution Order
- **BFS**: A → D → B → C → E
- **DFS**: A → B → C → E → D

### Error Handling
- Retry mechanism works correctly (2 retries for failed step)
- Dependencies are properly blocked when parent fails
- Conditions are evaluated correctly

## ✅ Plan Requirements Met

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Custom DSL | ✅ | JSON-based format with all required fields |
| DSL Parser | ✅ | Custom parser with validation and cycle detection |
| Graph Structure | ✅ | DAG with adjacency list and inverse dependencies |
| Execution Engine | ✅ | Complete engine with dependency handling |
| BFS/DFS Strategies | ✅ | Both strategies implemented and tested |
| Dynamic Branching | ✅ | Condition evaluation with status checking |
| Error Handling | ✅ | Retry and skip_dependents strategies |
| Logging | ✅ | Comprehensive logging with execution order |
| Visualization | ✅ | Console-based status table |
| Testing | ✅ | Multiple test workflows with different scenarios |
| Single File | ✅ | All functionality in `synthetic_wf_engine.py` |

## 🎯 Key Features Demonstrated

1. **Dependency Resolution**: Steps execute in correct order based on dependencies
2. **Parallel Execution**: Independent steps (A and D) can run simultaneously
3. **Dynamic Branching**: Step B only runs if Step A succeeds
4. **Error Handling**: Step C retries on failure, Step D is blocked if C fails
5. **Scheduling**: Different strategies produce different execution orders
6. **Visualization**: Real-time status updates during execution
7. **Logging**: Complete execution history with timestamps

The implementation successfully meets all requirements from the original plan and provides a fully functional workflow engine with comprehensive features in a single, simple file.