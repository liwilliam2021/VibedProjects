"""Evaluation module for storage decision performance."""

from typing import List, Dict, Any, Tuple, Optional
import time
from pathlib import Path

from ..common.models import StorageDecision
from ..common.metrics import MetricsCollector
from ..common.logger import get_logger


class DecisionEvaluator:
    """Evaluate storage decision performance against ground truth."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.logger = get_logger("DecisionEvaluator")
        self.metrics = MetricsCollector("decision_evaluation")
    
    def evaluate(self, 
                decisions: List[StorageDecision], 
                ground_truth: List[Dict[str, str]]) -> Dict[str, float]:
        """Evaluate storage decisions against ground truth.
        
        Args:
            decisions: List of storage decisions made
            ground_truth: List of ground truth decisions with 'rule_id' and 'decision'
            
        Returns:
            Dictionary containing evaluation metrics
        """
        start_time = time.time()
        
        self.logger.info(f"Evaluating {len(decisions)} decisions against "
                        f"{len(ground_truth)} ground truth labels")
        
        # Create lookup for ground truth
        gt_lookup = {gt["rule_id"]: gt["decision"] for gt in ground_truth}
        
        # Calculate agreement
        predictions = []
        labels = []
        
        for decision in decisions:
            if decision.rule_id in gt_lookup:
                predictions.append(decision.decision)
                labels.append(gt_lookup[decision.rule_id])
        
        if not predictions:
            self.logger.warning("No matching decisions found for evaluation")
            return {
                "agreement_rate": 0.0,
                "total_decisions": len(decisions),
                "total_ground_truth": len(ground_truth),
                "matched_decisions": 0
            }
        
        # Calculate metrics
        agreement_rate = self.metrics.calculate_agreement_rate(predictions, labels)
        
        # Calculate confusion matrix metrics
        tp = sum(1 for p, l in zip(predictions, labels) if p == "store" and l == "store")
        tn = sum(1 for p, l in zip(predictions, labels) if p == "ignore" and l == "ignore")
        fp = sum(1 for p, l in zip(predictions, labels) if p == "store" and l == "ignore")
        fn = sum(1 for p, l in zip(predictions, labels) if p == "ignore" and l == "store")
        
        # Calculate additional metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # False positive/negative rates
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        processing_time = time.time() - start_time
        
        metrics = {
            "agreement_rate": agreement_rate,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "confusion_matrix": {
                "true_positive": tp,
                "true_negative": tn,
                "false_positive": fp,
                "false_negative": fn
            },
            "total_decisions": len(decisions),
            "total_ground_truth": len(ground_truth),
            "matched_decisions": len(predictions),
            "evaluation_time": processing_time
        }
        
        # Log results
        self.logger.info(f"Evaluation complete: Agreement={agreement_rate:.3f}, "
                        f"Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
        
        # Record metrics
        self.metrics.record("agreement_rate", agreement_rate)
        self.metrics.record("precision", precision)
        self.metrics.record("recall", recall)
        self.metrics.record("f1_score", f1)
        
        return metrics
    
    def evaluate_batch(self, 
                      batch_results: List[Dict[str, Any]],
                      ground_truth_batches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate multiple batches of decisions.
        
        Args:
            batch_results: List of batch decision results
            ground_truth_batches: List of ground truth for each batch
            
        Returns:
            Aggregated evaluation metrics
        """
        self.logger.info(f"Evaluating {len(batch_results)} batches")
        
        all_metrics = []
        total_tp = 0
        total_tn = 0
        total_fp = 0
        total_fn = 0
        
        for batch_result, gt_batch in zip(batch_results, ground_truth_batches):
            # Extract decisions from batch result
            decisions = []
            for rule, decision, justification in batch_result["results"]:
                storage_decision = StorageDecision(
                    rule_id=rule.id,
                    decision=decision,
                    justification=justification,
                    confidence=rule.confidence
                )
                decisions.append(storage_decision)
            
            # Evaluate batch
            metrics = self.evaluate(decisions, gt_batch["ground_truth"])
            metrics["batch_id"] = batch_result.get("batch_id", "unknown")
            all_metrics.append(metrics)
            
            # Accumulate confusion matrix
            cm = metrics["confusion_matrix"]
            total_tp += cm["true_positive"]
            total_tn += cm["true_negative"]
            total_fp += cm["false_positive"]
            total_fn += cm["false_negative"]
        
        # Calculate overall metrics
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) \
                    if (overall_precision + overall_recall) > 0 else 0.0
        overall_agreement = (total_tp + total_tn) / (total_tp + total_tn + total_fp + total_fn) \
                          if (total_tp + total_tn + total_fp + total_fn) > 0 else 0.0
        
        # Calculate statistics
        agreement_values = [m["agreement_rate"] for m in all_metrics]
        precision_values = [m["precision"] for m in all_metrics]
        recall_values = [m["recall"] for m in all_metrics]
        f1_values = [m["f1_score"] for m in all_metrics]
        
        batch_metrics = {
            "overall": {
                "agreement_rate": overall_agreement,
                "precision": overall_precision,
                "recall": overall_recall,
                "f1_score": overall_f1,
                "confusion_matrix": {
                    "true_positive": total_tp,
                    "true_negative": total_tn,
                    "false_positive": total_fp,
                    "false_negative": total_fn
                }
            },
            "statistics": {
                "num_batches": len(batch_results),
                "avg_agreement": sum(agreement_values) / len(agreement_values) if agreement_values else 0.0,
                "avg_precision": sum(precision_values) / len(precision_values) if precision_values else 0.0,
                "avg_recall": sum(recall_values) / len(recall_values) if recall_values else 0.0,
                "avg_f1": sum(f1_values) / len(f1_values) if f1_values else 0.0,
                "min_agreement": min(agreement_values) if agreement_values else 0.0,
                "max_agreement": max(agreement_values) if agreement_values else 0.0
            },
            "individual_results": all_metrics
        }
        
        return batch_metrics
    
    def analyze_errors(self, 
                      decisions: List[StorageDecision],
                      ground_truth: List[Dict[str, str]],
                      rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Analyze errors in storage decisions.
        
        Args:
            decisions: List of storage decisions
            ground_truth: List of ground truth decisions
            rules: Optional list of rule dictionaries for detailed analysis
            
        Returns:
            Error analysis results
        """
        # Create lookups
        gt_lookup = {gt["rule_id"]: gt["decision"] for gt in ground_truth}
        decision_lookup = {d.rule_id: d for d in decisions}
        rule_lookup = {r["id"]: r for r in rules} if rules else {}
        
        # Categorize errors
        false_positives = []  # Stored when should ignore
        false_negatives = []  # Ignored when should store
        
        for decision in decisions:
            if decision.rule_id in gt_lookup:
                predicted = decision.decision
                actual = gt_lookup[decision.rule_id]
                
                if predicted == "store" and actual == "ignore":
                    error_info = {
                        "rule_id": decision.rule_id,
                        "predicted": predicted,
                        "actual": actual,
                        "justification": decision.justification,
                        "confidence": decision.confidence
                    }
                    
                    # Add rule details if available
                    if decision.rule_id in rule_lookup:
                        rule = rule_lookup[decision.rule_id]
                        error_info["rule_description"] = rule.get("action", {}).get("description", "N/A")
                        error_info["rule_type"] = rule.get("action", {}).get("type", "N/A")
                    
                    false_positives.append(error_info)
                    
                elif predicted == "ignore" and actual == "store":
                    error_info = {
                        "rule_id": decision.rule_id,
                        "predicted": predicted,
                        "actual": actual,
                        "justification": decision.justification,
                        "confidence": decision.confidence
                    }
                    
                    if decision.rule_id in rule_lookup:
                        rule = rule_lookup[decision.rule_id]
                        error_info["rule_description"] = rule.get("action", {}).get("description", "N/A")
                        error_info["rule_type"] = rule.get("action", {}).get("type", "N/A")
                    
                    false_negatives.append(error_info)
        
        # Analyze patterns in errors
        fp_patterns = self._analyze_error_patterns(false_positives)
        fn_patterns = self._analyze_error_patterns(false_negatives)
        
        return {
            "false_positives": {
                "count": len(false_positives),
                "examples": false_positives[:5],  # First 5 examples
                "patterns": fp_patterns
            },
            "false_negatives": {
                "count": len(false_negatives),
                "examples": false_negatives[:5],  # First 5 examples
                "patterns": fn_patterns
            },
            "error_rate": (len(false_positives) + len(false_negatives)) / len(decisions) if decisions else 0.0
        }
    
    def _analyze_error_patterns(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in errors.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Pattern analysis results
        """
        if not errors:
            return {"no_errors": True}
        
        patterns = {
            "by_rule_type": {},
            "by_confidence_range": {
                "high": 0,      # >= 0.8
                "medium": 0,    # 0.6 - 0.8
                "low": 0        # < 0.6
            },
            "common_justification_keywords": {}
        }
        
        for error in errors:
            # By rule type
            rule_type = error.get("rule_type", "unknown")
            patterns["by_rule_type"][rule_type] = patterns["by_rule_type"].get(rule_type, 0) + 1
            
            # By confidence range
            confidence = error.get("confidence", 0.0)
            if confidence >= 0.8:
                patterns["by_confidence_range"]["high"] += 1
            elif confidence >= 0.6:
                patterns["by_confidence_range"]["medium"] += 1
            else:
                patterns["by_confidence_range"]["low"] += 1
            
            # Extract keywords from justification
            justification = error.get("justification", "").lower()
            keywords = ["cross-session", "stability", "triggers", "consistency", 
                       "specificity", "confidence", "temporal", "broad", "conflict"]
            
            for keyword in keywords:
                if keyword in justification:
                    patterns["common_justification_keywords"][keyword] = \
                        patterns["common_justification_keywords"].get(keyword, 0) + 1
        
        return patterns
    
    def generate_report(self, 
                       metrics: Dict[str, Any],
                       error_analysis: Optional[Dict[str, Any]] = None,
                       output_path: Optional[str] = None) -> str:
        """Generate a human-readable evaluation report.
        
        Args:
            metrics: Evaluation metrics
            error_analysis: Optional error analysis results
            output_path: Optional path to save the report
            
        Returns:
            Report as a string
        """
        report_lines = [
            "=" * 60,
            "Storage Decision Evaluation Report",
            "=" * 60,
            "",
            f"Evaluation Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Overall metrics
        if "overall" in metrics:
            overall = metrics["overall"]
            report_lines.extend([
                "Overall Performance:",
                "-" * 30,
                f"Agreement Rate: {overall['agreement_rate']:.3f}",
                f"Precision: {overall['precision']:.3f}",
                f"Recall: {overall['recall']:.3f}",
                f"F1 Score: {overall['f1_score']:.3f}",
                "",
                "Confusion Matrix:",
                f"  True Positives: {overall['confusion_matrix']['true_positive']}",
                f"  True Negatives: {overall['confusion_matrix']['true_negative']}",
                f"  False Positives: {overall['confusion_matrix']['false_positive']}",
                f"  False Negatives: {overall['confusion_matrix']['false_negative']}",
                ""
            ])
        elif "agreement_rate" in metrics:
            # Single evaluation metrics
            report_lines.extend([
                "Performance Metrics:",
                "-" * 30,
                f"Agreement Rate: {metrics['agreement_rate']:.3f}",
                f"Precision: {metrics['precision']:.3f}",
                f"Recall: {metrics['recall']:.3f}",
                f"F1 Score: {metrics['f1_score']:.3f}",
                f"False Positive Rate: {metrics['false_positive_rate']:.3f}",
                f"False Negative Rate: {metrics['false_negative_rate']:.3f}",
                ""
            ])
        
        # Statistics
        if "statistics" in metrics:
            stats = metrics["statistics"]
            report_lines.extend([
                "Batch Statistics:",
                "-" * 30,
                f"Number of Batches: {stats['num_batches']}",
                f"Average Agreement: {stats['avg_agreement']:.3f}",
                f"Agreement Range: [{stats['min_agreement']:.3f}, {stats['max_agreement']:.3f}]",
                ""
            ])
        
        # Error analysis
        if error_analysis:
            report_lines.extend([
                "Error Analysis:",
                "-" * 30,
                f"Total Error Rate: {error_analysis['error_rate']:.3f}",
                "",
                f"False Positives: {error_analysis['false_positives']['count']}",
            ])
            
            if error_analysis['false_positives']['patterns'].get('by_rule_type'):
                report_lines.append("  By Rule Type:")
                for rule_type, count in error_analysis['false_positives']['patterns']['by_rule_type'].items():
                    report_lines.append(f"    {rule_type}: {count}")
            
            report_lines.extend([
                "",
                f"False Negatives: {error_analysis['false_negatives']['count']}",
            ])
            
            if error_analysis['false_negatives']['patterns'].get('by_rule_type'):
                report_lines.append("  By Rule Type:")
                for rule_type, count in error_analysis['false_negatives']['patterns']['by_rule_type'].items():
                    report_lines.append(f"    {rule_type}: {count}")
            
            report_lines.append("")
        
        report_lines.extend([
            "=" * 60,
            "End of Report",
            "=" * 60
        ])
        
        report = "\n".join(report_lines)
        
        # Save report if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            self.logger.info(f"Report saved to {output_path}")
        
        return report
    
    def compare_decision_makers(self, 
                               results_dict: Dict[str, List[StorageDecision]],
                               ground_truth: List[Dict[str, str]]) -> Dict[str, Any]:
        """Compare performance of multiple decision makers.
        
        Args:
            results_dict: Dictionary mapping decision maker names to their decisions
            ground_truth: Ground truth decisions
            
        Returns:
            Comparison metrics
        """
        comparison = {
            "decision_makers": {},
            "best_overall": None,
            "best_precision": None,
            "best_recall": None
        }
        
        best_agreement = 0.0
        best_precision = 0.0
        best_recall = 0.0
        
        for dm_name, decisions in results_dict.items():
            # Evaluate this decision maker
            metrics = self.evaluate(decisions, ground_truth)
            comparison["decision_makers"][dm_name] = metrics
            
            # Track best performers
            if metrics["agreement_rate"] > best_agreement:
                best_agreement = metrics["agreement_rate"]
                comparison["best_overall"] = dm_name
            
            if metrics["precision"] > best_precision:
                best_precision = metrics["precision"]
                comparison["best_precision"] = dm_name
            
            if metrics["recall"] > best_recall:
                best_recall = metrics["recall"]
                comparison["best_recall"] = dm_name
        
        return comparison