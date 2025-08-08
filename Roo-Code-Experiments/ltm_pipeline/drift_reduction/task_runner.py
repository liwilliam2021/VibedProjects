"""Task runner for executing tasks with and without rules to measure drift."""

from typing import List, Dict, Any, Optional, Callable
import time
from datetime import datetime
import random
import copy

from ..common.models import Task, Rule, ApplicationResult
from ..common.logger import get_logger
from ..common.metrics import MetricsCollector
from ..retrieval_application.ltm_storage import SimulatedLTMStorage
from ..retrieval_application.retriever import RuleRetriever
from ..retrieval_application.applicator import RuleApplicator


class TaskRunner:
    """Run tasks with and without rules to measure consistency."""
    
    def __init__(self, ltm_storage: Optional[SimulatedLTMStorage] = None,
                 task_executor: Optional[Callable] = None):
        """Initialize the task runner.
        
        Args:
            ltm_storage: LTM storage instance (will create if not provided)
            task_executor: Optional custom task executor function
        """
        self.logger = get_logger("TaskRunner")
        self.metrics = MetricsCollector("task_running")
        
        # Initialize components
        self.storage = ltm_storage or SimulatedLTMStorage()
        self.retriever = RuleRetriever(self.storage)
        self.applicator = RuleApplicator(self.storage, self.retriever)
        
        # Task executor - can be customized
        self.task_executor = task_executor or self._default_task_executor
    
    def run_task_without_rules(self, task: Task, num_runs: int = 5) -> List[Dict[str, Any]]:
        """Run a task multiple times without applying rules.
        
        Args:
            task: Task to run
            num_runs: Number of times to run the task
            
        Returns:
            List of outputs from each run
        """
        self.logger.info(f"Running task {task.id} without rules ({num_runs} times)")
        
        outputs = []
        for i in range(num_runs):
            start_time = time.time()
            
            # Execute task without rules
            output = self.task_executor(task, rules=[])
            
            # Add metadata
            output["_metadata"] = {
                "run_number": i + 1,
                "with_rules": False,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            outputs.append(output)
            
            # Record metrics
            self.metrics.record("task_execution_time", output["_metadata"]["execution_time"],
                              task_id=task.id, with_rules=False)
        
        return outputs
    
    def run_task_with_rules(self, task: Task, num_runs: int = 5,
                           rules: Optional[List[Rule]] = None) -> List[Dict[str, Any]]:
        """Run a task multiple times with rules applied.
        
        Args:
            task: Task to run
            num_runs: Number of times to run the task
            rules: Optional list of rules (will retrieve if not provided)
            
        Returns:
            List of outputs from each run
        """
        self.logger.info(f"Running task {task.id} with rules ({num_runs} times)")
        
        # Retrieve rules if not provided
        if rules is None:
            rules = self.retriever.retrieve_for_task(task)
            self.logger.info(f"Retrieved {len(rules)} rules for task {task.id}")
        
        outputs = []
        for i in range(num_runs):
            start_time = time.time()
            
            # Apply rules to task
            application_result = self.applicator.apply_rules_to_task(task, rules)
            
            # Execute task with applied rules
            output = self.task_executor(task, rules, application_result)
            
            # Add metadata
            output["_metadata"] = {
                "run_number": i + 1,
                "with_rules": True,
                "rules_applied": len(application_result.applied_rules),
                "rules_skipped": len(application_result.skipped_rules),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "application_result": application_result.to_dict()
            }
            
            outputs.append(output)
            
            # Record metrics
            self.metrics.record("task_execution_time", output["_metadata"]["execution_time"],
                              task_id=task.id, with_rules=True)
            self.metrics.record("rules_applied_count", len(application_result.applied_rules),
                              task_id=task.id)
        
        return outputs
    
    def run_comparison(self, task: Task, num_runs: int = 5,
                      rules: Optional[List[Rule]] = None) -> Dict[str, Any]:
        """Run task comparison with and without rules.
        
        Args:
            task: Task to run
            num_runs: Number of runs for each condition
            rules: Optional list of rules
            
        Returns:
            Dictionary containing both sets of outputs
        """
        self.logger.info(f"Running comparison for task {task.id}")
        
        # Run without rules
        outputs_without = self.run_task_without_rules(task, num_runs)
        
        # Run with rules
        outputs_with = self.run_task_with_rules(task, num_runs, rules)
        
        return {
            "task_id": task.id,
            "outputs_without_rules": outputs_without,
            "outputs_with_rules": outputs_with,
            "summary": self._generate_comparison_summary(outputs_without, outputs_with)
        }
    
    def run_batch_comparison(self, tasks: List[Task], num_runs_per_task: int = 5,
                           store_rules: bool = True) -> List[Dict[str, Any]]:
        """Run comparison for multiple tasks.
        
        Args:
            tasks: List of tasks to run
            num_runs_per_task: Number of runs per task
            store_rules: Whether to store extracted rules in LTM
            
        Returns:
            List of comparison results
        """
        self.logger.info(f"Running batch comparison for {len(tasks)} tasks")
        
        results = []
        
        for i, task in enumerate(tasks):
            self.logger.info(f"Processing task {i+1}/{len(tasks)}: {task.id}")
            
            # Run comparison
            comparison = self.run_comparison(task, num_runs_per_task)
            results.append(comparison)
            
            # Optional: Store rules if they were retrieved
            if store_rules and "_metadata" in comparison["outputs_with_rules"][0]:
                app_result = comparison["outputs_with_rules"][0]["_metadata"].get("application_result")
                if app_result and app_result.get("applied_rules"):
                    self.logger.info(f"Storing {len(app_result['applied_rules'])} rules from task {task.id}")
        
        return results
    
    def _default_task_executor(self, task: Task, rules: List[Rule],
                             application_result: Optional[ApplicationResult] = None) -> Dict[str, Any]:
        """Default task executor that simulates code generation.
        
        Args:
            task: Task to execute
            rules: Rules to consider
            application_result: Optional application result
            
        Returns:
            Simulated output
        """
        output = {
            "task_id": task.id,
            "type": task.type,
            "language": task.language
        }
        
        # Simulate different types of outputs based on task type
        if task.type == "code_generation":
            output.update(self._generate_code_output(task, rules, application_result))
        elif task.type == "refactoring":
            output.update(self._generate_refactoring_output(task, rules, application_result))
        elif task.type == "debugging":
            output.update(self._generate_debugging_output(task, rules, application_result))
        else:
            output.update(self._generate_generic_output(task, rules, application_result))
        
        return output
    
    def _generate_code_output(self, task: Task, rules: List[Rule],
                            application_result: Optional[ApplicationResult] = None) -> Dict[str, Any]:
        """Generate simulated code output.
        
        Args:
            task: Task to execute
            rules: Rules to apply
            application_result: Application result
            
        Returns:
            Code generation output
        """
        # Base code structure
        output = {
            "code": "",
            "files": [],
            "identifiers": {},
            "style": {},
            "components": []
        }
        
        # Determine naming convention based on rules
        naming_convention = "camelCase"  # default
        if application_result:
            for mod in application_result.modifications:
                if mod.get("action_type") == "naming":
                    for change in mod.get("changes", []):
                        if "convention" in change:
                            naming_convention = change["convention"]
                            break
        
        # Determine style based on rules
        indentation = "4 spaces"  # default
        if application_result:
            for mod in application_result.modifications:
                if mod.get("action_type") == "style":
                    for change in mod.get("changes", []):
                        for rule in change.get("style_rules", []):
                            if rule["rule"] == "indentation":
                                indentation = rule["value"]
        
        # Generate code based on task
        if task.language == "JavaScript":
            output["code"] = self._generate_javascript_code(task, naming_convention, indentation)
            output["files"] = ["index.js", "utils.js"]
        elif task.language == "Python":
            output["code"] = self._generate_python_code(task, naming_convention, indentation)
            output["files"] = ["main.py", "helpers.py"]
        else:
            output["code"] = f"// Generated code for {task.description}"
            output["files"] = ["main.ext"]
        
        # Extract identifiers and components
        output["identifiers"] = self._extract_identifiers_from_code(output["code"])
        output["components"] = self._extract_components_from_code(output["code"])
        output["style"]["indentation"] = indentation
        output["style"]["naming_convention"] = naming_convention
        
        return output
    
    def _generate_javascript_code(self, task: Task, naming_convention: str, indentation: str) -> str:
        """Generate JavaScript code with specified conventions."""
        indent = "    " if "4" in indentation else "  " if "2" in indentation else "\t"
        
        # Convert function names based on convention
        func_name = self._convert_name("calculate_total", naming_convention)
        var_name = self._convert_name("user_data", naming_convention)
        
        code = f"""// {task.description}

function {func_name}(items) {{
{indent}let {var_name} = {{}};
{indent}let total = 0;
{indent}
{indent}for (const item of items) {{
{indent}{indent}total += item.value;
{indent}}}
{indent}
{indent}return total;
}}

module.exports = {{ {func_name} }};
"""
        return code
    
    def _generate_python_code(self, task: Task, naming_convention: str, indentation: str) -> str:
        """Generate Python code with specified conventions."""
        indent = "    " if "4" in indentation else "  " if "2" in indentation else "\t"
        
        # Python typically uses snake_case, but respect the rule
        func_name = self._convert_name("calculate_total", naming_convention)
        var_name = self._convert_name("user_data", naming_convention)
        
        code = f"""# {task.description}

def {func_name}(items):
{indent}\"\"\"{task.description}\"\"\"
{indent}{var_name} = {{}}
{indent}total = 0
{indent}
{indent}for item in items:
{indent}{indent}total += item.get('value', 0)
{indent}
{indent}return total


if __name__ == "__main__":
{indent}test_items = [{{'value': 10}}, {{'value': 20}}]
{indent}result = {func_name}(test_items)
{indent}print(f"Total: {{result}}")
"""
        return code
    
    def _convert_name(self, name: str, convention: str) -> str:
        """Convert a name to the specified convention."""
        # Simple conversion logic
        parts = name.split('_')
        
        if convention == "camelCase":
            return parts[0] + ''.join(p.capitalize() for p in parts[1:])
        elif convention == "PascalCase":
            return ''.join(p.capitalize() for p in parts)
        elif convention == "kebab-case":
            return '-'.join(parts)
        else:  # snake_case
            return name
    
    def _generate_refactoring_output(self, task: Task, rules: List[Rule],
                                   application_result: Optional[ApplicationResult] = None) -> Dict[str, Any]:
        """Generate simulated refactoring output."""
        return {
            "refactored_code": f"// Refactored: {task.description}",
            "changes_made": ["Improved naming", "Extracted methods", "Removed duplication"],
            "files": ["refactored.js"],
            "components": ["improvedFunction", "helperMethod"]
        }
    
    def _generate_debugging_output(self, task: Task, rules: List[Rule],
                                 application_result: Optional[ApplicationResult] = None) -> Dict[str, Any]:
        """Generate simulated debugging output."""
        return {
            "fixed_code": f"// Fixed: {task.description}",
            "bugs_found": ["Null pointer", "Off-by-one error"],
            "fixes_applied": ["Added null check", "Fixed loop condition"],
            "files": ["fixed.js"]
        }
    
    def _generate_generic_output(self, task: Task, rules: List[Rule],
                               application_result: Optional[ApplicationResult] = None) -> Dict[str, Any]:
        """Generate generic output for unknown task types."""
        return {
            "output": f"Completed: {task.description}",
            "files": ["output.txt"]
        }
    
    def _extract_identifiers_from_code(self, code: str) -> Dict[str, str]:
        """Extract identifiers from code."""
        identifiers = {}
        
        # Simple extraction
        import re
        
        # Functions
        func_pattern = r'(?:function|def)\s+(\w+)'
        for match in re.finditer(func_pattern, code):
            identifiers[match.group(1)] = "function"
        
        # Variables
        var_pattern = r'(?:let|const|var)\s+(\w+)'
        for match in re.finditer(var_pattern, code):
            identifiers[match.group(1)] = "variable"
        
        return identifiers
    
    def _extract_components_from_code(self, code: str) -> List[str]:
        """Extract component names from code."""
        components = []
        
        import re
        
        # Functions
        func_pattern = r'(?:function|def)\s+(\w+)'
        components.extend(re.findall(func_pattern, code))
        
        # Classes
        class_pattern = r'class\s+(\w+)'
        components.extend(re.findall(class_pattern, code))
        
        return components
    
    def _generate_comparison_summary(self, outputs_without: List[Dict[str, Any]],
                                   outputs_with: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of comparison results.
        
        Args:
            outputs_without: Outputs without rules
            outputs_with: Outputs with rules
            
        Returns:
            Summary dictionary
        """
        # Calculate average execution times
        avg_time_without = sum(o["_metadata"]["execution_time"] for o in outputs_without) / len(outputs_without)
        avg_time_with = sum(o["_metadata"]["execution_time"] for o in outputs_with) / len(outputs_with)
        
        # Count rules applied
        total_rules_applied = sum(o["_metadata"].get("rules_applied", 0) for o in outputs_with)
        
        return {
            "num_runs": len(outputs_without),
            "avg_execution_time_without_rules": avg_time_without,
            "avg_execution_time_with_rules": avg_time_with,
            "total_rules_applied": total_rules_applied,
            "avg_rules_per_run": total_rules_applied / len(outputs_with) if outputs_with else 0
        }
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics.
        
        Returns:
            Dictionary of statistics
        """
        summary = self.metrics.get_summary()
        
        return {
            "total_executions": summary["total_metrics"],
            "execution_times": {
                "without_rules": {
                    "mean": summary["metrics_by_name"].get("task_execution_time", {}).get("mean", 0),
                    "min": summary["metrics_by_name"].get("task_execution_time", {}).get("min", 0),
                    "max": summary["metrics_by_name"].get("task_execution_time", {}).get("max", 0)
                }
            },
            "rules_applied": summary["metrics_by_name"].get("rules_applied_count", {})
        }