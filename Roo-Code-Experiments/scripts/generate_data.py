#!/usr/bin/env python3
"""Generate synthetic data for testing the LTM pipeline."""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ltm_pipeline.utils.data_generator import SyntheticDataGenerator
from ltm_pipeline.utils.file_io import FileIO
from ltm_pipeline.common.models import Rule, Task, Transcript


def generate_transcripts(generator: SyntheticDataGenerator, 
                        output_dir: Path,
                        num_transcripts: int = 10) -> List[Dict[str, Any]]:
    """Generate synthetic transcripts with varying rule mixes.
    
    Args:
        generator: Data generator instance
        output_dir: Output directory
        num_transcripts: Number of transcripts to generate
        
    Returns:
        List of generated transcript data
    """
    print(f"Generating {num_transcripts} synthetic transcripts...")
    
    # Define different rule mix presets
    rule_mixes = [
        {"persistent": 0.5, "short_term": 0.2, "irrelevant": 0.3},  # Balanced
        {"persistent": 0.7, "short_term": 0.1, "irrelevant": 0.2},  # Rule-heavy
        {"persistent": 0.3, "short_term": 0.4, "irrelevant": 0.3},  # Short-term heavy
        {"persistent": 0.2, "short_term": 0.2, "irrelevant": 0.6},  # Noisy
    ]
    
    transcripts_dir = output_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    ground_truth_dir = output_dir / "ground_truth"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    
    generated_transcripts = []
    
    for i in range(num_transcripts):
        # Select rule mix
        rule_mix = rule_mixes[i % len(rule_mixes)]
        
        # Generate transcript
        transcript = generator.generate_transcript(
            rule_mix=rule_mix,
            num_segments=20 + (i % 10) * 5  # Vary length
        )
        
        # Save transcript
        transcript_data = transcript.to_dict()
        FileIO.write_json(
            transcript_data,
            transcripts_dir / f"{transcript.id}.json"
        )
        
        # Generate and save ground truth rules
        ground_truth_rules = generator.generate_ground_truth(transcript)
        ground_truth_data = [rule.to_dict() for rule in ground_truth_rules]
        
        FileIO.write_json(
            ground_truth_data,
            ground_truth_dir / f"{transcript.id}_rules.json"
        )
        
        generated_transcripts.append({
            "transcript": transcript_data,
            "ground_truth": ground_truth_data,
            "rule_mix": rule_mix
        })
        
        print(f"  Generated transcript {transcript.id} with {len(ground_truth_rules)} ground truth rules")
    
    return generated_transcripts


def generate_test_tasks(generator: SyntheticDataGenerator,
                       output_dir: Path,
                       num_tasks: int = 20) -> List[Dict[str, Any]]:
    """Generate test tasks for retrieval and application testing.
    
    Args:
        generator: Data generator instance
        output_dir: Output directory
        num_tasks: Number of tasks to generate
        
    Returns:
        List of generated task data
    """
    print(f"Generating {num_tasks} test tasks...")
    
    tasks_dir = output_dir / "test_tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    
    # Task configurations
    task_configs = [
        {"rule_types": ["naming"], "language": "JavaScript"},
        {"rule_types": ["style"], "language": "Python"},
        {"rule_types": ["structure"], "language": "TypeScript"},
        {"rule_types": ["behavior"], "language": "Java"},
        {"rule_types": ["naming", "style"], "language": "JavaScript"},
        {"rule_types": ["structure", "behavior"], "language": "Python"},
    ]
    
    all_tasks = []
    drift_tasks = []
    
    for i in range(num_tasks):
        config = task_configs[i % len(task_configs)]
        
        # Generate task
        task = generator.generate_test_task(
            rule_types=config["rule_types"],
            language=config["language"]
        )
        
        task_data = task.to_dict()
        all_tasks.append(task_data)
        
        # Select some tasks for drift testing
        if i % 3 == 0:
            drift_tasks.append(task_data)
        
        print(f"  Generated task {task.id} ({config['language']}, {config['rule_types']})")
    
    # Save all tasks
    FileIO.write_json(
        all_tasks,
        tasks_dir / "tasks.json"
    )
    
    # Save drift testing tasks
    FileIO.write_json(
        drift_tasks,
        tasks_dir / "drift_tasks.json"
    )
    
    return all_tasks


def generate_example_rules(output_dir: Path) -> List[Dict[str, Any]]:
    """Generate example rules for testing.
    
    Args:
        output_dir: Output directory
        
    Returns:
        List of generated rule data
    """
    print("Generating example rules...")
    
    rules_dir = output_dir / "example_rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    example_rules = [
        {
            "id": "rule_naming_001",
            "match_criteria": {
                "type": "pattern",
                "value": "javascript.*variable",
                "context": {"language": "JavaScript"}
            },
            "action": {
                "type": "naming",
                "description": "Always use camelCase for JavaScript variables",
                "parameters": {"convention": "camelCase", "construct": "variables"}
            },
            "rationale": "JavaScript convention for variable naming",
            "confidence": 0.95
        },
        {
            "id": "rule_style_001",
            "match_criteria": {
                "type": "keyword",
                "value": "indentation",
                "context": {"file_type": "source_code"}
            },
            "action": {
                "type": "style",
                "description": "Use 4 spaces for indentation",
                "parameters": {"amount": "4", "unit": "spaces"}
            },
            "rationale": "Project standard for code indentation",
            "confidence": 0.9
        },
        {
            "id": "rule_structure_001",
            "match_criteria": {
                "type": "context",
                "value": "project_structure",
                "context": {"target": "components"}
            },
            "action": {
                "type": "structure",
                "description": "Organize components by feature",
                "parameters": {"action": "organize", "target": "components"}
            },
            "rationale": "Improves code organization and maintainability",
            "confidence": 0.85
        },
        {
            "id": "rule_behavior_001",
            "match_criteria": {
                "type": "pattern",
                "value": "validate.*input",
                "context": {"modifier": "always"}
            },
            "action": {
                "type": "behavior",
                "description": "Always validate user input before processing",
                "parameters": {"modifier": "always", "action": "validate", "condition": "processing"}
            },
            "rationale": "Security best practice",
            "confidence": 0.98
        }
    ]
    
    # Save example rules
    FileIO.write_json(
        example_rules,
        rules_dir / "example_rules.json"
    )
    
    print(f"  Generated {len(example_rules)} example rules")
    
    return example_rules


def generate_storage_decisions_ground_truth(rules: List[Dict[str, Any]], 
                                          output_dir: Path) -> List[Dict[str, str]]:
    """Generate ground truth storage decisions for rules.
    
    Args:
        rules: List of rules
        output_dir: Output directory
        
    Returns:
        List of ground truth decisions
    """
    print("Generating ground truth storage decisions...")
    
    ground_truth_dir = output_dir / "ground_truth"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    
    decisions = []
    
    for rule in rules:
        # Simple heuristic for ground truth
        confidence = rule.get("confidence", 0.5)
        rule_type = rule.get("action", {}).get("type", "")
        
        # Store high-confidence rules and important types
        should_store = (
            confidence >= 0.85 or
            rule_type in ["naming", "behavior"] or
            "always" in rule.get("action", {}).get("description", "").lower() or
            "never" in rule.get("action", {}).get("description", "").lower()
        )
        
        decision = {
            "rule_id": rule["id"],
            "decision": "store" if should_store else "ignore"
        }
        decisions.append(decision)
    
    # Save decisions
    FileIO.write_json(
        decisions,
        ground_truth_dir / "storage_decisions_ground_truth.json"
    )
    
    print(f"  Generated {len(decisions)} storage decision labels")
    
    return decisions


def generate_complete_dataset(output_dir: str, seed: int = 42) -> Dict[str, Any]:
    """Generate a complete dataset for pipeline testing.
    
    Args:
        output_dir: Output directory
        seed: Random seed
        
    Returns:
        Summary of generated data
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    generator = SyntheticDataGenerator(seed=seed)
    
    print(f"Generating complete dataset in {output_dir}")
    print("=" * 50)
    
    # Generate transcripts
    transcripts = generate_transcripts(generator, output_path, num_transcripts=15)
    
    # Generate test tasks
    tasks = generate_test_tasks(generator, output_path, num_tasks=20)
    
    # Generate example rules
    example_rules = generate_example_rules(output_path)
    
    # Generate storage decisions ground truth
    all_rules = []
    for t in transcripts:
        all_rules.extend(t["ground_truth"])
    storage_decisions = generate_storage_decisions_ground_truth(all_rules, output_path)
    
    # Create dataset summary
    summary = {
        "dataset_info": {
            "seed": seed,
            "generation_timestamp": FileIO.create_timestamped_filename("", "").split("_")[1].split(".")[0],
            "num_transcripts": len(transcripts),
            "num_tasks": len(tasks),
            "num_example_rules": len(example_rules),
            "total_ground_truth_rules": len(all_rules)
        },
        "file_structure": {
            "transcripts": "transcripts/*.json",
            "ground_truth_rules": "ground_truth/*_rules.json",
            "test_tasks": "test_tasks/tasks.json",
            "drift_tasks": "test_tasks/drift_tasks.json",
            "example_rules": "example_rules/example_rules.json",
            "storage_decisions_gt": "ground_truth/storage_decisions_ground_truth.json"
        },
        "statistics": {
            "avg_transcript_length": sum(len(t["transcript"]["segments"]) for t in transcripts) / len(transcripts),
            "total_rule_segments": sum(
                1 for t in transcripts 
                for seg in t["transcript"]["segments"] 
                if seg["type"] != "irrelevant"
            ),
            "rule_type_distribution": {}
        }
    }
    
    # Calculate rule type distribution
    rule_types = {}
    for t in transcripts:
        for rule in t["ground_truth"]:
            rule_type = rule["action"]["type"]
            rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
    summary["statistics"]["rule_type_distribution"] = rule_types
    
    # Save summary
    FileIO.write_json(summary, output_path / "dataset_summary.json")
    
    print("\n" + "=" * 50)
    print("Dataset generation complete!")
    print(f"Summary saved to: {output_path / 'dataset_summary.json'}")
    
    return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for LTM pipeline testing"
    )
    
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for generated data"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--type",
        choices=["all", "transcripts", "tasks", "rules"],
        default="all",
        help="Type of data to generate"
    )
    
    parser.add_argument(
        "--num-transcripts",
        type=int,
        default=15,
        help="Number of transcripts to generate"
    )
    
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=20,
        help="Number of tasks to generate"
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    generator = SyntheticDataGenerator(seed=args.seed)
    
    if args.type == "all":
        summary = generate_complete_dataset(args.output, args.seed)
        print(f"\nGenerated {summary['dataset_info']['num_transcripts']} transcripts")
        print(f"Generated {summary['dataset_info']['num_tasks']} tasks")
        print(f"Generated {summary['dataset_info']['total_ground_truth_rules']} ground truth rules")
    
    elif args.type == "transcripts":
        transcripts = generate_transcripts(generator, output_path, args.num_transcripts)
        print(f"\nGenerated {len(transcripts)} transcripts")
    
    elif args.type == "tasks":
        tasks = generate_test_tasks(generator, output_path, args.num_tasks)
        print(f"\nGenerated {len(tasks)} tasks")
    
    elif args.type == "rules":
        rules = generate_example_rules(output_path)
        print(f"\nGenerated {len(rules)} example rules")


if __name__ == "__main__":
    main()