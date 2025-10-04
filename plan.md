# Synthetic Workflow Simulator (Synthetic-WF) Project Plan

## 1. Project Goal and Scope

The goal of this project is to design and implement a custom mini-workflow engine, Synthetic-WF, in Python. This engine will define, parse, and execute workflows based on a custom Domain Specific Language (DSL), ensuring dependencies, parallel execution, dynamic branching, and specific scheduling strategies are supported.

## 2. Phase 1: Custom DSL Definition and Documentation

**Requirement:** Accept a workflow definition written in a custom DSL. DSL must allow defining steps, dependencies, conditions, and parallel execution. Document the grammar.

### 2.1. Custom DSL Grammar (YAML-like Simple Structure)

To keep the parser simple (no external libraries), the DSL will use a structured, configuration-file-like format, represented as a list of step definitions.

| Element | Format Example | Description |
|---------|----------------|-------------|
| Workflow Block | `workflow: MyProcess` | Defines the workflow name. |
| Step Definition | `step_id: A` | Unique identifier for the step. |
| Execution Command | `run: "python task_a.py"` | The simulated external command to execute. |
| Dependencies | `depends_on: [B, C]` | List of step IDs that must complete successfully first. |
| Parallel Hint (Ignored by engine, but parsed) | `parallel_with: [D]` | A hint for the developer, parsed but functionally covered by dependency structure. |
| Condition (Dynamic Branching) | `if: "status_B == success"` | A condition that must evaluate to true for this step to run. |
| Error Handling | `on_failure: skip_dependents` | Strategy: `retry: N` (e.g., retry: 3) or `skip_dependents`. |

### 2.2. Example DSL Workflow (Input File)

The DSL will be implemented as a simple list of Python dictionaries (or a configuration file that reads into a list of dicts) for maximum simplicity in parsing.

```json
# workflow.wf (Example DSL Content)
[
  {
    "step_id": "A",
    "run": "task1.sh",
    "on_failure": "skip_dependents"
  },
  {
    "step_id": "B",
    "run": "task2.sh",
    "depends_on": ["A"],
    "if": "result_A == 'success'"
  },
  {
    "step_id": "C",
    "run": "task3.sh",
    "depends_on": ["A"],
    "parallel_with": ["D"]
  },
  {
    "step_id": "D",
    "run": "task4.sh"
  },
  {
    "step_id": "E",
    "run": "task5.sh",
    "depends_on": ["B", "C"],
    "on_failure": "retry: 2"
  }
]
```

## 3. Phase 2: Custom DSL Parser and Graph Structure

**Requirements:** Implement your own DSL parser (no external parsing libraries). Parse the workflow DSL into an in-memory graph structure.

### 3.1. Parser Implementation

- **Lexer/Tokenization (Custom):** Implement a function (e.g., `tokenize_dsl`) to read the input DSL file (simulated configuration file or Python dictionary structure) and convert the text/data into structured Python objects (dictionaries/lists). Since the DSL is designed to be dictionary-like, the parser primarily involves structural validation and conversion.
- **Validation:** Ensure all required fields (`step_id`, `run`) are present and dependencies reference existing steps.

### 3.2. In-Memory Graph Structure (Adjacency List)

The parsed data will be converted into a Directed Acyclic Graph (DAG) for execution.

**Node Representation:** A Python class (`Step`) to hold all step attributes:
- `id` (str)
- `command` (str)
- `dependencies` (list of str)
- `condition` (str or None)
- `failure_strategy` (str, e.g., 'skip', 'retry:N')
- `status` (str: PENDING, READY, RUNNING, SUCCESS, FAILED, SKIPPED)
- `retry_count` (int)

**Graph Representation:** A main `Workflow` class using a Python dictionary (adjacency list) where keys are `step_ids` and values are `Step` objects.

**Dependency Tracking:** Maintain an inverse dependency list (steps that depend on the current step) for easy propagation of status.

## 4. Phase 3: Execution Engine & Scheduling

**Requirements:** Execute the workflow, respect dependencies, allow parallel execution (simulated), implement error handling, log execution order. Implement Depth-first and Breadth-first execution strategies. Engine must be built from scratch.

### 4.1. Core Execution Loop

The execution will be driven by a main loop in the `WorkflowEngine` class.

- **Ready Queue:** Maintain a queue of steps that have met all their dependencies and are ready to run (READY status).
- **Execution:** Steps will be "executed" by simulating a task run (e.g., printing the command and setting a simulated status: SUCCESS or FAILED).
- **Status Propagation:** Upon a step's completion, update its status and check all its inverse dependents. If a dependent's prerequisites are all met, move it to the READY queue.

### 4.2. Scheduling Strategies

The core difference between strategies is how steps are added/prioritized in the READY queue.

**Breadth-First (BFS):**
- **Strategy:** Steps are prioritized by their depth/level in the DAG. All steps in a shallower level are executed before moving to the next deeper level.
- **Implementation:** When a step is marked READY, it is appended to the main execution queue (simulating FIFO order based on discovery).

**Depth-First (DFS):**
- **Strategy:** After a step completes, its immediate dependents are prioritized for execution before other steps at the same level.
- **Implementation:** When a step is marked READY, it is prepended to the execution queue (simulating LIFO/Stack behavior on the recently completed path).

### 4.3. Dynamic Branching & Error Handling

**Dynamic Branching (if: condition):** Before moving a step from PENDING to READY, evaluate its `if` condition (e.g., parsing `result_A == 'success'` against a global workflow state). If the condition is false, the step is immediately marked as SKIPPED.

**Error Handling:**
- **Retry:** If a step fails and `on_failure: retry: N` is set, increment the `retry_count` and move the step back to READY status if retry limit not exceeded.
- **Skip Dependents:** If a step fails and `on_failure: skip_dependents` is set, the step is marked FAILED. All of its direct and indirect dependents are immediately marked as SKIPPED.

### 4.4. Logging

Log the `step_id`, status change, and command for every state transition in chronological order to capture the execution flow.

## 5. Phase 4: Visualization (Console-Based)

**Requirement:** Provide a visualizer (console-based).

### 5.1. Real-time Status Viewer

Implement a function (`visualize_workflow`) that prints the current state of the workflow graph at key checkpoints (e.g., after every simulated step completion).

| Step ID | Status | Dependencies Met | Command | Retries |
|---------|--------|------------------|---------|----------|
| A | SUCCESS | N/A | task1.sh | 0 |
| B | PENDING | A | task2.sh | 0 |
| C | READY | A | task3.sh | 0 |
| D | RUNNING | N/A | task4.sh | 0 |
| E | PENDING | B, C | task5.sh | 0 |

### 5.2. Execution Log Output

At the end of the simulation, print the final chronological execution log gathered in Phase 3.

## 6. Phase 5: Deliverables and Testing

**Requirements:** Source code, DSL documentation, example workflows and results, visualization.

### 6.1. Deliverables Checklist

| Deliverable | Description | Status |
|-------------|-------------|--------|
| Source Code | Complete Python files implementing the parser, engine, and visualization. | PENDING |
| DSL Documentation | Formal description of the custom grammar (similar to Section 2.1). | PENDING |
| Example Workflows | Two different .wf files demonstrating: dependencies, parallel steps, conditions, and error handling. | PENDING |
| Execution Results | Output logs for both BFS and DFS strategies on the example workflows. | PENDING |
| Visualization | Console output showing the status table and execution log. | PENDING |

### 6.2. Testing Plan

**Test 1 (Dependency & Parallel):** Run a workflow with independent steps (C and D) and chained dependencies (A -> B). Verify A runs first, C and D run in parallel (simultaneously ready), and B runs last.

**Test 2 (DFS vs. BFS):** Run a workflow with A -> B, A -> C.
- **BFS:** Should execute A, then B and C are prioritized equally based on level.
- **DFS:** Should execute A, then B runs first if B was the first dependent discovered/added to the ready list from A.

**Test 3 (Error Handling & Branching):** Run a workflow where Step X fails (triggering a retry) and Step Y's condition is false (triggering a skip). Verify the correct status propagation (e.g., dependents of a FAILED step are SKIPPED).

## Final Project Structure (Python)

The solution will be implemented in a single Python script (`synthetic_wf_engine.py`) containing the required classes and logic.

```
synthetic_wf_engine.py
├── Step Class (Node definition)
├── Workflow Class (DAG structure and management)
├── DSLParser Function (Custom parser)
└── WorkflowEngine Class
    ├── run_workflow (Main execution loop)
    ├── execute_step (Simulates task run, handles retry/fail)
    ├── schedule_bfs (Prioritizes queue for BFS)
    ├── schedule_dfs (Prioritizes queue for DFS)
    └── visualize_workflow (Console output)
```
