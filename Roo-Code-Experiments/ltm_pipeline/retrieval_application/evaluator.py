"""Evaluation module for retrieval and application performance."""

from typing import List, Dict, Any, Tuple, Optional
import time
from datetime import datetime

from ..common.models import Rule, Task, ApplicationResult
from ..common.metrics import MetricsCollector
from ..common.logger import get_logger


class RetrievalEvaluator:
    """Evaluate retrieval and application performance."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.logger = get_logger("RetrievalEvaluator")
        self.metrics = MetricsCollector("retrieval_evaluation")
    
    def evaluate_retrieval(self, 
                          retrieved_rules: List[Rule],
                          expected_rules: List[str],
                          all_relevant_rules: Optional[List[str]] = None) -> Dict[str, float]:
        """Evaluate retrieval performance.
        
        Args:
            retrieved_rules: List of retrieved rules
            expected_rules: List of expected rule IDs
            all_relevant_rules: Optional list of all relevant rule IDs (for recall calculation)
            
        Returns:
            Dictionary containing retrieval metrics
        """
        start_time = time.time()
        
        # Get retrieved rule IDs
        retrieved_ids = [rule.id for rule in retrieved_rules]
        
        # Calculate true positives, false positives, false negatives
        retrieved_set = set(retrieved_ids)
        expected_set = set(expected_rules)
        
        true_positives = len(retrieved_set & expected_set)
        false_positives = len(retrieved_set - expected_set)
        false_negatives = len(expected_set - retrieved_set)
        
        # Calculate metrics
        metrics = self.metrics.calculate_retrieval_metrics(
            retrieved=retrieved_ids,
            relevant=expected_rules,
            total_available=len(all_relevant_rules) if all_relevant_rules else len(expected_rules)
        )
        
        # Add additional metrics
        metrics["total_retrieved"] = len(retrieved_rules)
        metrics["total_expected"] = len(expected_rules)
        
        # Calculate over-retrieval rate
        if expected_rules:
            over_retrieval_rate = max(0, len(retrieved_rules) - len(expected_rules)) / len(expected_rules)
            metrics["over_retrieval_rate"] = over_retrieval_rate
        else:
            metrics["over_retrieval_rate"] = 0.0
        
        processing_time = time.time() - start_time
        metrics["evaluation_time"] = processing_time
        
        self.logger.info(f"Retrieval evaluation: Precision={metrics['precision']:.3f}, "
                        f"Recall={metrics['recall']:.3f}, Retrieved={len(retrieved_rules)}, "
                        f"Expected={len(expected_rules)}")
        
        return metrics
    
    def evaluate_application(self,
                           application_result: ApplicationResult,
                           expected_applications: List[str],
                           task: Optional[Task] = None) -> Dict[str, float]:
        """Evaluate application performance.
        
        Args:
            application_result: Result of rule application
            expected_applications: List of expected rule IDs to be applied
            task: Optional task for context
            
        Returns:
            Dictionary containing application metrics
        """
        # Calculate application accuracy
        applied_set = set(application_result.applied_rules)
        expected_set = set(expected_applications)
        
        correct_applications = len(applied_set & expected_set)
        incorrect_applications = len(applied_set - expected_set)
        missed_applications = len(expected_set - applied_set)
        
        # Calculate metrics
        precision = correct_applications / len(applied_set) if applied_set else 0.0
        recall = correct_applications / len(expected_set) if expected_set else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Calculate over-application rate
        total_rules = len(application_result.applied_rules) + len(application_result.skipped_rules)
        over_application_rate = incorrect_applications / total_rules if total_rules > 0 else 0.0
        
        metrics = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "correct_applications": correct_applications,
            "incorrect_applications": incorrect_applications,
            "missed_applications": missed_applications,
            "total_applied": len(application_result.applied_rules),
            "total_skipped": len(application_result.skipped_rules),
            "total_errors": len(application_result.errors),
            "over_application_rate": over_application_rate
        }
        
        # Record metrics
        self.metrics.record("application_precision", precision)
        self.metrics.record("application_recall", recall)
        self.metrics.record("application_f1", f1)
        self.metrics.record("over_application_rate", over_application_rate)
        
        self.logger.info(f"Application evaluation for task {application_result.task_id}: "
                        f"Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
        
        return metrics
    
    def evaluate_end_to_end(self,
                           task: Task,
                           retrieved_rules: List[Rule],
                           application_result: ApplicationResult,
                           ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate end-to-end retrieval and application performance.
        
        Args:
            task: Task that was processed
            retrieved_rules: Rules that were retrieved
            application_result: Result of applying rules
            ground_truth: Ground truth containing:
                         - expected_retrievals: List of rule IDs expected to be retrieved
                         - expected_applications: List of rule IDs expected to be applied
                         
        Returns:
            Comprehensive evaluation metrics
        """
        self.logger.info(f"Evaluating end-to-end performance for task {task.id}")
        
        # Evaluate retrieval
        retrieval_metrics = self.evaluate_retrieval(
            retrieved_rules,
            ground_truth.get("expected_retrievals", []),
            ground_truth.get("all_relevant_rules")
        )
        
        # Evaluate application
        application_metrics = self.evaluate_application(
            application_result,
            ground_truth.get("expected_applications", []),
            task
        )
        
        # Calculate combined metrics
        combined_metrics = {
            "task_id": task.id,
            "retrieval": retrieval_metrics,
            "application": application_metrics,
            "end_to_end": {
                "total_rules_processed": len(retrieved_rules),
                "total_rules_applied": len(application_result.applied_rules),
                "application_rate": len(application_result.applied_rules) / len(retrieved_rules) 
                                  if retrieved_rules else 0.0,
                "error_rate": len(application_result.errors) / 
                            (len(application_result.applied_rules) + len(application_result.skipped_rules))
                            if (application_result.applied_rules or application_result.skipped_rules) else 0.0
            }
        }
        
        # Calculate overall effectiveness
        # Effectiveness = (retrieval_f1 + application_f1) / 2
        retrieval_f1 = (2 * retrieval_metrics["precision"] * retrieval_metrics["recall"]) / \
                      (retrieval_metrics["precision"] + retrieval_metrics["recall"]) \
                      if (retrieval_metrics["precision"] + retrieval_metrics["recall"]) > 0 else 0.0
        
        application_f1 = application_metrics["f1_score"]
        
        combined_metrics["end_to_end"]["effectiveness"] = (retrieval_f1 + application_f1) / 2
        
        return combined_metrics
    
    def evaluate_batch(self,
                      batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate a batch of retrieval and application results.
        
        Args:
            batch_results: List of result dictionaries, each containing:
                          - task: Task object
                          - retrieved_rules: List of retrieved rules
                          - application_result: ApplicationResult
                          - ground_truth: Ground truth data
                          
        Returns:
            Aggregated evaluation metrics
        """
        self.logger.info(f"Evaluating batch of {len(batch_results)} results")
        
        all_metrics = []
        
        # Aggregate metrics
        total_retrieval_tp = 0
        total_retrieval_fp = 0
        total_retrieval_fn = 0
        
        total_application_correct = 0
        total_application_incorrect = 0
        total_application_missed = 0
        
        for result in batch_results:
            # Evaluate individual result
            metrics = self.evaluate_end_to_end(
                result["task"],
                result["retrieved_rules"],
                result["application_result"],
                result["ground_truth"]
            )
            all_metrics.append(metrics)
            
            # Accumulate retrieval metrics
            ret_metrics = metrics["retrieval"]
            total_retrieval_tp += ret_metrics["true_positives"]
            total_retrieval_fp += ret_metrics["false_positives"]
            total_retrieval_fn += ret_metrics["false_negatives"]
            
            # Accumulate application metrics
            app_metrics = metrics["application"]
            total_application_correct += app_metrics["correct_applications"]
            total_application_incorrect += app_metrics["incorrect_applications"]
            total_application_missed += app_metrics["missed_applications"]
        
        # Calculate overall metrics
        overall_retrieval_precision = total_retrieval_tp / (total_retrieval_tp + total_retrieval_fp) \
                                    if (total_retrieval_tp + total_retrieval_fp) > 0 else 0.0
        overall_retrieval_recall = total_retrieval_tp / (total_retrieval_tp + total_retrieval_fn) \
                                 if (total_retrieval_tp + total_retrieval_fn) > 0 else 0.0
        
        overall_application_precision = total_application_correct / \
                                      (total_application_correct + total_application_incorrect) \
                                      if (total_application_correct + total_application_incorrect) > 0 else 0.0
        overall_application_recall = total_application_correct / \
                                   (total_application_correct + total_application_missed) \
                                   if (total_application_correct + total_application_missed) > 0 else 0.0
        
        # Calculate statistics
        effectiveness_values = [m["end_to_end"]["effectiveness"] for m in all_metrics]
        over_retrieval_values = [m["retrieval"]["over_retrieval_rate"] for m in all_metrics]
        over_application_values = [m["application"]["over_application_rate"] for m in all_metrics]
        
        batch_metrics = {
            "overall": {
                "retrieval": {
                    "precision": overall_retrieval_precision,
                    "recall": overall_retrieval_recall,
                    "f1_score": 2 * (overall_retrieval_precision * overall_retrieval_recall) / 
                               (overall_retrieval_precision + overall_retrieval_recall)
                               if (overall_retrieval_precision + overall_retrieval_recall) > 0 else 0.0
                },
                "application": {
                    "precision": overall_application_precision,
                    "recall": overall_application_recall,
                    "f1_score": 2 * (overall_application_precision * overall_application_recall) / 
                               (overall_application_precision + overall_application_recall)
                               if (overall_application_precision + overall_application_recall) > 0 else 0.0
                }
            },
            "statistics": {
                "num_tasks": len(batch_results),
                "avg_effectiveness": sum(effectiveness_values) / len(effectiveness_values) 
                                   if effectiveness_values else 0.0,
                "avg_over_retrieval_rate": sum(over_retrieval_values) / len(over_retrieval_values)
                                          if over_retrieval_values else 0.0,
                "avg_over_application_rate": sum(over_application_values) / len(over_application_values)
                                            if over_application_values else 0.0,
                "min_effectiveness": min(effectiveness_values) if effectiveness_values else 0.0,
                "max_effectiveness": max(effectiveness_values) if effectiveness_values else 0.0
            },
            "individual_results": all_metrics
        }
        
        return batch_metrics
    
    def analyze_failures(self,
                        batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze failures in retrieval and application.
        
        Args:
            batch_results: Batch results to analyze
            
        Returns:
            Failure analysis
        """
        retrieval_failures = {
            "false_positives": [],
            "false_negatives": []
        }
        
        application_failures = {
            "incorrect_applications": [],
            "missed_applications": [],
            "errors": []
        }
        
        for result in batch_results:
            task = result["task"]
            retrieved_rules = result["retrieved_rules"]
            app_result = result["application_result"]
            ground_truth = result["ground_truth"]
            
            # Analyze retrieval failures
            retrieved_ids = [r.id for r in retrieved_rules]
            expected_retrievals = set(ground_truth.get("expected_retrievals", []))
            
            for rule in retrieved_rules:
                if rule.id not in expected_retrievals:
                    retrieval_failures["false_positives"].append({
                        "task_id": task.id,
                        "rule_id": rule.id,
                        "rule_description": rule.action.description
                    })
            
            for expected_id in expected_retrievals:
                if expected_id not in retrieved_ids:
                    retrieval_failures["false_negatives"].append({
                        "task_id": task.id,
                        "rule_id": expected_id
                    })
            
            # Analyze application failures
            expected_applications = set(ground_truth.get("expected_applications", []))
            
            for applied_id in app_result.applied_rules:
                if applied_id not in expected_applications:
                    application_failures["incorrect_applications"].append({
                        "task_id": task.id,
                        "rule_id": applied_id
                    })
            
            for expected_id in expected_applications:
                if expected_id not in app_result.applied_rules:
                    application_failures["missed_applications"].append({
                        "task_id": task.id,
                        "rule_id": expected_id,
                        "was_retrieved": expected_id in retrieved_ids
                    })
            
            # Collect errors
            for error in app_result.errors:
                application_failures["errors"].append({
                    "task_id": task.id,
                    "error": error
                })
        
        # Analyze patterns
        analysis = {
            "retrieval_failures": retrieval_failures,
            "application_failures": application_failures,
            "patterns": self._analyze_failure_patterns(retrieval_failures, application_failures)
        }
        
        return analysis
    
    def _analyze_failure_patterns(self,
                                 retrieval_failures: Dict[str, List],
                                 application_failures: Dict[str, List]) -> Dict[str, Any]:
        """Analyze patterns in failures.
        
        Args:
            retrieval_failures: Retrieval failure data
            application_failures: Application failure data
            
        Returns:
            Pattern analysis
        """
        patterns = {
            "retrieval": {
                "false_positive_rate": len(retrieval_failures["false_positives"]) / 
                                      (len(retrieval_failures["false_positives"]) + 
                                       len(retrieval_failures["false_negatives"]))
                                      if (retrieval_failures["false_positives"] or 
                                          retrieval_failures["false_negatives"]) else 0.0,
                "common_false_positive_rules": self._get_common_items(
                    retrieval_failures["false_positives"], "rule_id"
                )
            },
            "application": {
                "missed_but_retrieved": sum(1 for m in application_failures["missed_applications"]
                                          if m.get("was_retrieved", False)),
                "error_rate": len(application_failures["errors"]) / 
                            (len(application_failures["incorrect_applications"]) +
                             len(application_failures["missed_applications"]) +
                             len(application_failures["errors"]))
                            if any(application_failures.values()) else 0.0
            }
        }
        
        return patterns
    
    def _get_common_items(self, items: List[Dict], key: str, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get most common items by key.
        
        Args:
            items: List of dictionaries
            key: Key to count by
            top_n: Number of top items to return
            
        Returns:
            List of (item, count) tuples
        """
        from collections import Counter
        
        counter = Counter(item.get(key) for item in items if key in item)
        return counter.most_common(top_n)
    
    def generate_report(self,
                       batch_metrics: Dict[str, Any],
                       failure_analysis: Optional[Dict[str, Any]] = None,
                       output_path: Optional[str] = None) -> str:
        """Generate evaluation report.
        
        Args:
            batch_metrics: Batch evaluation metrics
            failure_analysis: Optional failure analysis
            output_path: Optional path to save report
            
        Returns:
            Report as string
        """
        report_lines = [
            "=" * 60,
            "Retrieval & Application Evaluation Report",
            "=" * 60,
            "",
            f"Evaluation Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Overall performance
        if "overall" in batch_metrics:
            overall = batch_metrics["overall"]
            report_lines.extend([
                "Overall Performance:",
                "-" * 30,
                "",
                "Retrieval Metrics:",
                f"  Precision: {overall['retrieval']['precision']:.3f}",
                f"  Recall: {overall['retrieval']['recall']:.3f}",
                f"  F1 Score: {overall['retrieval']['f1_score']:.3f}",
                "",
                "Application Metrics:",
                f"  Precision: {overall['application']['precision']:.3f}",
                f"  Recall: {overall['application']['recall']:.3f}",
                f"  F1 Score: {overall['application']['f1_score']:.3f}",
                ""
            ])
        
        # Statistics
        if "statistics" in batch_metrics:
            stats = batch_metrics["statistics"]
            report_lines.extend([
                "Batch Statistics:",
                "-" * 30,
                f"Number of Tasks: {stats['num_tasks']}",
                f"Average Effectiveness: {stats['avg_effectiveness']:.3f}",
                f"Average Over-retrieval Rate: {stats['avg_over_retrieval_rate']:.3f}",
                f"Average Over-application Rate: {stats['avg_over_application_rate']:.3f}",
                f"Effectiveness Range: [{stats['min_effectiveness']:.3f}, {stats['max_effectiveness']:.3f}]",
                ""
            ])
        
        # Failure analysis
        if failure_analysis:
            report_lines.extend([
                "Failure Analysis:",
                "-" * 30,
                f"Retrieval False Positives: {len(failure_analysis['retrieval_failures']['false_positives'])}",
                f"Retrieval False Negatives: {len(failure_analysis['retrieval_failures']['false_negatives'])}",
                f"Application Incorrect: {len(failure_analysis['application_failures']['incorrect_applications'])}",
                f"Application Missed: {len(failure_analysis['application_failures']['missed_applications'])}",
                f"Application Errors: {len(failure_analysis['application_failures']['errors'])}",
                ""
            ])
            
            # Common failures
            if failure_analysis["patterns"]["retrieval"]["common_false_positive_rules"]:
                report_lines.append("Common False Positive Rules:")
                for rule_id, count in failure_analysis["patterns"]["retrieval"]["common_false_positive_rules"]:
                    report_lines.append(f"  {rule_id}: {count} occurrences")
                report_lines.append("")
        
        report_lines.extend([
            "=" * 60,
            "End of Report",
            "=" * 60
        ])
        
        report = "\n".join(report_lines)
        
        # Save if path provided
        if output_path:
            from pathlib import Path
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            self.logger.info(f"Report saved to {output_path}")
        
        return report