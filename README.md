# FreeCell Solver

FreeCell Solver is a Python-based implementation of the FreeCell card game integrated with multiple artificial intelligence search algorithms for automatic solving and performance evaluation.

The project supports both manual gameplay and algorithm execution, allowing comparison between classical search strategies under the same game conditions.

## Authors

Group 14 – 24C07

* 24127132 – Nguyễn Thị Ngọc Trâm
* 24127158 – Nguyễn Trần Lan Duy
* 24127262 – Đỗ Thành Vinh
* 24127465 – Tạ Mai Như Ngọc

Course: CSC14003 – Introduction to Artificial Intelligence
Semester II – 2025–2026

## Project Structure

* `main.py` – main entry point of the application
* `Freecell_Game.py` – game logic and move validation
* `BFS_Solver.py` – Breadth-First Search solver
* `IDS_Solver.py` – Iterative Deepening Search solver
* `UCS_Solver.py` – Uniform Cost Search solver
* `A_Star_Solver.py` – A* Search solver
* `utils.py` – utility functions and resource loading
* `test_cases.py` – test scenarios for algorithm evaluation

## Requirements

Install dependencies before running the project:

```bash id="x8n3q1"
pip install -r requirements.txt
```

Required packages:

```txt id="f1m2d7"
pygame
psutil
```

## How to Run Source Code

### Step 1: Prepare resources

Make sure the `images/` folder contains all required card images and background files.

Example:

* `hearts1.png`
* `clubs10.png`
* `diamonds13.png`
* `background.png`

### Step 2: Run the program

Execute:

```bash id="z7p4c2"
python main.py
```

### Step 3: Use the game

* Drag and drop cards for manual play

* Select **Solver** to choose an algorithm

* Available algorithms:

  * BFS
  * IDS
  * UCS
  * A*

* Use **Seed** to generate a specific board

* Use **Undo** to revert moves

* Use **Stop** to interrupt solver execution

## Output

Solver performance is saved automatically in:

```txt id="q5v8n1"
log.txt
```

Recorded metrics include:

* execution time
* explored states
* memory usage
* solution length

## Notes

* Python 3.x is required
* Missing image assets may cause runtime errors
* `psutil` is required for memory measurement
