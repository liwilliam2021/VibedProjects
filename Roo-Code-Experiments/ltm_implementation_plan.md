# LTM Pipeline Implementation Plan

## Phase 1: Core Infrastructure

### 1.1 Common Models and Utilities

#### Data Models (`ltm_pipeline/common/models.py`)
```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class RuleType(Enum):
    PERSISTENT = "persistent"
    SHORT_TERM = "short_term"
    IRRELEVANT = "irrelevant"

class MatchType(Enum):
    PATTERN = "pattern"
    KEYWORD = "keyword"
    CONTEXT = "context"

class ActionType(Enum):
    STYLE = "style"
    NAMING = "naming"
    STRUCTURE = "structure"
    BEHAVIOR = "behavior"

@dataclass
class MatchCriteria:
    type: MatchType
    value: str
    context: Optional[Dict[str, Any]] = None

@dataclass
class Action:
    type: ActionType
    description: str
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class Rule:
    id: str
    match_criteria: MatchCriteria
    action: Action
    rationale: str
    confidence: float = 1.0
    source_id: Optional[str] = None
    timestamp: datetime = None
    
@dataclass
class TranscriptSegment:
    speaker: str  # "user" or "assistant"
    content: str
    type: RuleType
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Transcript:
    id: str
    segments: List[TranscriptSegment]
    session_id: str
    duration: int  # seconds
    tags: List[str]
```

#### Metrics Framework (`ltm_pipeline/common/metrics.py`)
```python
from dataclasses import dataclass
from typing import Dict, List, Any
import json
from datetime import datetime

@dataclass
class MetricResult:
    metric_name: str
    value: float
    metadata: Dict[str, Any]
    timestamp: datetime

class MetricsCollector:
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.metrics: List[MetricResult] = []
    
    def record(self, metric_name: str, value: float, **metadata):
        """Record a metric with metadata"""
        pass
    
    def calculate_precision_recall_f1(self, true_positives: int, 
                                    false_positives: int, 
                                    false_negatives: int) -> Dict[str, float]:
        """Calculate standard classification metrics"""
        pass
    
    def save_metrics(self, filepath: str):
        """Save metrics to JSON file"""
        pass
```

### 1.2 Logging Infrastructure (`ltm_pipeline/common/logger.py`)
```python
import logging
from datetime import datetime
import json

class StructuredLogger:
    def __init__(self, module_name: str, log_dir: str):
        self.module_name = module_name
        self.logger = self._setup_logger(log_dir)
    
    def log_operation(self, operation: str, data: Dict[str, Any], 
                     status: str = "success"):
        """Log structured operation data"""
        pass
    
    def log_error(self, operation: str, error: Exception, context: Dict[str, Any]):
        """Log error with context"""
        pass
```

## Phase 2: Module Implementations

### 2.1 Rule Extraction Module

#### Core Extractor (`ltm_pipeline/rule_extraction/extractor.py`)
```python
from typing import List, Dict, Any
import re
from ..common.models import Rule, Transcript, MatchCriteria, Action

class RuleExtractor:
    def __init__(self, extraction_patterns: Dict[str, str]):
        self.patterns = extraction_patterns
        self.rule_indicators = [
            "always", "never", "should", "must", "prefer",
            "convention", "standard", "format", "style"
        ]
    
    def extract_rules(self, transcript: Transcript) -> List[Rule]:
        """Extract candidate rules from transcript"""
        rules = []
        for segment in transcript.segments:
            if self._contains_rule_indicator(segment.content):
                rule = self._parse_rule(segment)
                if rule:
                    rules.append(rule)
        return rules
    
    def _contains_rule_indicator(self, text: str) -> bool:
        """Check if text likely contains a rule"""
        pass
    
    def _parse_rule(self, segment: TranscriptSegment) -> Optional[Rule]:
        """Parse a segment into a rule"""
        pass
```

#### Evaluator (`ltm_pipeline/rule_extraction/evaluator.py`)
```python
class ExtractionEvaluator:
    def evaluate(self, extracted: List[Rule], ground_truth: List[Rule]) -> Dict[str, float]:
        """Evaluate extraction performance"""
        # Match rules based on similarity
        # Calculate precision, recall, F1
        pass
```

### 2.2 Storage Decision Module

#### Decision Maker (`ltm_pipeline/storage_decision/decision_maker.py`)
```python
from typing import List, Tuple
from ..common.models import Rule

class StorageDecisionMaker:
    def __init__(self, criteria_weights: Dict[str, float]):
        self.criteria_weights = criteria_weights
    
    def evaluate_rules(self, rules: List[Rule]) -> List[Tuple[Rule, str, str]]:
        """
        Evaluate rules for storage
        Returns: List of (rule, decision, justification)
        """
        results = []
        for rule in rules:
            score = self._calculate_storage_score(rule)
            decision = "store" if score > 0.7 else "ignore"
            justification = self._generate_justification(rule, score)
            results.append((rule, decision, justification))
        return results
    
    def _calculate_storage_score(self, rule: Rule) -> float:
        """Calculate storage worthiness score"""
        # Evaluate:
        # - Cross-session value
        # - Stability
        # - Clear triggers
        # - Reduces inconsistency
        pass
```

### 2.3 Retrieval & Application Module

#### LTM Storage (`ltm_pipeline/retrieval_application/ltm_storage.py`)
```python
class SimulatedLTMStorage:
    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self.index: Dict[str, List[str]] = {}  # keyword -> rule_ids
    
    def store_rule(self, rule: Rule):
        """Store a rule with indexing"""
        pass
    
    def retrieve_relevant_rules(self, context: Dict[str, Any]) -> List[Rule]:
        """Retrieve rules matching context"""
        pass
```

#### Applicator (`ltm_pipeline/retrieval_application/applicator.py`)
```python
class RuleApplicator:
    def __init__(self, ltm_storage: SimulatedLTMStorage):
        self.storage = ltm_storage
    
    def apply_rules_to_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Apply relevant rules to a task"""
        relevant_rules = self.storage.retrieve_relevant_rules(task)
        results = {
            "task": task,
            "applied_rules": [],
            "modifications": []
        }
        
        for rule in relevant_rules:
            if self._should_apply_rule(rule, task):
                modification = self._apply_rule(rule, task)
                results["applied_rules"].append(rule.id)
                results["modifications"].append(modification)
        
        return results
```

### 2.4 Drift Reduction Module

#### Consistency Checker (`ltm_pipeline/drift_reduction/consistency_checker.py`)
```python
class ConsistencyChecker:
    def __init__(self, similarity_metrics: List[str]):
        self.metrics = similarity_metrics
    
    def compare_outputs(self, output1: Dict[str, Any], 
                       output2: Dict[str, Any]) -> Dict[str, float]:
        """Compare two outputs for consistency"""
        scores = {}
        
        # Check naming conventions
        scores["naming_consistency"] = self._check_naming_consistency(output1, output2)
        
        # Check style adherence
        scores["style_consistency"] = self._check_style_consistency(output1, output2)
        
        # Check structural similarity
        scores["structure_consistency"] = self._check_structure_consistency(output1, output2)
        
        return scores
```

## Phase 3: Data Generation and Testing

### 3.1 Synthetic Data Generator (`ltm_pipeline/utils/data_generator.py`)
```python
class SyntheticDataGenerator:
    def generate_transcript(self, rule_mix: Dict[str, float]) -> Transcript:
        """Generate synthetic transcript with specified rule mix"""
        pass
    
    def generate_test_task(self, rule_types: List[str]) -> Dict[str, Any]:
        """Generate test task that should trigger specific rules"""
        pass
    
    def generate_ground_truth(self, transcript: Transcript) -> List[Rule]:
        """Generate ground truth rules for a transcript"""
        pass
```

### 3.2 Pipeline Runner (`scripts/run_pipeline.py`)
```python
#!/usr/bin/env python3
import argparse
from ltm_pipeline import (
    RuleExtractor, StorageDecisionMaker, 
    SimulatedLTMStorage, RuleApplicator,
    ConsistencyChecker, MetricsCollector
)

def run_full_pipeline(config_path: str):
    """Run complete pipeline with all stages"""
    # Load configuration
    # Initialize modules
    # Run each stage
    # Collect and report metrics
    pass

def run_single_stage(stage: str, input_path: str, output_path: str):
    """Run a single pipeline stage"""
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["all", "extract", "decide", "retrieve", "drift"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    if args.stage == "all":
        run_full_pipeline(args.config)
    else:
        run_single_stage(args.stage, args.input, args.output)
```

## Phase 4: Example Datasets

### 4.1 Synthetic Transcript Example
```json
{
    "id": "transcript_001",
    "segments": [
        {
            "speaker": "user",
            "content": "I always use camelCase for JavaScript variables",
            "type": "persistent",
            "timestamp": "2025-01-05T10:00:00Z"
        },
        {
            "speaker": "assistant",
            "content": "I'll follow the camelCase convention for all JavaScript variables",
            "type": "persistent",
            "timestamp": "2025-01-05T10:00:05Z"
        },
        {
            "speaker": "user",
            "content": "For this specific function, use snake_case",
            "type": "short_term",
            "timestamp": "2025-01-05T10:00:10Z"
        },
        {
            "speaker": "user",
            "content": "The weather is nice today",
            "type": "irrelevant",
            "timestamp": "2025-01-05T10:00:15Z"
        }
    ],
    "session_id": "session_001",
    "duration": 1800,
    "tags": ["naming_conventions", "javascript"]
}
```

### 4.2 Ground Truth Rules Example
```json
[
    {
        "id": "rule_001",
        "match_criteria": {
            "type": "pattern",
            "value": "javascript.*variable"
        },
        "action": {
            "type": "naming",
            "description": "Use camelCase for JavaScript variables"
        },
        "rationale": "User preference for JavaScript naming convention",
        "confidence": 0.95
    }
]
```

### 4.3 Test Task Example
```json
{
    "id": "task_001",
    "type": "code_generation",
    "language": "javascript",
    "description": "Create a function to calculate user statistics",
    "context": {
        "variables_needed": ["userName", "userAge", "totalScore"],
        "existing_code": "function getUserData() { ... }"
    }
}
```

## Phase 5: Configuration

### Pipeline Configuration (`config/pipeline_config.json`)
```json
{
    "extraction": {
        "patterns": {
            "naming_rule": "(?i)(always|must|should)\\s+use\\s+(\\w+Case)",
            "style_rule": "(?i)(prefer|convention|standard)\\s+(.+)"
        },
        "confidence_threshold": 0.7
    },
    "storage_decision": {
        "criteria_weights": {
            "cross_session_value": 0.4,
            "stability": 0.3,
            "clear_triggers": 0.2,
            "reduces_inconsistency": 0.1
        },
        "storage_threshold": 0.7
    },
    "retrieval": {
        "similarity_threshold": 0.8,
        "max_rules_per_task": 10
    },
    "drift_reduction": {
        "metrics": ["naming_consistency", "style_consistency", "structure_consistency"],
        "improvement_threshold": 0.1
    },
    "logging": {
        "level": "INFO",
        "format": "json",
        "output_dir": "data/logs"
    }
}
```

## Implementation Timeline

1. **Week 1**: Core infrastructure (models, metrics, logging)
2. **Week 2**: Rule extraction and storage decision modules
3. **Week 3**: Retrieval/application and drift reduction modules
4. **Week 4**: Data generation, testing, and documentation

## Success Criteria

1. **Rule Extraction**: F1 score > 0.8 on synthetic data
2. **Storage Decision**: Agreement rate > 0.85 with human labels
3. **Retrieval**: Accuracy > 0.9, over-application < 0.1
4. **Drift Reduction**: > 30% improvement in consistency scores