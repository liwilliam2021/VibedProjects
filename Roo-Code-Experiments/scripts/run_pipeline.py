#!/usr/bin/env python3
"""Main pipeline runner for the LTM validation system."""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ltm_pipeline.utils.file_io import FileIO, ConfigLoader
from ltm_pipeline.utils.data_generator import SyntheticDataGenerator
from ltm_pipeline.common.models import Transcript, Rule, Task
from ltm_pipeline.common.logger import LoggerFactory

# Import pipeline modules
from ltm_pipeline.rule_extraction import RuleExtractor, ExtractionEvaluator
from ltm_pipeline.storage_decision import StorageDecisionMaker, DecisionEvaluator
from ltm_pipeline.retrieval_application import (
    SimulatedLTMStorage, RuleRetriever, RuleApplicator, RetrievalEvaluator
)
from ltm_pipeline.drift_reduction import ConsistencyChecker, TaskRunner, DriftEvaluator


class LTMPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, config_path: str):
        """Initialize the pipeline with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigLoader.load_config(config_path)
        
        # Configure logging
        LoggerFactory.configure(
            log_dir=self.config["logging"]["output_dir"],
            level=self.config["logging"]["level"]
        )
        
        self.logger = LoggerFactory.get_logger("LTMPipeline")
        self.logger.info(f"Initialized pipeline with config: {config_path}")
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all pipeline components."""
        # Data generator
        self.data_generator = SyntheticDataGenerator(
            seed=self.config["data_generation"]["seed"]
        )
        
        # Rule extraction
        self.rule_extractor = RuleExtractor(
            extraction_patterns=self.config["extraction"]["patterns"],
            confidence_threshold=self.config["extraction"]["confidence_threshold"]
        )
        self.extraction_evaluator = ExtractionEvaluator()
        
        # Storage decision
        self.storage_decision_maker = StorageDecisionMaker(
            criteria_weights=self.config["storage_decision"]["criteria_weights"],
            storage_threshold=self.config["storage_decision"]["storage_threshold"]
        )
        self.decision_evaluator = DecisionEvaluator()
        
        # Retrieval & Application
        self.ltm_storage = SimulatedLTMStorage()
        self.rule_retriever = RuleRetriever(
            self.ltm_storage,
            similarity_threshold=self.config["retrieval"]["similarity_threshold"]
        )
        self.rule_applicator = RuleApplicator(self.ltm_storage, self.rule_retriever)
        self.retrieval_evaluator = RetrievalEvaluator()
        
        # Drift reduction
        self.consistency_checker = ConsistencyChecker(
            similarity_metrics=self.config["drift_reduction"]["metrics"],
            weights=self.config["drift_reduction"]["consistency_weights"]
        )
        self.task_runner = TaskRunner(self.ltm_storage)
        self.drift_evaluator = DriftEvaluator(self.consistency_checker)
    
    def run_full_pipeline(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Run the complete pipeline.
        
        Args:
            input_dir: Directory containing input data
            output_dir: Directory for output results
            
        Returns:
            Pipeline results
        """
        self.logger.info("Starting full pipeline run")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "stages": {}
        }
        
        # Stage 1: Rule Extraction
        self.logger.info("Stage 1: Rule Extraction")
        extraction_results = self._run_extraction_stage(input_dir, output_dir)
        results["stages"]["extraction"] = extraction_results
        
        # Stage 2: Storage Decision
        self.logger.info("Stage 2: Storage Decision")
        decision_results = self._run_storage_decision_stage(
            extraction_results["extracted_rules"], output_dir
        )
        results["stages"]["storage_decision"] = decision_results
        
        # Store approved rules
        approved_rules = decision_results["approved_rules"]
        self.ltm_storage.store_rules(approved_rules)
        self.logger.info(f"Stored {len(approved_rules)} rules in LTM")
        
        # Stage 3: Retrieval & Application
        self.logger.info("Stage 3: Retrieval & Application")
        retrieval_results = self._run_retrieval_application_stage(input_dir, output_dir)
        results["stages"]["retrieval_application"] = retrieval_results
        
        # Stage 4: Drift Reduction
        self.logger.info("Stage 4: Drift Reduction")
        drift_results = self._run_drift_reduction_stage(input_dir, output_dir)
        results["stages"]["drift_reduction"] = drift_results
        
        # Save overall results
        results_path = Path(output_dir) / "pipeline_results.json"
        FileIO.write_json(results, results_path)
        
        self.logger.info(f"Pipeline complete. Results saved to {results_path}")
        return results
    
    def _run_extraction_stage(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Run rule extraction stage."""
        # Load transcripts
        transcript_files = FileIO.list_files(
            Path(input_dir) / "transcripts", "*.json"
        )
        
        all_extracted_rules = []
        all_ground_truth = []
        
        for transcript_file in transcript_files[:10]:  # Limit for demo
            # Load transcript
            transcript_data = FileIO.read_json(transcript_file)
            transcript = Transcript.from_dict(transcript_data)
            
            # Extract rules
            extracted_rules = self.rule_extractor.extract_rules(transcript)
            all_extracted_rules.extend(extracted_rules)
            
            # Load ground truth if available
            gt_file = Path(input_dir) / "ground_truth" / f"{transcript.id}_rules.json"
            if gt_file.exists():
                gt_data = FileIO.read_json(gt_file)
                ground_truth_rules = [Rule.from_dict(r) for r in gt_data]
                all_ground_truth.extend(ground_truth_rules)
        
        # Evaluate extraction
        if all_ground_truth:
            metrics = self.extraction_evaluator.evaluate(
                all_extracted_rules, all_ground_truth
            )
        else:
            metrics = {"note": "No ground truth available for evaluation"}
        
        # Save results
        extraction_output = Path(output_dir) / "extraction"
        extraction_output.mkdir(parents=True, exist_ok=True)
        
        FileIO.write_json(
            {"rules": [r.to_dict() for r in all_extracted_rules]},
            extraction_output / "extracted_rules.json"
        )
        
        FileIO.write_json(metrics, extraction_output / "extraction_metrics.json")
        
        return {
            "extracted_rules": all_extracted_rules,
            "metrics": metrics,
            "num_transcripts": len(transcript_files[:10]),
            "num_rules": len(all_extracted_rules)
        }
    
    def _run_storage_decision_stage(self, rules: List[Rule], 
                                   output_dir: str) -> Dict[str, Any]:
        """Run storage decision stage."""
        # Evaluate rules for storage
        evaluation_results = self.storage_decision_maker.evaluate_rules(rules)
        
        # Separate approved and rejected rules
        approved_rules = []
        rejected_rules = []
        
        for rule, decision, justification in evaluation_results:
            if decision == "store":
                approved_rules.append(rule)
            else:
                rejected_rules.append(rule)
        
        # Create storage decisions for evaluation
        storage_decisions = self.storage_decision_maker.create_storage_decisions(
            evaluation_results
        )
        
        # Evaluate if ground truth available
        # For demo, we'll use a simple heuristic
        ground_truth_decisions = [
            {"rule_id": rule.id, "decision": "store" if rule.confidence > 0.8 else "ignore"}
            for rule in rules
        ]
        
        metrics = self.decision_evaluator.evaluate(storage_decisions, ground_truth_decisions)
        
        # Save results
        decision_output = Path(output_dir) / "storage_decision"
        decision_output.mkdir(parents=True, exist_ok=True)
        
        FileIO.write_json(
            {
                "approved": [r.to_dict() for r in approved_rules],
                "rejected": [r.to_dict() for r in rejected_rules]
            },
            decision_output / "storage_decisions.json"
        )
        
        FileIO.write_json(metrics, decision_output / "decision_metrics.json")
        
        return {
            "approved_rules": approved_rules,
            "rejected_rules": rejected_rules,
            "metrics": metrics,
            "approval_rate": len(approved_rules) / len(rules) if rules else 0.0
        }
    
    def _run_retrieval_application_stage(self, input_dir: str, 
                                        output_dir: str) -> Dict[str, Any]:
        """Run retrieval and application stage."""
        # Load or generate test tasks
        task_file = Path(input_dir) / "test_tasks" / "tasks.json"
        if task_file.exists():
            tasks_data = FileIO.read_json(task_file)
            tasks = [Task.from_dict(t) for t in tasks_data]
        else:
            # Generate test tasks
            tasks = [
                self.data_generator.generate_test_task(["naming", "style"])
                for _ in range(5)
            ]
        
        # Run retrieval and application for each task
        all_results = []
        
        for task in tasks:
            # Retrieve rules
            retrieved_rules = self.rule_retriever.retrieve_for_task(task)
            
            # Apply rules
            application_result = self.rule_applicator.apply_rules_to_task(
                task, retrieved_rules
            )
            
            # Create ground truth (for demo)
            ground_truth = {
                "expected_retrievals": [r.id for r in retrieved_rules[:3]],
                "expected_applications": [r.id for r in retrieved_rules[:2]]
            }
            
            # Evaluate
            result = {
                "task": task,
                "retrieved_rules": retrieved_rules,
                "application_result": application_result,
                "ground_truth": ground_truth
            }
            all_results.append(result)
        
        # Batch evaluation
        batch_metrics = self.retrieval_evaluator.evaluate_batch(all_results)
        
        # Save results
        retrieval_output = Path(output_dir) / "retrieval_application"
        retrieval_output.mkdir(parents=True, exist_ok=True)
        
        FileIO.write_json(
            {
                "tasks": [r["task"].to_dict() for r in all_results],
                "retrievals": [
                    {
                        "task_id": r["task"].id,
                        "retrieved_rules": [rule.id for rule in r["retrieved_rules"]]
                    }
                    for r in all_results
                ],
                "applications": [
                    r["application_result"].to_dict() for r in all_results
                ]
            },
            retrieval_output / "retrieval_application_results.json"
        )
        
        FileIO.write_json(batch_metrics, retrieval_output / "retrieval_metrics.json")
        
        # Generate report
        report = self.retrieval_evaluator.generate_report(batch_metrics)
        with open(retrieval_output / "retrieval_report.txt", 'w') as f:
            f.write(report)
        
        return {
            "num_tasks": len(tasks),
            "metrics": batch_metrics,
            "avg_rules_retrieved": sum(len(r["retrieved_rules"]) for r in all_results) / len(all_results)
        }
    
    def _run_drift_reduction_stage(self, input_dir: str, 
                                  output_dir: str) -> Dict[str, Any]:
        """Run drift reduction stage."""
        # Load or generate tasks for drift testing
        task_file = Path(input_dir) / "test_tasks" / "drift_tasks.json"
        if task_file.exists():
            tasks_data = FileIO.read_json(task_file)
            tasks = [Task.from_dict(t) for t in tasks_data]
        else:
            # Generate tasks
            tasks = [
                self.data_generator.generate_test_task(["naming", "style", "structure"])
                for _ in range(3)
            ]
        
        # Run comparisons
        comparison_results = self.task_runner.run_batch_comparison(
            tasks, num_runs_per_task=5
        )
        
        # Evaluate drift reduction
        drift_evaluation = self.drift_evaluator.evaluate_drift_reduction(
            comparison_results,
            improvement_threshold=self.config["drift_reduction"]["improvement_threshold"]
        )
        
        # Save results
        drift_output = Path(output_dir) / "drift_reduction"
        drift_output.mkdir(parents=True, exist_ok=True)
        
        FileIO.write_json(
            {
                "comparisons": [
                    {
                        "task_id": comp["task_id"],
                        "num_outputs_without_rules": len(comp["outputs_without_rules"]),
                        "num_outputs_with_rules": len(comp["outputs_with_rules"]),
                        "summary": comp["summary"]
                    }
                    for comp in comparison_results
                ]
            },
            drift_output / "drift_comparison_results.json"
        )
        
        FileIO.write_json(drift_evaluation, drift_output / "drift_metrics.json")
        
        # Generate report
        report = self.drift_evaluator.generate_report(drift_evaluation)
        with open(drift_output / "drift_report.txt", 'w') as f:
            f.write(report)
        
        return {
            "num_tasks": len(tasks),
            "avg_drift_reduction": drift_evaluation["summary"]["avg_drift_reduction"],
            "significant_improvements": drift_evaluation["improvement_analysis"]["num_significant"]
        }
    
    def run_single_stage(self, stage: str, input_path: str, output_path: str) -> Dict[str, Any]:
        """Run a single pipeline stage.
        
        Args:
            stage: Stage to run (extract, decide, retrieve, drift)
            input_path: Input file/directory path
            output_path: Output file/directory path
            
        Returns:
            Stage results
        """
        self.logger.info(f"Running single stage: {stage}")
        
        if stage == "extract":
            # Load transcript
            transcript_data = FileIO.read_json(input_path)
            transcript = Transcript.from_dict(transcript_data)
            
            # Extract rules
            rules = self.rule_extractor.extract_rules(transcript)
            
            # Save results
            FileIO.write_json(
                {"rules": [r.to_dict() for r in rules]},
                output_path
            )
            
            return {"num_rules": len(rules)}
        
        elif stage == "decide":
            # Load rules
            rules_data = FileIO.read_json(input_path)
            rules = [Rule.from_dict(r) for r in rules_data["rules"]]
            
            # Make storage decisions
            results = self.storage_decision_maker.evaluate_rules(rules)
            
            # Save results
            decisions = []
            for rule, decision, justification in results:
                decisions.append({
                    "rule_id": rule.id,
                    "decision": decision,
                    "justification": justification
                })
            
            FileIO.write_json({"decisions": decisions}, output_path)
            
            return {"num_decisions": len(decisions)}
        
        elif stage == "retrieve":
            # Load task
            task_data = FileIO.read_json(input_path)
            task = Task.from_dict(task_data)
            
            # Retrieve and apply rules
            retrieved_rules = self.rule_retriever.retrieve_for_task(task)
            application_result = self.rule_applicator.apply_rules_to_task(
                task, retrieved_rules
            )
            
            # Save results
            FileIO.write_json(
                {
                    "retrieved_rules": [r.to_dict() for r in retrieved_rules],
                    "application_result": application_result.to_dict()
                },
                output_path
            )
            
            return {
                "num_retrieved": len(retrieved_rules),
                "num_applied": len(application_result.applied_rules)
            }
        
        elif stage == "drift":
            # Load task
            task_data = FileIO.read_json(input_path)
            task = Task.from_dict(task_data)
            
            # Run comparison
            comparison = self.task_runner.run_comparison(task, num_runs=5)
            
            # Calculate drift
            drift_metrics = self.consistency_checker.calculate_drift(
                comparison["outputs_without_rules"],
                comparison["outputs_with_rules"]
            )
            
            # Save results
            FileIO.write_json(
                {
                    "task_id": task.id,
                    "drift_metrics": drift_metrics,
                    "summary": comparison["summary"]
                },
                output_path
            )
            
            return drift_metrics
        
        else:
            raise ValueError(f"Unknown stage: {stage}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LTM Validation Pipeline Runner"
    )
    
    parser.add_argument(
        "--stage",
        choices=["all", "extract", "decide", "retrieve", "drift"],
        default="all",
        help="Pipeline stage to run"
    )
    
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--input",
        required=True,
        help="Input file or directory"
    )
    
    parser.add_argument(
        "--output",
        required=True,
        help="Output file or directory"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = LTMPipeline(args.config)
    
    # Run requested stage
    if args.stage == "all":
        results = pipeline.run_full_pipeline(args.input, args.output)
    else:
        results = pipeline.run_single_stage(args.stage, args.input, args.output)
    
    # Print summary
    print(f"\nPipeline stage '{args.stage}' completed successfully!")
    print(f"Results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()