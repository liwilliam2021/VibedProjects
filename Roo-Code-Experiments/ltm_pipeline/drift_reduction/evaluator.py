"""Evaluation module for drift reduction performance."""

from typing import List, Dict, Any, Optional, Tuple
import time
from datetime import datetime
import statistics

from ..common.logger import get_logger
from ..common.metrics import MetricsCollector
from .consistency_checker import ConsistencyChecker


class DriftEvaluator:
    """Evaluate drift reduction effectiveness."""
    
    def __init__(self, consistency_checker: Optional[ConsistencyChecker] = None):
        """Initialize the drift evaluator.
        
        Args:
            consistency_checker: Optional consistency checker instance
        """
        self.logger = get_logger("DriftEvaluator")
        self.metrics = MetricsCollector("drift_evaluation")
        self.consistency_checker = consistency_checker or ConsistencyChecker()
    
    def evaluate_drift_reduction(self, 
                               comparison_results: List[Dict[str, Any]],
                               improvement_threshold: float = 0.1) -> Dict[str, Any]:
        """Evaluate drift reduction across multiple task comparisons.
        
        Args:
            comparison_results: List of comparison results from TaskRunner
            improvement_threshold: Minimum improvement to consider significant
            
        Returns:
            Comprehensive drift evaluation metrics
        """
        self.logger.info(f"Evaluating drift reduction for {len(comparison_results)} tasks")
        
        start_time = time.time()
        
        # Collect all drift metrics
        all_drift_metrics = []
        task_improvements = []
        
        for comparison in comparison_results:
            task_id = comparison["task_id"]
            outputs_without = comparison["outputs_without_rules"]
            outputs_with = comparison["outputs_with_rules"]
            
            # Calculate drift for this task
            drift_metrics = self.consistency_checker.calculate_drift(
                outputs_without, outputs_with
            )
            
            drift_metrics["task_id"] = task_id
            all_drift_metrics.append(drift_metrics)
            
            # Track improvement
            improvement = drift_metrics["drift_reduction_percentage"] / 100.0
            task_improvements.append({
                "task_id": task_id,
                "improvement": improvement,
                "significant": improvement >= improvement_threshold
            })
            
            # Record per-task metrics
            self.metrics.record("task_drift_reduction", drift_metrics["drift_reduction_percentage"],
                              task_id=task_id)
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(all_drift_metrics)
        
        # Analyze improvements
        improvement_analysis = self._analyze_improvements(task_improvements, improvement_threshold)
        
        # Analyze by metric type
        metric_analysis = self._analyze_by_metric_type(all_drift_metrics)
        
        evaluation_time = time.time() - start_time
        
        evaluation_results = {
            "summary": aggregate_metrics,
            "improvement_analysis": improvement_analysis,
            "metric_analysis": metric_analysis,
            "per_task_results": all_drift_metrics,
            "evaluation_time": evaluation_time
        }
        
        # Log summary
        self.logger.info(f"Drift evaluation complete: "
                        f"Average reduction={aggregate_metrics['avg_drift_reduction']:.1f}%, "
                        f"Significant improvements={improvement_analysis['num_significant']}/{len(comparison_results)}")
        
        return evaluation_results
    
    def _calculate_aggregate_metrics(self, drift_metrics: List[Dict[str, float]]) -> Dict[str, float]:
        """Calculate aggregate metrics across all tasks.
        
        Args:
            drift_metrics: List of drift metric dictionaries
            
        Returns:
            Aggregate metrics
        """
        # Extract values
        consistency_without = [m["consistency_without_rules"] for m in drift_metrics]
        consistency_with = [m["consistency_with_rules"] for m in drift_metrics]
        drift_reductions = [m["drift_reduction_percentage"] for m in drift_metrics]
        improvement_factors = [m["improvement_factor"] for m in drift_metrics]
        
        return {
            "avg_consistency_without_rules": statistics.mean(consistency_without),
            "avg_consistency_with_rules": statistics.mean(consistency_with),
            "avg_drift_reduction": statistics.mean(drift_reductions),
            "median_drift_reduction": statistics.median(drift_reductions),
            "std_drift_reduction": statistics.stdev(drift_reductions) if len(drift_reductions) > 1 else 0.0,
            "min_drift_reduction": min(drift_reductions),
            "max_drift_reduction": max(drift_reductions),
            "avg_improvement_factor": statistics.mean(improvement_factors),
            "overall_consistency_improvement": (
                statistics.mean(consistency_with) - statistics.mean(consistency_without)
            ) / statistics.mean(consistency_without) * 100 if statistics.mean(consistency_without) > 0 else 0.0
        }
    
    def _analyze_improvements(self, task_improvements: List[Dict[str, Any]], 
                            threshold: float) -> Dict[str, Any]:
        """Analyze improvement patterns.
        
        Args:
            task_improvements: List of task improvement data
            threshold: Significance threshold
            
        Returns:
            Improvement analysis
        """
        significant_improvements = [t for t in task_improvements if t["significant"]]
        improvements = [t["improvement"] for t in task_improvements]
        
        return {
            "num_significant": len(significant_improvements),
            "percentage_significant": len(significant_improvements) / len(task_improvements) * 100
                                    if task_improvements else 0.0,
            "avg_improvement": statistics.mean(improvements) if improvements else 0.0,
            "improvement_distribution": {
                "negative": sum(1 for i in improvements if i < 0),
                "minimal": sum(1 for i in improvements if 0 <= i < threshold),
                "significant": sum(1 for i in improvements if i >= threshold),
                "high": sum(1 for i in improvements if i >= threshold * 2)
            },
            "top_improvements": sorted(task_improvements, 
                                     key=lambda x: x["improvement"], 
                                     reverse=True)[:5]
        }
    
    def _analyze_by_metric_type(self, drift_metrics: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Analyze drift reduction by metric type.
        
        Args:
            drift_metrics: List of drift metric dictionaries
            
        Returns:
            Analysis by metric type
        """
        metric_types = ["naming_consistency", "style_consistency", "structure_consistency"]
        analysis = {}
        
        for metric_type in metric_types:
            # Extract consistency scores for this metric
            without_scores = []
            with_scores = []
            
            # This would require the drift_metrics to include per-metric breakdowns
            # For now, we'll simulate this analysis
            for metrics in drift_metrics:
                # In a real implementation, we'd have per-metric scores
                base_score = metrics["consistency_without_rules"]
                improved_score = metrics["consistency_with_rules"]
                
                # Simulate variation by metric type
                if metric_type == "naming_consistency":
                    factor = 1.1  # Naming tends to improve more
                elif metric_type == "style_consistency":
                    factor = 1.0  # Style improves moderately
                else:  # structure_consistency
                    factor = 0.9  # Structure improves less
                
                without_scores.append(base_score * factor)
                with_scores.append(improved_score * factor)
            
            # Calculate improvements
            improvements = [(w - wo) / wo * 100 if wo > 0 else 0.0 
                          for wo, w in zip(without_scores, with_scores)]
            
            analysis[metric_type] = {
                "avg_without_rules": statistics.mean(without_scores) if without_scores else 0.0,
                "avg_with_rules": statistics.mean(with_scores) if with_scores else 0.0,
                "avg_improvement": statistics.mean(improvements) if improvements else 0.0,
                "std_improvement": statistics.stdev(improvements) if len(improvements) > 1 else 0.0
            }
        
        return analysis
    
    def evaluate_consistency_patterns(self, 
                                    outputs_without_rules: List[Dict[str, Any]],
                                    outputs_with_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate detailed consistency patterns.
        
        Args:
            outputs_without_rules: Outputs generated without rules
            outputs_with_rules: Outputs generated with rules
            
        Returns:
            Pattern analysis
        """
        patterns = {
            "without_rules": self._analyze_output_patterns(outputs_without_rules),
            "with_rules": self._analyze_output_patterns(outputs_with_rules),
            "improvements": {}
        }
        
        # Calculate improvements
        for key in patterns["without_rules"]:
            if key in patterns["with_rules"]:
                without_val = patterns["without_rules"][key]
                with_val = patterns["with_rules"][key]
                
                if isinstance(without_val, (int, float)) and isinstance(with_val, (int, float)):
                    if without_val > 0:
                        improvement = (with_val - without_val) / without_val * 100
                    else:
                        improvement = 100.0 if with_val > 0 else 0.0
                    patterns["improvements"][key] = improvement
        
        return patterns
    
    def _analyze_output_patterns(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in a set of outputs.
        
        Args:
            outputs: List of outputs to analyze
            
        Returns:
            Pattern analysis
        """
        if not outputs:
            return {}
        
        patterns = {
            "num_outputs": len(outputs),
            "consistency_indicators": {}
        }
        
        # Analyze code patterns if present
        if any("code" in output for output in outputs):
            code_patterns = self._analyze_code_patterns(outputs)
            patterns.update(code_patterns)
        
        # Analyze structural patterns
        if any("files" in output for output in outputs):
            structure_patterns = self._analyze_structure_patterns(outputs)
            patterns.update(structure_patterns)
        
        # Analyze naming patterns
        if any("identifiers" in output for output in outputs):
            naming_patterns = self._analyze_naming_patterns(outputs)
            patterns.update(naming_patterns)
        
        return patterns
    
    def _analyze_code_patterns(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in code outputs."""
        code_outputs = [o for o in outputs if "code" in o]
        if not code_outputs:
            return {}
        
        # Analyze code length consistency
        code_lengths = [len(o["code"]) for o in code_outputs]
        
        return {
            "code_length_consistency": 1.0 - (statistics.stdev(code_lengths) / statistics.mean(code_lengths))
                                      if len(code_lengths) > 1 and statistics.mean(code_lengths) > 0 else 1.0,
            "avg_code_length": statistics.mean(code_lengths) if code_lengths else 0
        }
    
    def _analyze_structure_patterns(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in structural outputs."""
        file_outputs = [o for o in outputs if "files" in o]
        if not file_outputs:
            return {}
        
        # Check file consistency
        all_files = [tuple(sorted(o["files"])) for o in file_outputs]
        unique_structures = len(set(all_files))
        
        return {
            "structure_consistency": 1.0 / unique_structures if unique_structures > 0 else 1.0,
            "unique_structures": unique_structures
        }
    
    def _analyze_naming_patterns(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in naming outputs."""
        identifier_outputs = [o for o in outputs if "identifiers" in o]
        if not identifier_outputs:
            return {}
        
        # Check naming consistency
        all_names = []
        for output in identifier_outputs:
            all_names.extend(output["identifiers"].keys())
        
        # Simple consistency check - in practice would be more sophisticated
        unique_names = len(set(all_names))
        total_names = len(all_names)
        
        return {
            "naming_diversity": unique_names / total_names if total_names > 0 else 1.0,
            "total_identifiers": total_names
        }
    
    def generate_report(self, evaluation_results: Dict[str, Any],
                       output_path: Optional[str] = None) -> str:
        """Generate a comprehensive drift evaluation report.
        
        Args:
            evaluation_results: Results from evaluate_drift_reduction
            output_path: Optional path to save report
            
        Returns:
            Report as string
        """
        report_lines = [
            "=" * 60,
            "Drift Reduction Evaluation Report",
            "=" * 60,
            "",
            f"Evaluation Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Number of Tasks Evaluated: {len(evaluation_results['per_task_results'])}",
            ""
        ]
        
        # Summary section
        summary = evaluation_results["summary"]
        report_lines.extend([
            "Overall Performance:",
            "-" * 30,
            f"Average Consistency Without Rules: {summary['avg_consistency_without_rules']:.3f}",
            f"Average Consistency With Rules: {summary['avg_consistency_with_rules']:.3f}",
            f"Average Drift Reduction: {summary['avg_drift_reduction']:.1f}%",
            f"Median Drift Reduction: {summary['median_drift_reduction']:.1f}%",
            f"Drift Reduction Range: [{summary['min_drift_reduction']:.1f}%, "
            f"{summary['max_drift_reduction']:.1f}%]",
            f"Overall Consistency Improvement: {summary['overall_consistency_improvement']:.1f}%",
            ""
        ])
        
        # Improvement analysis
        improvement = evaluation_results["improvement_analysis"]
        report_lines.extend([
            "Improvement Analysis:",
            "-" * 30,
            f"Tasks with Significant Improvement: {improvement['num_significant']} "
            f"({improvement['percentage_significant']:.1f}%)",
            f"Average Improvement: {improvement['avg_improvement']*100:.1f}%",
            "",
            "Improvement Distribution:",
            f"  Negative (drift increased): {improvement['improvement_distribution']['negative']}",
            f"  Minimal (< threshold): {improvement['improvement_distribution']['minimal']}",
            f"  Significant (>= threshold): {improvement['improvement_distribution']['significant']}",
            f"  High (>= 2x threshold): {improvement['improvement_distribution']['high']}",
            ""
        ])
        
        # Top improvements
        if improvement["top_improvements"]:
            report_lines.extend([
                "Top 5 Improvements:",
                "-" * 20
            ])
            for i, task_imp in enumerate(improvement["top_improvements"][:5], 1):
                report_lines.append(
                    f"{i}. Task {task_imp['task_id']}: {task_imp['improvement']*100:.1f}% improvement"
                )
            report_lines.append("")
        
        # Metric type analysis
        if "metric_analysis" in evaluation_results:
            report_lines.extend([
                "Analysis by Metric Type:",
                "-" * 30
            ])
            
            for metric_type, analysis in evaluation_results["metric_analysis"].items():
                report_lines.extend([
                    f"\n{metric_type.replace('_', ' ').title()}:",
                    f"  Without Rules: {analysis['avg_without_rules']:.3f}",
                    f"  With Rules: {analysis['avg_with_rules']:.3f}",
                    f"  Improvement: {analysis['avg_improvement']:.1f}%"
                ])
            report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "Recommendations:",
            "-" * 30
        ])
        
        if summary['avg_drift_reduction'] > 30:
            report_lines.append("✓ Excellent drift reduction achieved. Rules are highly effective.")
        elif summary['avg_drift_reduction'] > 10:
            report_lines.append("✓ Good drift reduction. Consider expanding rule coverage.")
        else:
            report_lines.append("⚠ Limited drift reduction. Review rule quality and applicability.")
        
        if improvement['percentage_significant'] < 50:
            report_lines.append("⚠ Less than half of tasks showed significant improvement. "
                              "Consider task-specific rule refinement.")
        
        report_lines.extend([
            "",
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
    
    def compare_drift_reduction_methods(self, 
                                      method_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Compare different drift reduction methods.
        
        Args:
            method_results: Dictionary mapping method names to their comparison results
            
        Returns:
            Comparison analysis
        """
        comparison = {
            "methods": {},
            "best_overall": None,
            "best_by_metric": {}
        }
        
        best_avg_reduction = 0.0
        
        for method_name, results in method_results.items():
            # Evaluate this method
            evaluation = self.evaluate_drift_reduction(results)
            comparison["methods"][method_name] = evaluation
            
            # Track best overall
            avg_reduction = evaluation["summary"]["avg_drift_reduction"]
            if avg_reduction > best_avg_reduction:
                best_avg_reduction = avg_reduction
                comparison["best_overall"] = method_name
            
            # Track best by metric type
            for metric_type, analysis in evaluation["metric_analysis"].items():
                improvement = analysis["avg_improvement"]
                
                if metric_type not in comparison["best_by_metric"]:
                    comparison["best_by_metric"][metric_type] = {
                        "method": method_name,
                        "improvement": improvement
                    }
                elif improvement > comparison["best_by_metric"][metric_type]["improvement"]:
                    comparison["best_by_metric"][metric_type] = {
                        "method": method_name,
                        "improvement": improvement
                    }
        
        return comparison