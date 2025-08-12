# LTM Validation Pipeline

An experimental pipeline to validate Phase 1 of a Long-Term Memory (LTM) system for coding assistants. This system extracts rules from conversations, decides which to store, and measures their effectiveness in reducing behavioral drift.

## Overview

The pipeline consists of four independent test stages:

1. **Rule Extraction** - Extract candidate rules from transcripts
2. **Storage Decision** - Decide which rules to store in LTM
3. **Retrieval & Application** - Test rule retrieval and application
4. **Drift Reduction** - Measure consistency improvements

## Quick Start

### Installation

```bash
# Clone the repository
cd Roo-Code-Experiments

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Generate Test Data

```bash
# Generate complete dataset
python scripts/generate_data.py --output data/synthetic --seed 42

# Generate specific data types
python scripts/generate_data.py --output data/synthetic --type transcripts --num-transcripts 20
python scripts/generate_data.py --output data/synthetic --type tasks --num-tasks 30
```

### Run the Pipeline

```bash
# Run full pipeline
python scripts/run_pipeline.py \
    --stage all \
    --config config/pipeline_config.json \
    --input data/synthetic \
    --output data/results

# Run individual stages
python scripts/run_pipeline.py \
    --stage extract \
    --config config/pipeline_config.json \
    --input data/synthetic/transcripts/transcript_001.json \
    --output data/results/extracted_rules.json
```

### Evaluate Results

```bash
# Generate summary report
python scripts/evaluate_results.py \
    --results data/results \
    --action summary

# Generate visualizations
python scripts/evaluate_results.py \
    --results data/results \
    --action plot-drift \
    --output data/results/drift_plot.png

# Export metrics to CSV
python scripts/evaluate_results.py \
    --results data/results \
    --action export-csv \
    --output data/results/metrics.csv
```

## Architecture

### Module Structure

```
ltm_pipeline/
├── rule_extraction/       # Extract rules from transcripts
│   ├── extractor.py      # Rule extraction logic
│   └── evaluator.py      # Extraction performance evaluation
├── storage_decision/      # Decide which rules to store
│   ├── decision_maker.py # Storage decision logic
│   ├── criteria.py       # Evaluation criteria
│   └── evaluator.py      # Decision performance evaluation
├── retrieval_application/ # Retrieve and apply rules
│   ├── ltm_storage.py    # Simulated LTM storage
│   ├── retriever.py      # Rule retrieval logic
│   ├── applicator.py     # Rule application logic
│   └── evaluator.py      # Retrieval/application evaluation
├── drift_reduction/       # Measure consistency improvements
│   ├── consistency_checker.py # Consistency metrics
│   ├── task_runner.py    # Task execution with/without rules
│   └── evaluator.py      # Drift reduction evaluation
└── common/               # Shared utilities
    ├── models.py         # Data models
    ├── metrics.py        # Metrics collection
    └── logger.py         # Structured logging
```

### Data Flow

1. **Input**: Transcripts containing mixed content (rules + chatter)
2. **Rule Extraction**: Identify and extract candidate rules
3. **Storage Decision**: Evaluate rules against criteria
4. **LTM Storage**: Store approved rules with indexing
5. **Retrieval**: Find relevant rules for tasks
6. **Application**: Apply rules to modify task execution
7. **Evaluation**: Measure drift reduction

## Configuration

The pipeline is configured via `config/pipeline_config.json`:

```json
{
  "extraction": {
    "patterns": {...},           // Regex patterns for rule extraction
    "confidence_threshold": 0.7  // Minimum confidence for extraction
  },
  "storage_decision": {
    "criteria_weights": {...},   // Weights for storage criteria
    "storage_threshold": 0.7     // Minimum score for storage
  },
  "retrieval": {
    "similarity_threshold": 0.8, // Minimum similarity for retrieval
    "max_rules_per_task": 10     // Maximum rules to retrieve
  },
  "drift_reduction": {
    "metrics": [...],            // Consistency metrics to use
    "improvement_threshold": 0.1 // Significant improvement threshold
  }
}
```

## Evaluation Metrics

### Rule Extraction
- **Precision**: Correct extractions / Total extractions
- **Recall**: Correct extractions / Total ground truth rules
- **F1 Score**: Harmonic mean of precision and recall

### Storage Decision
- **Agreement Rate**: Matching decisions / Total decisions
- **False Positive Rate**: Incorrect stores / Total stores
- **False Negative Rate**: Missed stores / Total should-store

### Retrieval & Application
- **Retrieval Accuracy**: Correct retrievals / Total relevant rules
- **Application Precision**: Correct applications / Total applications
- **Over-application Rate**: Unnecessary applications / Total opportunities

### Drift Reduction
- **Consistency Score**: Similarity between repeated runs
- **Drift Reduction %**: (Drift_without - Drift_with) / Drift_without * 100
- **Style Adherence**: Matching style patterns / Total style checks

## Data Models

### Rule Structure
```python
{
    "id": "rule_001",
    "match_criteria": {
        "type": "pattern|keyword|context",
        "value": "specific matching condition",
        "context": {...}
    },
    "action": {
        "type": "style|naming|structure|behavior",
        "description": "what to do",
        "parameters": {...}
    },
    "rationale": "why this rule exists",
    "confidence": 0.95,
    "source_id": "transcript_id",
    "timestamp": "2025-01-05T12:00:00Z"
}
```

### Transcript Structure
```python
{
    "id": "transcript_001",
    "segments": [
        {
            "speaker": "user|assistant",
            "content": "text content",
            "type": "persistent|short_term|irrelevant",
            "timestamp": "2025-01-05T12:00:00Z"
        }
    ],
    "session_id": "session_001",
    "duration": 1800,
    "tags": ["naming_conventions", "javascript"]
}
```

### Task Structure
```python
{
    "id": "task_001",
    "type": "code_generation|refactoring|debugging",
    "language": "JavaScript|Python|etc",
    "description": "Task description",
    "context": {
        "variables_needed": [...],
        "requirements": [...]
    },
    "expected_rules": ["rule_001", "rule_002"]
}
```

## Advanced Usage

### Custom Rule Patterns

Add custom extraction patterns in the configuration:

```json
{
  "extraction": {
    "patterns": {
      "custom_rule": "(?i)my_custom_pattern\\s+(\\w+)",
      ...
    }
  }
}
```

### Storage Criteria Weights

Adjust criteria importance for storage decisions:

```json
{
  "storage_decision": {
    "criteria_weights": {
      "cross_session_value": 0.4,    // Increase for persistent rules
      "stability": 0.2,              // Increase for stable rules
      "clear_triggers": 0.2,         // Increase for clear patterns
      "reduces_inconsistency": 0.2   // Increase for consistency
    }
  }
}
```

### Batch Processing

Process multiple transcripts efficiently:

```python
from ltm_pipeline import LTMPipeline

pipeline = LTMPipeline("config/pipeline_config.json")
results = pipeline.run_full_pipeline("data/synthetic", "data/results")
```

## Troubleshooting

### Common Issues

1. **Low Extraction Precision**
   - Review extraction patterns in config
   - Check transcript quality and formatting
   - Adjust confidence threshold

2. **Poor Storage Decisions**
   - Review criteria weights
   - Check ground truth labels
   - Analyze false positives/negatives

3. **Low Drift Reduction**
   - Ensure rules are being retrieved correctly
   - Check rule applicability to tasks
   - Review consistency metrics

### Debugging

Enable debug logging:

```json
{
  "logging": {
    "level": "DEBUG",
    "output_dir": "data/logs"
  }
}
```

View logs:
```bash
tail -f data/logs/LTMPipeline_*.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This is an experimental project for validating LTM concepts.

## Contact

For questions or issues, please open a GitHub issue.