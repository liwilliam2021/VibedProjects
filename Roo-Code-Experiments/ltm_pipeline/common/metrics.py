"""Metrics collection and calculation for the LTM pipeline."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from pathlib import Path
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix


@dataclass
class MetricResult:
    """Container for a single metric result."""
    metric_name: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class MetricsCollector:
    """Collects and manages metrics for a module."""
    
    def __init__(self, module_name: str, output_dir: Optional[str] = None):
        """Initialize metrics collector.
        
        Args:
            module_name: Name of the module collecting metrics
            output_dir: Directory to save metrics (optional)
        """
        self.module_name = module_name
        self.metrics: List[MetricResult] = []
        self.output_dir = Path(output_dir) if output_dir else None
        
    def record(self, metric_name: str, value: float, **metadata) -> None:
        """Record a metric with metadata.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            **metadata: Additional metadata as keyword arguments
        """
        result = MetricResult(
            metric_name=metric_name,
            value=value,
            metadata={
                "module": self.module_name,
                **metadata
            }
        )
        self.metrics.append(result)
        
    def calculate_precision_recall_f1(
        self, 
        true_positives: int, 
        false_positives: int, 
        false_negatives: int
    ) -> Dict[str, float]:
        """Calculate standard classification metrics.
        
        Args:
            true_positives: Number of true positives
            false_positives: Number of false positives
            false_negatives: Number of false negatives
            
        Returns:
            Dictionary with precision, recall, and f1 scores
        """
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Record the metrics
        self.record("precision", precision, 
                   true_positives=true_positives,
                   false_positives=false_positives)
        self.record("recall", recall,
                   true_positives=true_positives,
                   false_negatives=false_negatives)
        self.record("f1_score", f1)
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
    
    def calculate_agreement_rate(
        self,
        predictions: List[str],
        ground_truth: List[str]
    ) -> float:
        """Calculate agreement rate between predictions and ground truth.
        
        Args:
            predictions: List of predicted values
            ground_truth: List of ground truth values
            
        Returns:
            Agreement rate (0-1)
        """
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")
        
        agreements = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
        rate = agreements / len(predictions) if predictions else 0.0
        
        self.record("agreement_rate", rate,
                   total_samples=len(predictions),
                   agreements=agreements)
        
        return rate
    
    def calculate_retrieval_metrics(
        self,
        retrieved: List[str],
        relevant: List[str],
        total_available: int
    ) -> Dict[str, float]:
        """Calculate retrieval metrics.
        
        Args:
            retrieved: List of retrieved item IDs
            relevant: List of relevant item IDs
            total_available: Total number of items available
            
        Returns:
            Dictionary with retrieval metrics
        """
        retrieved_set = set(retrieved)
        relevant_set = set(relevant)
        
        true_positives = len(retrieved_set & relevant_set)
        false_positives = len(retrieved_set - relevant_set)
        false_negatives = len(relevant_set - retrieved_set)
        
        precision = true_positives / len(retrieved) if retrieved else 0.0
        recall = true_positives / len(relevant) if relevant else 0.0
        
        self.record("retrieval_precision", precision,
                   retrieved_count=len(retrieved),
                   relevant_count=len(relevant))
        self.record("retrieval_recall", recall,
                   true_positives=true_positives,
                   false_negatives=false_negatives)
        
        return {
            "precision": precision,
            "recall": recall,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        }
    
    def calculate_drift_metrics(
        self,
        outputs_without_rules: List[Dict[str, Any]],
        outputs_with_rules: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate drift reduction metrics.
        
        Args:
            outputs_without_rules: Outputs from runs without rules
            outputs_with_rules: Outputs from runs with rules
            
        Returns:
            Dictionary with drift metrics
        """
        # Calculate consistency scores
        consistency_without = self._calculate_consistency(outputs_without_rules)
        consistency_with = self._calculate_consistency(outputs_with_rules)
        
        # Calculate drift reduction
        drift_without = 1.0 - consistency_without
        drift_with = 1.0 - consistency_with
        drift_reduction = (drift_without - drift_with) / drift_without * 100 if drift_without > 0 else 0.0
        
        self.record("consistency_without_rules", consistency_without)
        self.record("consistency_with_rules", consistency_with)
        self.record("drift_reduction_percentage", drift_reduction)
        
        return {
            "consistency_without_rules": consistency_without,
            "consistency_with_rules": consistency_with,
            "drift_reduction_percentage": drift_reduction
        }
    
    def _calculate_consistency(self, outputs: List[Dict[str, Any]]) -> float:
        """Calculate consistency score for a set of outputs.
        
        Args:
            outputs: List of output dictionaries
            
        Returns:
            Consistency score (0-1)
        """
        if len(outputs) < 2:
            return 1.0
        
        # Simple consistency: compare all pairs and average
        scores = []
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                score = self._compare_outputs(outputs[i], outputs[j])
                scores.append(score)
        
        return np.mean(scores) if scores else 0.0
    
    def _compare_outputs(self, output1: Dict[str, Any], output2: Dict[str, Any]) -> float:
        """Compare two outputs for similarity.
        
        Args:
            output1: First output
            output2: Second output
            
        Returns:
            Similarity score (0-1)
        """
        # This is a simplified comparison - in practice, you'd implement
        # more sophisticated comparison based on the output structure
        
        # Compare keys
        keys1 = set(output1.keys())
        keys2 = set(output2.keys())
        key_similarity = len(keys1 & keys2) / len(keys1 | keys2) if (keys1 | keys2) else 1.0
        
        # Compare values for common keys
        common_keys = keys1 & keys2
        if not common_keys:
            return key_similarity
        
        value_similarities = []
        for key in common_keys:
            if output1[key] == output2[key]:
                value_similarities.append(1.0)
            elif isinstance(output1[key], (int, float)) and isinstance(output2[key], (int, float)):
                # Numeric similarity
                max_val = max(abs(output1[key]), abs(output2[key]))
                if max_val > 0:
                    similarity = 1.0 - abs(output1[key] - output2[key]) / max_val
                else:
                    similarity = 1.0
                value_similarities.append(similarity)
            else:
                value_similarities.append(0.0)
        
        value_similarity = np.mean(value_similarities) if value_similarities else 0.0
        
        # Weighted average
        return 0.3 * key_similarity + 0.7 * value_similarity
    
    def save_metrics(self, filepath: Optional[str] = None) -> None:
        """Save metrics to JSON file.
        
        Args:
            filepath: Path to save metrics (uses default if not provided)
        """
        if filepath is None and self.output_dir:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"{self.module_name}_metrics_{timestamp}.json"
        
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "module": self.module_name,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": [m.to_dict() for m in self.metrics]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics.
        
        Returns:
            Dictionary with metric summaries
        """
        summary = {
            "module": self.module_name,
            "total_metrics": len(self.metrics),
            "metrics_by_name": {}
        }
        
        # Group metrics by name
        for metric in self.metrics:
            name = metric.metric_name
            if name not in summary["metrics_by_name"]:
                summary["metrics_by_name"][name] = {
                    "values": [],
                    "count": 0,
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0
                }
            
            summary["metrics_by_name"][name]["values"].append(metric.value)
            summary["metrics_by_name"][name]["count"] += 1
        
        # Calculate statistics
        for name, data in summary["metrics_by_name"].items():
            values = data["values"]
            data["mean"] = np.mean(values)
            data["min"] = np.min(values)
            data["max"] = np.max(values)
            data["std"] = np.std(values) if len(values) > 1 else 0.0
            del data["values"]  # Remove raw values from summary
        
        return summary


class EvaluationMetrics:
    """Static methods for common evaluation metrics."""
    
    @staticmethod
    def calculate_rule_similarity(rule1: Dict[str, Any], rule2: Dict[str, Any]) -> float:
        """Calculate similarity between two rules.
        
        Args:
            rule1: First rule dictionary
            rule2: Second rule dictionary
            
        Returns:
            Similarity score (0-1)
        """
        # Compare match criteria
        criteria_sim = 0.0
        if rule1.get("match_criteria") and rule2.get("match_criteria"):
            if rule1["match_criteria"]["type"] == rule2["match_criteria"]["type"]:
                criteria_sim += 0.5
            if rule1["match_criteria"]["value"] == rule2["match_criteria"]["value"]:
                criteria_sim += 0.5
        
        # Compare action
        action_sim = 0.0
        if rule1.get("action") and rule2.get("action"):
            if rule1["action"]["type"] == rule2["action"]["type"]:
                action_sim += 0.5
            # Simple text similarity for description
            desc1 = rule1["action"]["description"].lower()
            desc2 = rule2["action"]["description"].lower()
            if desc1 == desc2:
                action_sim += 0.5
            elif desc1 in desc2 or desc2 in desc1:
                action_sim += 0.25
        
        # Weighted average
        return 0.6 * criteria_sim + 0.4 * action_sim
    
    @staticmethod
    def match_rules_to_ground_truth(
        extracted: List[Dict[str, Any]], 
        ground_truth: List[Dict[str, Any]],
        similarity_threshold: float = 0.7
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Match extracted rules to ground truth rules.
        
        Args:
            extracted: List of extracted rules
            ground_truth: List of ground truth rules
            similarity_threshold: Minimum similarity for matching
            
        Returns:
            Tuple of (matches, unmatched_extracted, unmatched_ground_truth)
        """
        matches = []
        matched_extracted = set()
        matched_ground_truth = set()
        
        # Find best matches
        for i, ext_rule in enumerate(extracted):
            best_match = -1
            best_score = 0.0
            
            for j, gt_rule in enumerate(ground_truth):
                if j in matched_ground_truth:
                    continue
                    
                score = EvaluationMetrics.calculate_rule_similarity(ext_rule, gt_rule)
                if score > best_score and score >= similarity_threshold:
                    best_score = score
                    best_match = j
            
            if best_match >= 0:
                matches.append((i, best_match))
                matched_extracted.add(i)
                matched_ground_truth.add(best_match)
        
        # Find unmatched
        unmatched_extracted = [i for i in range(len(extracted)) if i not in matched_extracted]
        unmatched_ground_truth = [j for j in range(len(ground_truth)) if j not in matched_ground_truth]
        
        return matches, unmatched_extracted, unmatched_ground_truth