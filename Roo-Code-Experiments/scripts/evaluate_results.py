#!/usr/bin/env python3
"""Evaluate and analyze results from the LTM pipeline."""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ltm_pipeline.utils.file_io import FileIO


class ResultsAnalyzer:
    """Analyze and visualize pipeline results."""
    
    def __init__(self, results_dir: str):
        """Initialize the analyzer.
        
        Args:
            results_dir: Directory containing pipeline results
        """
        self.results_dir = Path(results_dir)
        self.results = self._load_results()
    
    def _load_results(self) -> Dict[str, Any]:
        """Load all results from the results directory."""
        results = {}
        
        # Load extraction results
        extraction_dir = self.results_dir / "extraction"
        if extraction_dir.exists():
            metrics_file = extraction_dir / "extraction_metrics.json"
            if metrics_file.exists():
                results["extraction"] = FileIO.read_json(metrics_file)
        
        # Load storage decision results
        decision_dir = self.results_dir / "storage_decision"
        if decision_dir.exists():
            metrics_file = decision_dir / "decision_metrics.json"
            if metrics_file.exists():
                results["storage_decision"] = FileIO.read_json(metrics_file)
        
        # Load retrieval results
        retrieval_dir = self.results_dir / "retrieval_application"
        if retrieval_dir.exists():
            metrics_file = retrieval_dir / "retrieval_metrics.json"
            if metrics_file.exists():
                results["retrieval_application"] = FileIO.read_json(metrics_file)
        
        # Load drift reduction results
        drift_dir = self.results_dir / "drift_reduction"
        if drift_dir.exists():
            metrics_file = drift_dir / "drift_metrics.json"
            if metrics_file.exists():
                results["drift_reduction"] = FileIO.read_json(metrics_file)
        
        # Load pipeline summary if available
        pipeline_results = self.results_dir / "pipeline_results.json"
        if pipeline_results.exists():
            results["pipeline_summary"] = FileIO.read_json(pipeline_results)
        
        return results
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report."""
        report_lines = [
            "=" * 80,
            "LTM Pipeline Results Summary",
            "=" * 80,
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Results Directory: {self.results_dir}",
            ""
        ]
        
        # Extraction results
        if "extraction" in self.results:
            extraction = self.results["extraction"]
            report_lines.extend([
                "Rule Extraction Performance:",
                "-" * 40,
                f"  Precision: {extraction.get('precision', 'N/A'):.3f}" if isinstance(extraction.get('precision'), (int, float)) else "  Precision: N/A",
                f"  Recall: {extraction.get('recall', 'N/A'):.3f}" if isinstance(extraction.get('recall'), (int, float)) else "  Recall: N/A",
                f"  F1 Score: {extraction.get('f1_score', 'N/A'):.3f}" if isinstance(extraction.get('f1_score'), (int, float)) else "  F1 Score: N/A",
                ""
            ])
        
        # Storage decision results
        if "storage_decision" in self.results:
            decision = self.results["storage_decision"]
            report_lines.extend([
                "Storage Decision Performance:",
                "-" * 40,
                f"  Agreement Rate: {decision.get('agreement_rate', 'N/A'):.3f}" if isinstance(decision.get('agreement_rate'), (int, float)) else "  Agreement Rate: N/A",
                f"  Precision: {decision.get('precision', 'N/A'):.3f}" if isinstance(decision.get('precision'), (int, float)) else "  Precision: N/A",
                f"  Recall: {decision.get('recall', 'N/A'):.3f}" if isinstance(decision.get('recall'), (int, float)) else "  Recall: N/A",
                ""
            ])
        
        # Retrieval & Application results
        if "retrieval_application" in self.results:
            retrieval = self.results["retrieval_application"]
            if "overall" in retrieval:
                report_lines.extend([
                    "Retrieval & Application Performance:",
                    "-" * 40,
                    "  Retrieval:",
                    f"    Precision: {retrieval['overall']['retrieval']['precision']:.3f}",
                    f"    Recall: {retrieval['overall']['retrieval']['recall']:.3f}",
                    f"    F1 Score: {retrieval['overall']['retrieval']['f1_score']:.3f}",
                    "  Application:",
                    f"    Precision: {retrieval['overall']['application']['precision']:.3f}",
                    f"    Recall: {retrieval['overall']['application']['recall']:.3f}",
                    f"    F1 Score: {retrieval['overall']['application']['f1_score']:.3f}",
                    ""
                ])
        
        # Drift reduction results
        if "drift_reduction" in self.results:
            drift = self.results["drift_reduction"]
            if "summary" in drift:
                summary = drift["summary"]
                report_lines.extend([
                    "Drift Reduction Performance:",
                    "-" * 40,
                    f"  Average Drift Reduction: {summary['avg_drift_reduction']:.1f}%",
                    f"  Consistency Without Rules: {summary['avg_consistency_without_rules']:.3f}",
                    f"  Consistency With Rules: {summary['avg_consistency_with_rules']:.3f}",
                    f"  Overall Improvement: {summary['overall_consistency_improvement']:.1f}%",
                    ""
                ])
        
        # Pipeline summary
        if "pipeline_summary" in self.results:
            stages = self.results["pipeline_summary"].get("stages", {})
            report_lines.extend([
                "Pipeline Execution Summary:",
                "-" * 40
            ])
            
            for stage, data in stages.items():
                if isinstance(data, dict):
                    report_lines.append(f"  {stage}:")
                    for key, value in data.items():
                        if key != "metrics" and not key.endswith("_rules"):
                            report_lines.append(f"    {key}: {value}")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 80,
            "End of Summary Report",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def plot_extraction_metrics(self, output_path: Optional[str] = None):
        """Plot rule extraction metrics."""
        if "extraction" not in self.results:
            print("No extraction results found")
            return
        
        extraction = self.results["extraction"]
        
        # Check if we have by_type metrics
        if "by_type" in extraction:
            # Create subplot for each metric type
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle("Rule Extraction Performance by Type", fontsize=16)
            
            rule_types = list(extraction["by_type"].keys())
            metrics = ["precision", "recall", "f1_score"]
            
            for idx, metric in enumerate(metrics):
                ax = axes[idx // 2, idx % 2]
                values = [extraction["by_type"][rt].get(metric, 0) for rt in rule_types]
                
                bars = ax.bar(rule_types, values)
                ax.set_title(f"{metric.replace('_', ' ').title()}")
                ax.set_ylim(0, 1.0)
                ax.set_ylabel("Score")
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:.2f}', ha='center', va='bottom')
            
            # Use the last subplot for counts
            ax = axes[1, 1]
            gt_counts = [extraction["by_type"][rt].get("ground_truth_count", 0) for rt in rule_types]
            ext_counts = [extraction["by_type"][rt].get("extracted_count", 0) for rt in rule_types]
            
            x = range(len(rule_types))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], gt_counts, width, label='Ground Truth')
            ax.bar([i + width/2 for i in x], ext_counts, width, label='Extracted')
            ax.set_title("Rule Counts by Type")
            ax.set_xticks(x)
            ax.set_xticklabels(rule_types)
            ax.legend()
            
            plt.tight_layout()
        else:
            # Simple bar chart for overall metrics
            fig, ax = plt.subplots(figsize=(8, 6))
            
            metrics = ["precision", "recall", "f1_score"]
            values = [extraction.get(m, 0) for m in metrics]
            
            bars = ax.bar(metrics, values)
            ax.set_title("Overall Rule Extraction Performance")
            ax.set_ylim(0, 1.0)
            ax.set_ylabel("Score")
            
            # Add value labels
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.3f}', ha='center', va='bottom')
        
        if output_path:
            plt.savefig(output_path)
        else:
            plt.show()
    
    def plot_drift_reduction(self, output_path: Optional[str] = None):
        """Plot drift reduction results."""
        if "drift_reduction" not in self.results:
            print("No drift reduction results found")
            return
        
        drift = self.results["drift_reduction"]
        
        if "per_task_results" in drift:
            # Create visualization of drift reduction per task
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Extract data
            task_ids = [r["task_id"] for r in drift["per_task_results"]]
            consistency_without = [r["consistency_without_rules"] for r in drift["per_task_results"]]
            consistency_with = [r["consistency_with_rules"] for r in drift["per_task_results"]]
            drift_reductions = [r["drift_reduction_percentage"] for r in drift["per_task_results"]]
            
            # Plot 1: Consistency comparison
            x = range(len(task_ids))
            width = 0.35
            
            bars1 = ax1.bar([i - width/2 for i in x], consistency_without, width, 
                           label='Without Rules', color='lightcoral')
            bars2 = ax1.bar([i + width/2 for i in x], consistency_with, width, 
                           label='With Rules', color='lightgreen')
            
            ax1.set_xlabel('Task')
            ax1.set_ylabel('Consistency Score')
            ax1.set_title('Consistency Comparison: With vs Without Rules')
            ax1.set_xticks(x)
            ax1.set_xticklabels([f"T{i+1}" for i in x], rotation=45)
            ax1.legend()
            ax1.set_ylim(0, 1.1)
            
            # Plot 2: Drift reduction percentages
            bars3 = ax2.bar(x, drift_reductions, color='skyblue')
            ax2.set_xlabel('Task')
            ax2.set_ylabel('Drift Reduction (%)')
            ax2.set_title('Drift Reduction by Task')
            ax2.set_xticks(x)
            ax2.set_xticklabels([f"T{i+1}" for i in x], rotation=45)
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            
            # Add average line
            avg_reduction = drift["summary"]["avg_drift_reduction"]
            ax2.axhline(y=avg_reduction, color='red', linestyle='--', 
                       label=f'Average: {avg_reduction:.1f}%')
            ax2.legend()
            
            plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path)
        else:
            plt.show()
    
    def export_metrics_csv(self, output_path: str):
        """Export all metrics to CSV format."""
        metrics_data = []
        
        # Extraction metrics
        if "extraction" in self.results:
            extraction = self.results["extraction"]
            metrics_data.append({
                "Stage": "Rule Extraction",
                "Metric": "Precision",
                "Value": extraction.get("precision", "N/A")
            })
            metrics_data.append({
                "Stage": "Rule Extraction",
                "Metric": "Recall",
                "Value": extraction.get("recall", "N/A")
            })
            metrics_data.append({
                "Stage": "Rule Extraction",
                "Metric": "F1 Score",
                "Value": extraction.get("f1_score", "N/A")
            })
        
        # Storage decision metrics
        if "storage_decision" in self.results:
            decision = self.results["storage_decision"]
            metrics_data.append({
                "Stage": "Storage Decision",
                "Metric": "Agreement Rate",
                "Value": decision.get("agreement_rate", "N/A")
            })
        
        # Retrieval metrics
        if "retrieval_application" in self.results:
            retrieval = self.results["retrieval_application"]
            if "overall" in retrieval:
                metrics_data.append({
                    "Stage": "Retrieval",
                    "Metric": "F1 Score",
                    "Value": retrieval["overall"]["retrieval"]["f1_score"]
                })
                metrics_data.append({
                    "Stage": "Application",
                    "Metric": "F1 Score",
                    "Value": retrieval["overall"]["application"]["f1_score"]
                })
        
        # Drift reduction metrics
        if "drift_reduction" in self.results:
            drift = self.results["drift_reduction"]
            if "summary" in drift:
                metrics_data.append({
                    "Stage": "Drift Reduction",
                    "Metric": "Average Reduction",
                    "Value": f"{drift['summary']['avg_drift_reduction']:.1f}%"
                })
        
        # Create DataFrame and save
        df = pd.DataFrame(metrics_data)
        df.to_csv(output_path, index=False)
        print(f"Metrics exported to {output_path}")
    
    def compare_runs(self, other_results_dir: str) -> Dict[str, Any]:
        """Compare results from two different pipeline runs."""
        other_analyzer = ResultsAnalyzer(other_results_dir)
        
        comparison = {
            "run1": str(self.results_dir),
            "run2": str(other_results_dir),
            "improvements": {}
        }
        
        # Compare extraction metrics
        if "extraction" in self.results and "extraction" in other_analyzer.results:
            f1_1 = self.results["extraction"].get("f1_score", 0)
            f1_2 = other_analyzer.results["extraction"].get("f1_score", 0)
            comparison["improvements"]["extraction_f1"] = {
                "run1": f1_1,
                "run2": f1_2,
                "improvement": f1_2 - f1_1
            }
        
        # Compare drift reduction
        if "drift_reduction" in self.results and "drift_reduction" in other_analyzer.results:
            drift_1 = self.results["drift_reduction"]["summary"]["avg_drift_reduction"]
            drift_2 = other_analyzer.results["drift_reduction"]["summary"]["avg_drift_reduction"]
            comparison["improvements"]["drift_reduction"] = {
                "run1": drift_1,
                "run2": drift_2,
                "improvement": drift_2 - drift_1
            }
        
        return comparison


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate and analyze LTM pipeline results"
    )
    
    parser.add_argument(
        "--results",
        required=True,
        help="Path to results directory"
    )
    
    parser.add_argument(
        "--action",
        choices=["summary", "plot-extraction", "plot-drift", "export-csv", "compare"],
        default="summary",
        help="Analysis action to perform"
    )
    
    parser.add_argument(
        "--output",
        help="Output file path (for plots and exports)"
    )
    
    parser.add_argument(
        "--compare-with",
        help="Path to another results directory for comparison"
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = ResultsAnalyzer(args.results)
    
    # Perform requested action
    if args.action == "summary":
        report = analyzer.generate_summary_report()
        print(report)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"\nReport saved to {args.output}")
    
    elif args.action == "plot-extraction":
        analyzer.plot_extraction_metrics(args.output)
        if not args.output:
            print("Plot displayed. Use --output to save to file.")
    
    elif args.action == "plot-drift":
        analyzer.plot_drift_reduction(args.output)
        if not args.output:
            print("Plot displayed. Use --output to save to file.")
    
    elif args.action == "export-csv":
        if not args.output:
            print("Error: --output required for CSV export")
            return
        analyzer.export_metrics_csv(args.output)
    
    elif args.action == "compare":
        if not args.compare_with:
            print("Error: --compare-with required for comparison")
            return
        
        comparison = analyzer.compare_runs(args.compare_with)
        print(f"\nComparison Results:")
        print(f"Run 1: {comparison['run1']}")
        print(f"Run 2: {comparison['run2']}")
        print("\nImprovements:")
        for metric, data in comparison["improvements"].items():
            print(f"  {metric}:")
            print(f"    Run 1: {data['run1']:.3f}")
            print(f"    Run 2: {data['run2']:.3f}")
            print(f"    Change: {data['improvement']:+.3f}")


if __name__ == "__main__":
    # Check if matplotlib is available
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
    except ImportError:
        print("Warning: matplotlib not available. Plotting functions will not work.")
        print("Install with: pip install matplotlib")
    
    main()