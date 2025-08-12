# LTM Pipeline Usage Guide

This guide provides detailed instructions for using each component of the LTM validation pipeline.

## Table of Contents

1. [Installation](#installation)
2. [Data Generation](#data-generation)
3. [Running Individual Stages](#running-individual-stages)
4. [Full Pipeline Execution](#full-pipeline-execution)
5. [Results Analysis](#results-analysis)
6. [Advanced Configuration](#advanced-configuration)
7. [API Usage](#api-usage)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) Virtual environment

### Setup Steps

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd Roo-Code-Experiments
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Verify installation
python -c "from ltm_pipeline import LTMPipeline; print('Installation successful!')"
```

## Data Generation

### Generate Complete Dataset

```bash
python scripts/generate_data.py \
    --output data/synthetic \
    --seed 42
```

This creates:
- 15 synthetic transcripts with ground truth rules
- 20 test tasks for retrieval/application testing
- Example rules for testing
- Ground truth storage decisions

### Generate Specific Data Types

#### Transcripts Only
```bash
python scripts/generate_data.py \
    --output data/synthetic \
    --type transcripts \
    --num-transcripts 25 \
    --seed 42
```

#### Tasks Only
```bash
python scripts/generate_data.py \
    --output data/synthetic \
    --type tasks \
    --num-tasks 30 \
    --seed 42
```

#### Example Rules
```bash
python scripts/generate_data.py \
    --output data/synthetic \
    --type rules \
    --seed 42
```

### Data Directory Structure

```
data/synthetic/
├── transcripts/              # Synthetic conversation transcripts
│   ├── transcript_001.json
│   ├── transcript_002.json
│   └── ...
├── ground_truth/            # Ground truth for evaluation
│   ├── transcript_001_rules.json
│   ├── transcript_002_rules.json
│   └── storage_decisions_ground_truth.json
├── test_tasks/              # Tasks for testing
│   ├── tasks.json           # All test tasks
│   └── drift_tasks.json     # Tasks for drift testing
├── example_rules/           # Example rules
│   └── example_rules.json
└── dataset_summary.json     # Dataset statistics
```

## Running Individual Stages

### Stage 1: Rule Extraction

Extract rules from a single transcript:

```bash
python scripts/run_pipeline.py \
    --stage extract \
    --config config/pipeline_config.json \
    --input data/synthetic/transcripts/transcript_001.json \
    --output data/results/extracted_rules.json
```

Output format:
```json
{
  "rules": [
    {
      "id": "rule_abc123",
      "match_criteria": {...},
      "action": {...},
      "confidence": 0.85
    }
  ]
}
```

### Stage 2: Storage Decision

Evaluate rules for storage:

```bash
python scripts/run_pipeline.py \
    --stage decide \
    --config config/pipeline_config.json \
    --input data/results/extracted_rules.json \
    --output data/results/storage_decisions.json
```

Output format:
```json
{
  "decisions": [
    {
      "rule_id": "rule_abc123",
      "decision": "store",
      "justification": "Score: 0.82 (above threshold 0.7)..."
    }
  ]
}
```

### Stage 3: Retrieval & Application

Test rule retrieval and application:

```bash
python scripts/run_pipeline.py \
    --stage retrieve \
    --config config/pipeline_config.json \
    --input data/synthetic/test_tasks/task_001.json \
    --output data/results/retrieval_result.json
```

Output format:
```json
{
  "retrieved_rules": [...],
  "application_result": {
    "task_id": "task_001",
    "applied_rules": ["rule_123", "rule_456"],
    "modifications": [...],
    "skipped_rules": [],
    "errors": []
  }
}
```

### Stage 4: Drift Reduction

Measure consistency improvement:

```bash
python scripts/run_pipeline.py \
    --stage drift \
    --config config/pipeline_config.json \
    --input data/synthetic/test_tasks/drift_task_001.json \
    --output data/results/drift_result.json
```

Output format:
```json
{
  "task_id": "task_001",
  "drift_metrics": {
    "consistency_without_rules": 0.65,
    "consistency_with_rules": 0.88,
    "drift_reduction_percentage": 35.4
  }
}
```

## Full Pipeline Execution

### Basic Execution

Run all stages sequentially:

```bash
python scripts/run_pipeline.py \
    --stage all \
    --config config/pipeline_config.json \
    --input data/synthetic \
    --output data/results
```

### Output Structure

```
data/results/
├── extraction/
│   ├── extracted_rules.json
│   └── extraction_metrics.json
├── storage_decision/
│   ├── storage_decisions.json
│   └── decision_metrics.json
├── retrieval_application/
│   ├── retrieval_application_results.json
│   ├── retrieval_metrics.json
│   └── retrieval_report.txt
├── drift_reduction/
│   ├── drift_comparison_results.json
│   ├── drift_metrics.json
│   └── drift_report.txt
└── pipeline_results.json
```

## Results Analysis

### Generate Summary Report

```bash
python scripts/evaluate_results.py \
    --results data/results \
    --action summary \
    --output data/results/summary_report.txt
```

### Visualizations

#### Plot Extraction Performance
```bash
python scripts/evaluate_results.py \
    --results data/results \
    --action plot-extraction \
    --output data/results/extraction_plot.png
```

#### Plot Drift Reduction
```bash
python scripts/evaluate_results.py \
    --results data/results \
    --action plot-drift \
    --output data/results/drift_plot.png
```

### Export Metrics

Export all metrics to CSV:
```bash
python scripts/evaluate_results.py \
    --results data/results \
    --action export-csv \
    --output data/results/all_metrics.csv
```

### Compare Multiple Runs

```bash
python scripts/evaluate_results.py \
    --results data/results_run1 \
    --action compare \
    --compare-with data/results_run2
```

## Advanced Configuration

### Custom Extraction Patterns

Edit `config/pipeline_config.json`:

```json
{
  "extraction": {
    "patterns": {
      "custom_pattern": "(?i)custom\\s+rule\\s+pattern",
      "domain_specific": "(?i)always\\s+use\\s+(\\w+)\\s+for\\s+(\\w+)"
    },
    "confidence_threshold": 0.75
  }
}
```

### Adjust Storage Criteria

```json
{
  "storage_decision": {
    "criteria_weights": {
      "cross_session_value": 0.35,
      "stability": 0.25,
      "clear_triggers": 0.20,
      "reduces_inconsistency": 0.15,
      "specificity": 0.05
    },
    "storage_threshold": 0.65
  }
}
```

### Retrieval Configuration

```json
{
  "retrieval": {
    "similarity_threshold": 0.75,
    "max_rules_per_task": 15,
    "index_update_frequency": 50,
    "cache_size": 500
  }
}
```

### Drift Metrics Configuration

```json
{
  "drift_reduction": {
    "metrics": [
      "naming_consistency",
      "style_consistency",
      "structure_consistency",
      "custom_metric"
    ],
    "consistency_weights": {
      "naming": 0.4,
      "style": 0.3,
      "structure": 0.2,
      "custom": 0.1
    }
  }
}
```

## API Usage

### Python API Example

```python
from ltm_pipeline import LTMPipeline
from ltm_pipeline.common.models import Transcript, Task
from ltm_pipeline.utils.file_io import FileIO

# Initialize pipeline
pipeline = LTMPipeline("config/pipeline_config.json")

# Load transcript
transcript_data = FileIO.read_json("data/synthetic/transcripts/transcript_001.json")
transcript = Transcript.from_dict(transcript_data)

# Extract rules
rules = pipeline.rule_extractor.extract_rules(transcript)
print(f"Extracted {len(rules)} rules")

# Evaluate for storage
decisions = pipeline.storage_decision_maker.evaluate_rules(rules)
approved_rules = [rule for rule, decision, _ in decisions if decision == "store"]

# Store in LTM
pipeline.ltm_storage.store_rules(approved_rules)

# Test retrieval
task_data = FileIO.read_json("data/synthetic/test_tasks/task_001.json")
task = Task.from_dict(task_data)
retrieved_rules = pipeline.rule_retriever.retrieve_for_task(task)

# Apply rules
result = pipeline.rule_applicator.apply_rules_to_task(task, retrieved_rules)
print(f"Applied {len(result.applied_rules)} rules")
```

### Custom Task Executor

```python
from ltm_pipeline.drift_reduction import TaskRunner

def custom_executor(task, rules, application_result=None):
    """Custom task execution logic."""
    output = {
        "task_id": task.id,
        "custom_field": "custom_value"
    }
    
    # Apply rules to modify output
    if application_result:
        for modification in application_result.modifications:
            # Apply modification logic
            pass
    
    return output

# Use custom executor
task_runner = TaskRunner(task_executor=custom_executor)
results = task_runner.run_comparison(task, num_runs=5)
```

### Batch Processing

```python
# Process multiple transcripts
transcripts = []
for file in Path("data/synthetic/transcripts").glob("*.json"):
    data = FileIO.read_json(file)
    transcripts.append(Transcript.from_dict(data))

# Batch extraction
all_rules = []
for transcript in transcripts:
    rules = pipeline.rule_extractor.extract_rules(transcript)
    all_rules.extend(rules)

# Batch evaluation
batch_results = pipeline.storage_decision_maker.batch_evaluate(
    [{"rules": all_rules[i:i+10]} for i in range(0, len(all_rules), 10)]
)
```

## Tips and Best Practices

1. **Data Quality**: Ensure transcripts have clear rule indicators for better extraction
2. **Balanced Datasets**: Include mix of persistent, short-term, and irrelevant content
3. **Ground Truth**: Carefully label ground truth for accurate evaluation
4. **Iterative Tuning**: Start with default configs, then tune based on results
5. **Logging**: Enable DEBUG logging when troubleshooting
6. **Batch Size**: Process in batches for large datasets to manage memory

## Troubleshooting

### Low Extraction Performance
- Check extraction patterns match your domain
- Verify transcript formatting
- Adjust confidence threshold
- Review ground truth labels

### Poor Storage Decisions
- Analyze false positives/negatives
- Adjust criteria weights
- Check if rules meet storage criteria

### Retrieval Issues
- Verify LTM storage has rules
- Check similarity threshold
- Review task descriptions
- Ensure proper indexing

### Minimal Drift Reduction
- Confirm rules are being applied
- Check rule relevance to tasks
- Review consistency metrics
- Verify task execution logic