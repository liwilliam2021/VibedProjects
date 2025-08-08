"""Evaluation module for rule extraction performance."""

from typing import List, Dict, Any, Tuple, Optional
import time
from pathlib import Path

from ..common.models import Rule
from ..common.metrics import MetricsCollector, EvaluationMetrics
from ..common.logger import get_logger


class ExtractionEvaluator:
    """Evaluate rule extraction performance against ground truth."""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """Initialize the evaluator.
        
        Args:
            similarity_threshold: Minimum similarity score for matching rules
        """
        self.logger = get_logger("ExtractionEvaluator")
        self.metrics = MetricsCollector("extraction_evaluation")
        self.similarity_threshold = similarity_threshold
    
    def evaluate(self, extracted: List[Rule], ground_truth: List[Rule]) -> Dict[str, float]:
        """Evaluate extraction performance.
        
        Args:
            extracted: List of extracted rules
            ground_truth: List of ground truth rules
            
        Returns:
            Dictionary containing evaluation metrics
        """
        start_time = time.time()
        
        self.logger.info(f"Evaluating {len(extracted)} extracted rules against "
                        f"{len(ground_truth)} ground truth rules")
        
        # Convert rules to dictionaries for comparison
        extracted_dicts = [rule.to_dict() for rule in extracted]
        ground_truth_dicts = [rule.to_dict() for rule in ground_truth]
        
        # Match rules
        matches, unmatched_extracted, unmatched_ground_truth = \
            EvaluationMetrics.match_rules_to_ground_truth(
                extracted_dicts, 
                ground_truth_dicts,
                self.similarity_threshold
            )
        
        # Calculate metrics
        true_positives = len(matches)
        false_positives = len(unmatched_extracted)
        false_negatives = len(unmatched_ground_truth)
        
        metrics = self.metrics.calculate_precision_recall_f1(
            true_positives, false_positives, false_negatives
        )
        
        # Additional metrics
        metrics["total_extracted"] = len(extracted)
        metrics["total_ground_truth"] = len(ground_truth)
        metrics["matches"] = true_positives
        metrics["similarity_threshold"] = self.similarity_threshold
        
        # Calculate per-type metrics
        type_metrics = self._calculate_type_metrics(
            extracted, ground_truth, matches
        )
        metrics["by_type"] = type_metrics
        
        # Calculate confidence metrics
        confidence_metrics = self._calculate_confidence_metrics(
            extracted, matches, unmatched_extracted
        )
        metrics["confidence"] = confidence_metrics
        
        processing_time = time.time() - start_time
        metrics["evaluation_time"] = processing_time
        
        # Log results
        self.logger.info(f"Evaluation complete: Precision={metrics['precision']:.3f}, "
                        f"Recall={metrics['recall']:.3f}, F1={metrics['f1_score']:.3f}")
        
        # Record metrics
        self.metrics.record("evaluation_time", processing_time)
        
        return metrics
    
    def _calculate_type_metrics(self, extracted: List[Rule], 
                               ground_truth: List[Rule],
                               matches: List[Tuple[int, int]]) -> Dict[str, Dict[str, float]]:
        """Calculate metrics broken down by rule type.
        
        Args:
            extracted: List of extracted rules
            ground_truth: List of ground truth rules
            matches: List of (extracted_idx, ground_truth_idx) matches
            
        Returns:
            Dictionary of metrics by rule type
        """
        type_metrics = {}
        
        # Get matched indices
        matched_extracted = {m[0] for m in matches}
        matched_ground_truth = {m[1] for m in matches}
        
        # Count by type
        for rule_type in ["naming", "style", "structure", "behavior"]:
            # Count in ground truth
            gt_count = sum(1 for rule in ground_truth 
                          if rule.action.type.value == rule_type)
            
            # Count in extracted
            ext_count = sum(1 for rule in extracted 
                           if rule.action.type.value == rule_type)
            
            # Count true positives
            tp_count = sum(1 for ext_idx, gt_idx in matches
                          if extracted[ext_idx].action.type.value == rule_type and
                          ground_truth[gt_idx].action.type.value == rule_type)
            
            # Count false positives
            fp_count = sum(1 for i, rule in enumerate(extracted)
                          if i not in matched_extracted and 
                          rule.action.type.value == rule_type)
            
            # Count false negatives
            fn_count = sum(1 for i, rule in enumerate(ground_truth)
                          if i not in matched_ground_truth and
                          rule.action.type.value == rule_type)
            
            # Calculate metrics
            if gt_count > 0 or ext_count > 0:
                precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
                recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
                
                type_metrics[rule_type] = {
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "ground_truth_count": gt_count,
                    "extracted_count": ext_count,
                    "true_positives": tp_count,
                    "false_positives": fp_count,
                    "false_negatives": fn_count
                }
        
        return type_metrics
    
    def _calculate_confidence_metrics(self, extracted: List[Rule],
                                     matches: List[Tuple[int, int]],
                                     unmatched_indices: List[int]) -> Dict[str, float]:
        """Calculate metrics related to confidence scores.
        
        Args:
            extracted: List of extracted rules
            matches: List of matched rule indices
            unmatched_indices: Indices of unmatched extracted rules
            
        Returns:
            Dictionary of confidence-related metrics
        """
        if not extracted:
            return {
                "avg_confidence_all": 0.0,
                "avg_confidence_matched": 0.0,
                "avg_confidence_unmatched": 0.0,
                "confidence_correlation": 0.0
            }
        
        # Get confidence scores
        all_confidences = [rule.confidence for rule in extracted]
        matched_confidences = [extracted[m[0]].confidence for m in matches]
        unmatched_confidences = [extracted[i].confidence for i in unmatched_indices]
        
        # Calculate averages
        avg_all = sum(all_confidences) / len(all_confidences)
        avg_matched = sum(matched_confidences) / len(matched_confidences) if matched_confidences else 0.0
        avg_unmatched = sum(unmatched_confidences) / len(unmatched_confidences) if unmatched_confidences else 0.0
        
        # Calculate correlation between confidence and correctness
        # Higher confidence should correlate with being matched (correct)
        correlation = avg_matched - avg_unmatched if matched_confidences and unmatched_confidences else 0.0
        
        return {
            "avg_confidence_all": avg_all,
            "avg_confidence_matched": avg_matched,
            "avg_confidence_unmatched": avg_unmatched,
            "confidence_correlation": correlation
        }
    
    def evaluate_batch(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate a batch of extraction results.
        
        Args:
            results: List of result dictionaries, each containing:
                     - transcript_id: ID of the transcript
                     - extracted: List of extracted rules
                     - ground_truth: List of ground truth rules
                     
        Returns:
            Aggregated evaluation metrics
        """
        self.logger.info(f"Evaluating batch of {len(results)} extraction results")
        
        all_metrics = []
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        for result in results:
            transcript_id = result.get("transcript_id", "unknown")
            extracted = result["extracted"]
            ground_truth = result["ground_truth"]
            
            # Evaluate individual result
            metrics = self.evaluate(extracted, ground_truth)
            metrics["transcript_id"] = transcript_id
            all_metrics.append(metrics)
            
            # Accumulate for overall metrics
            total_tp += metrics["matches"]
            total_fp += metrics["total_extracted"] - metrics["matches"]
            total_fn += metrics["total_ground_truth"] - metrics["matches"]
        
        # Calculate overall metrics
        overall_metrics = self.metrics.calculate_precision_recall_f1(
            total_tp, total_fp, total_fn
        )
        
        # Aggregate type metrics
        aggregated_type_metrics = self._aggregate_type_metrics(all_metrics)
        
        # Calculate statistics
        precision_values = [m["precision"] for m in all_metrics]
        recall_values = [m["recall"] for m in all_metrics]
        f1_values = [m["f1_score"] for m in all_metrics]
        
        batch_metrics = {
            "overall": overall_metrics,
            "by_type": aggregated_type_metrics,
            "statistics": {
                "num_transcripts": len(results),
                "avg_precision": sum(precision_values) / len(precision_values) if precision_values else 0.0,
                "avg_recall": sum(recall_values) / len(recall_values) if recall_values else 0.0,
                "avg_f1": sum(f1_values) / len(f1_values) if f1_values else 0.0,
                "min_precision": min(precision_values) if precision_values else 0.0,
                "max_precision": max(precision_values) if precision_values else 0.0,
                "min_recall": min(recall_values) if recall_values else 0.0,
                "max_recall": max(recall_values) if recall_values else 0.0,
                "min_f1": min(f1_values) if f1_values else 0.0,
                "max_f1": max(f1_values) if f1_values else 0.0
            },
            "individual_results": all_metrics
        }
        
        return batch_metrics
    
    def _aggregate_type_metrics(self, all_metrics: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Aggregate type metrics across multiple evaluations.
        
        Args:
            all_metrics: List of evaluation metrics
            
        Returns:
            Aggregated metrics by type
        """
        type_totals = {}
        
        for metrics in all_metrics:
            if "by_type" not in metrics:
                continue
                
            for rule_type, type_data in metrics["by_type"].items():
                if rule_type not in type_totals:
                    type_totals[rule_type] = {
                        "total_tp": 0,
                        "total_fp": 0,
                        "total_fn": 0,
                        "total_gt": 0,
                        "total_ext": 0
                    }
                
                type_totals[rule_type]["total_tp"] += type_data["true_positives"]
                type_totals[rule_type]["total_fp"] += type_data["false_positives"]
                type_totals[rule_type]["total_fn"] += type_data["false_negatives"]
                type_totals[rule_type]["total_gt"] += type_data["ground_truth_count"]
                type_totals[rule_type]["total_ext"] += type_data["extracted_count"]
        
        # Calculate aggregated metrics
        aggregated = {}
        for rule_type, totals in type_totals.items():
            tp = totals["total_tp"]
            fp = totals["total_fp"]
            fn = totals["total_fn"]
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            aggregated[rule_type] = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "total_ground_truth": totals["total_gt"],
                "total_extracted": totals["total_ext"],
                "total_true_positives": tp,
                "total_false_positives": fp,
                "total_false_negatives": fn
            }
        
        return aggregated
    
    def generate_report(self, metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Generate a human-readable evaluation report.
        
        Args:
            metrics: Evaluation metrics
            output_path: Optional path to save the report
            
        Returns:
            Report as a string
        """
        report_lines = [
            "=" * 60,
            "Rule Extraction Evaluation Report",
            "=" * 60,
            "",
            f"Evaluation Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Similarity Threshold: {self.similarity_threshold}",
            ""
        ]
        
        # Overall metrics
        if "overall" in metrics:
            overall = metrics["overall"]
            report_lines.extend([
                "Overall Performance:",
                "-" * 30,
                f"Precision: {overall['precision']:.3f}",
                f"Recall: {overall['recall']:.3f}",
                f"F1 Score: {overall['f1_score']:.3f}",
                ""
            ])
        
        # Type-specific metrics
        if "by_type" in metrics:
            report_lines.extend([
                "Performance by Rule Type:",
                "-" * 30
            ])
            
            for rule_type, type_metrics in metrics["by_type"].items():
                report_lines.extend([
                    f"\n{rule_type.upper()}:",
                    f"  Precision: {type_metrics['precision']:.3f}",
                    f"  Recall: {type_metrics['recall']:.3f}",
                    f"  F1 Score: {type_metrics['f1_score']:.3f}",
                    f"  Ground Truth Count: {type_metrics.get('total_ground_truth', 'N/A')}",
                    f"  Extracted Count: {type_metrics.get('total_extracted', 'N/A')}"
                ])
            
            report_lines.append("")
        
        # Statistics
        if "statistics" in metrics:
            stats = metrics["statistics"]
            report_lines.extend([
                "Batch Statistics:",
                "-" * 30,
                f"Number of Transcripts: {stats['num_transcripts']}",
                f"Average Precision: {stats['avg_precision']:.3f}",
                f"Average Recall: {stats['avg_recall']:.3f}",
                f"Average F1: {stats['avg_f1']:.3f}",
                f"Precision Range: [{stats['min_precision']:.3f}, {stats['max_precision']:.3f}]",
                f"Recall Range: [{stats['min_recall']:.3f}, {stats['max_recall']:.3f}]",
                f"F1 Range: [{stats['min_f1']:.3f}, {stats['max_f1']:.3f}]",
                ""
            ])
        
        # Confidence metrics
        if "confidence" in metrics:
            conf = metrics["confidence"]
            report_lines.extend([
                "Confidence Analysis:",
                "-" * 30,
                f"Average Confidence (All): {conf['avg_confidence_all']:.3f}",
                f"Average Confidence (Matched): {conf['avg_confidence_matched']:.3f}",
                f"Average Confidence (Unmatched): {conf['avg_confidence_unmatched']:.3f}",
                f"Confidence Correlation: {conf['confidence_correlation']:.3f}",
                ""
            ])
        
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
    
    def compare_extractors(self, results_dict: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Compare performance of multiple extractors.
        
        Args:
            results_dict: Dictionary mapping extractor names to their results
            
        Returns:
            Comparison metrics
        """
        comparison = {
            "extractors": {},
            "best_overall": None,
            "best_by_type": {}
        }
        
        best_f1 = 0.0
        
        for extractor_name, results in results_dict.items():
            # Evaluate batch for this extractor
            batch_metrics = self.evaluate_batch(results)
            comparison["extractors"][extractor_name] = batch_metrics
            
            # Track best overall
            if batch_metrics["overall"]["f1_score"] > best_f1:
                best_f1 = batch_metrics["overall"]["f1_score"]
                comparison["best_overall"] = extractor_name
            
            # Track best by type
            for rule_type, type_metrics in batch_metrics["by_type"].items():
                if rule_type not in comparison["best_by_type"]:
                    comparison["best_by_type"][rule_type] = {
                        "extractor": extractor_name,
                        "f1_score": type_metrics["f1_score"]
                    }
                elif type_metrics["f1_score"] > comparison["best_by_type"][rule_type]["f1_score"]:
                    comparison["best_by_type"][rule_type] = {
                        "extractor": extractor_name,
                        "f1_score": type_metrics["f1_score"]
                    }
        
        return comparison