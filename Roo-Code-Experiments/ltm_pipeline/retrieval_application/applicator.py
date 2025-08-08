"""Rule application module for applying retrieved rules to tasks."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from ..common.models import Rule, Task, ApplicationResult
from ..common.logger import get_logger
from ..common.metrics import MetricsCollector
from .ltm_storage import SimulatedLTMStorage
from .retriever import RuleRetriever


class RuleApplicator:
    """Apply retrieved rules to tasks."""
    
    def __init__(self, ltm_storage: SimulatedLTMStorage, retriever: Optional[RuleRetriever] = None):
        """Initialize the rule applicator.
        
        Args:
            ltm_storage: LTM storage instance
            retriever: Optional retriever instance (will create if not provided)
        """
        self.logger = get_logger("RuleApplicator")
        self.metrics = MetricsCollector("rule_application")
        self.storage = ltm_storage
        self.retriever = retriever or RuleRetriever(ltm_storage)
    
    def apply_rules_to_task(self, task: Task, rules: Optional[List[Rule]] = None) -> ApplicationResult:
        """Apply relevant rules to a task.
        
        Args:
            task: Task to apply rules to
            rules: Optional list of rules (will retrieve if not provided)
            
        Returns:
            ApplicationResult with details of applied rules
        """
        start_time = datetime.utcnow()
        
        # Retrieve rules if not provided
        if rules is None:
            rules = self.retriever.retrieve_for_task(task)
        
        self.logger.info(f"Applying {len(rules)} rules to task {task.id}")
        
        # Initialize result
        result = ApplicationResult(task_id=task.id)
        
        # Apply each rule
        for rule in rules:
            try:
                should_apply, reason = self._should_apply_rule(rule, task)
                
                if should_apply:
                    modification = self._apply_rule(rule, task)
                    if modification:
                        result.applied_rules.append(rule.id)
                        result.modifications.append(modification)
                        
                        self.logger.log_rule_application(
                            task_id=task.id,
                            rule_id=rule.id,
                            applied=True,
                            reason="Successfully applied"
                        )
                else:
                    result.skipped_rules.append(rule.id)
                    self.logger.log_rule_application(
                        task_id=task.id,
                        rule_id=rule.id,
                        applied=False,
                        reason=reason
                    )
                    
            except Exception as e:
                error_msg = f"Failed to apply rule {rule.id}: {str(e)}"
                result.errors.append(error_msg)
                self.logger.error(error_msg)
        
        # Record metrics
        application_time = (datetime.utcnow() - start_time).total_seconds()
        self.metrics.record("application_time", application_time, task_id=task.id)
        self.metrics.record("rules_applied", len(result.applied_rules), task_id=task.id)
        self.metrics.record("rules_skipped", len(result.skipped_rules), task_id=task.id)
        self.metrics.record("application_errors", len(result.errors), task_id=task.id)
        
        # Calculate application rate
        if rules:
            application_rate = len(result.applied_rules) / len(rules)
            self.metrics.record("application_rate", application_rate, task_id=task.id)
        
        self.logger.info(f"Applied {len(result.applied_rules)} rules to task {task.id}, "
                        f"skipped {len(result.skipped_rules)}, errors: {len(result.errors)}")
        
        return result
    
    def _should_apply_rule(self, rule: Rule, task: Task) -> Tuple[bool, str]:
        """Determine if a rule should be applied to a task.
        
        Args:
            rule: Rule to check
            task: Task to check against
            
        Returns:
            Tuple of (should_apply, reason)
        """
        # Check language compatibility
        if rule.match_criteria.context and "language" in rule.match_criteria.context:
            rule_lang = rule.match_criteria.context["language"].lower()
            if task.language and rule_lang != "general" and rule_lang != task.language.lower():
                return False, f"Language mismatch: rule is for {rule_lang}, task is {task.language}"
        
        # Check match criteria
        if rule.match_criteria.type.value == "pattern":
            # Check if pattern matches task context
            pattern = rule.match_criteria.value
            if not self._pattern_matches_task(pattern, task):
                return False, f"Pattern '{pattern}' does not match task context"
        
        elif rule.match_criteria.type.value == "keyword":
            # Check if keyword is relevant to task
            keyword = rule.match_criteria.value.lower()
            task_text = f"{task.description} {str(task.context)}".lower()
            if keyword not in task_text:
                return False, f"Keyword '{keyword}' not found in task"
        
        elif rule.match_criteria.type.value == "context":
            # Check context match
            if not self._context_matches_task(rule.match_criteria.context, task):
                return False, "Context criteria do not match task"
        
        # Check if rule action is applicable
        if not self._is_action_applicable(rule.action, task):
            return False, f"Action type {rule.action.type.value} not applicable to task type {task.type}"
        
        return True, "All criteria met"
    
    def _pattern_matches_task(self, pattern: str, task: Task) -> bool:
        """Check if a pattern matches the task.
        
        Args:
            pattern: Pattern to match
            task: Task to check
            
        Returns:
            True if pattern matches
        """
        # Simple pattern matching - could be enhanced with regex
        pattern_lower = pattern.lower()
        
        # Check in description
        if pattern_lower in task.description.lower():
            return True
        
        # Check in context
        if task.context:
            context_str = str(task.context).lower()
            if pattern_lower in context_str:
                return True
        
        return False
    
    def _context_matches_task(self, rule_context: Optional[Dict[str, Any]], task: Task) -> bool:
        """Check if rule context matches task.
        
        Args:
            rule_context: Rule context requirements
            task: Task to check
            
        Returns:
            True if contexts match
        """
        if not rule_context:
            return True
        
        if not task.context:
            return False
        
        # Check each context requirement
        for key, value in rule_context.items():
            if key not in task.context:
                return False
            
            # Simple equality check - could be enhanced
            if task.context[key] != value:
                return False
        
        return True
    
    def _is_action_applicable(self, action: Any, task: Task) -> bool:
        """Check if an action is applicable to a task.
        
        Args:
            action: Rule action
            task: Task to check
            
        Returns:
            True if action is applicable
        """
        action_type = action.type.value
        task_type = task.type
        
        # Define applicability matrix
        applicability = {
            "naming": ["code_generation", "refactoring"],
            "style": ["code_generation", "refactoring", "formatting"],
            "structure": ["code_generation", "refactoring", "organization"],
            "behavior": ["code_generation", "debugging", "optimization"]
        }
        
        # Check if action type is applicable to task type
        if action_type in applicability:
            return task_type in applicability[action_type]
        
        # Default to applicable if not specified
        return True
    
    def _apply_rule(self, rule: Rule, task: Task) -> Dict[str, Any]:
        """Apply a rule to a task and return the modification.
        
        Args:
            rule: Rule to apply
            task: Task to apply to
            
        Returns:
            Dictionary describing the modification
        """
        modification = {
            "rule_id": rule.id,
            "action_type": rule.action.type.value,
            "description": rule.action.description,
            "timestamp": datetime.utcnow().isoformat(),
            "changes": []
        }
        
        # Simulate different types of rule applications
        action_type = rule.action.type.value
        
        if action_type == "naming":
            # Simulate naming convention application
            change = self._apply_naming_rule(rule, task)
            if change:
                modification["changes"].append(change)
        
        elif action_type == "style":
            # Simulate style rule application
            change = self._apply_style_rule(rule, task)
            if change:
                modification["changes"].append(change)
        
        elif action_type == "structure":
            # Simulate structure rule application
            change = self._apply_structure_rule(rule, task)
            if change:
                modification["changes"].append(change)
        
        elif action_type == "behavior":
            # Simulate behavior rule application
            change = self._apply_behavior_rule(rule, task)
            if change:
                modification["changes"].append(change)
        
        return modification
    
    def _apply_naming_rule(self, rule: Rule, task: Task) -> Optional[Dict[str, Any]]:
        """Apply a naming convention rule.
        
        Args:
            rule: Naming rule
            task: Task to apply to
            
        Returns:
            Change description or None
        """
        # Extract naming convention from rule
        conventions = ["camelCase", "snake_case", "PascalCase", "kebab-case"]
        convention = None
        
        for conv in conventions:
            if conv in rule.action.description:
                convention = conv
                break
        
        if not convention:
            return None
        
        # Simulate applying the convention
        change = {
            "type": "naming_convention",
            "convention": convention,
            "affected_items": []
        }
        
        # Check task context for variables that need naming
        if task.context and "variables_needed" in task.context:
            for var in task.context["variables_needed"]:
                if isinstance(var, str):
                    converted = self._convert_to_convention(var, convention)
                    if converted != var:
                        change["affected_items"].append({
                            "original": var,
                            "converted": converted
                        })
        
        return change if change["affected_items"] else None
    
    def _apply_style_rule(self, rule: Rule, task: Task) -> Optional[Dict[str, Any]]:
        """Apply a style rule.
        
        Args:
            rule: Style rule
            task: Task to apply to
            
        Returns:
            Change description or None
        """
        # Extract style parameters
        change = {
            "type": "style",
            "style_rules": []
        }
        
        # Check for indentation rules
        indent_match = re.search(r'(\d+)\s*(spaces?|tabs?)', rule.action.description.lower())
        if indent_match:
            amount = indent_match.group(1)
            unit = indent_match.group(2)
            change["style_rules"].append({
                "rule": "indentation",
                "value": f"{amount} {unit}"
            })
        
        # Check for line length rules
        length_match = re.search(r'(\d+)\s*characters?', rule.action.description.lower())
        if length_match:
            length = length_match.group(1)
            change["style_rules"].append({
                "rule": "line_length",
                "value": f"{length} characters"
            })
        
        return change if change["style_rules"] else None
    
    def _apply_structure_rule(self, rule: Rule, task: Task) -> Optional[Dict[str, Any]]:
        """Apply a structure rule.
        
        Args:
            rule: Structure rule
            task: Task to apply to
            
        Returns:
            Change description or None
        """
        change = {
            "type": "structure",
            "organization": []
        }
        
        # Extract organization patterns
        if "separate" in rule.action.description.lower():
            change["organization"].append({
                "pattern": "separation",
                "description": "Separate components into individual files"
            })
        
        if "group" in rule.action.description.lower():
            change["organization"].append({
                "pattern": "grouping",
                "description": "Group related items together"
            })
        
        if "organize" in rule.action.description.lower():
            change["organization"].append({
                "pattern": "organization",
                "description": rule.action.description
            })
        
        return change if change["organization"] else None
    
    def _apply_behavior_rule(self, rule: Rule, task: Task) -> Optional[Dict[str, Any]]:
        """Apply a behavior rule.
        
        Args:
            rule: Behavior rule
            task: Task to apply to
            
        Returns:
            Change description or None
        """
        change = {
            "type": "behavior",
            "behaviors": []
        }
        
        # Extract behavioral patterns
        description_lower = rule.action.description.lower()
        
        if "validate" in description_lower:
            change["behaviors"].append({
                "action": "validation",
                "description": "Add input validation"
            })
        
        if "log" in description_lower:
            change["behaviors"].append({
                "action": "logging",
                "description": "Add logging statements"
            })
        
        if "error" in description_lower:
            change["behaviors"].append({
                "action": "error_handling",
                "description": "Add error handling"
            })
        
        if "test" in description_lower:
            change["behaviors"].append({
                "action": "testing",
                "description": "Add test cases"
            })
        
        return change if change["behaviors"] else None
    
    def _convert_to_convention(self, name: str, convention: str) -> str:
        """Convert a name to a specific naming convention.
        
        Args:
            name: Name to convert
            convention: Target convention
            
        Returns:
            Converted name
        """
        # Split name into words
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', name)
        if not words:
            words = name.split('_')
        
        # Convert based on convention
        if convention == "camelCase":
            return words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        elif convention == "snake_case":
            return '_'.join(w.lower() for w in words)
        elif convention == "PascalCase":
            return ''.join(w.capitalize() for w in words)
        elif convention == "kebab-case":
            return '-'.join(w.lower() for w in words)
        
        return name
    
    def batch_apply(self, task_rules_map: Dict[str, List[Rule]]) -> Dict[str, ApplicationResult]:
        """Apply rules to multiple tasks.
        
        Args:
            task_rules_map: Dictionary mapping task IDs to rules
            
        Returns:
            Dictionary mapping task IDs to application results
        """
        results = {}
        
        for task_id, rules in task_rules_map.items():
            # Create a minimal task object for application
            task = Task(id=task_id)
            result = self.apply_rules_to_task(task, rules)
            results[task_id] = result
        
        # Calculate batch statistics
        total_applied = sum(len(r.applied_rules) for r in results.values())
        total_skipped = sum(len(r.skipped_rules) for r in results.values())
        total_errors = sum(len(r.errors) for r in results.values())
        
        self.metrics.record("batch_total_applied", total_applied)
        self.metrics.record("batch_total_skipped", total_skipped)
        self.metrics.record("batch_total_errors", total_errors)
        
        return results
    
    def get_application_statistics(self) -> Dict[str, Any]:
        """Get application statistics.
        
        Returns:
            Dictionary of statistics
        """
        summary = self.metrics.get_summary()
        
        return {
            "total_applications": summary["metrics_by_name"].get("rules_applied", {}).get("count", 0),
            "avg_rules_per_task": summary["metrics_by_name"].get("rules_applied", {}).get("mean", 0),
            "avg_application_rate": summary["metrics_by_name"].get("application_rate", {}).get("mean", 0),
            "total_errors": summary["metrics_by_name"].get("application_errors", {}).get("count", 0),
            "avg_application_time": summary["metrics_by_name"].get("application_time", {}).get("mean", 0)
        }