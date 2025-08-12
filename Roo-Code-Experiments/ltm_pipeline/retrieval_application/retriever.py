"""Rule retrieval module for finding relevant rules from LTM storage."""

from typing import List, Dict, Any, Optional, Set
import re
from datetime import datetime

from ..common.models import Rule, Task
from ..common.logger import get_logger
from ..common.metrics import MetricsCollector
from .ltm_storage import SimulatedLTMStorage


class RuleRetriever:
    """Retrieve relevant rules from LTM storage based on context."""
    
    def __init__(self, ltm_storage: SimulatedLTMStorage, 
                 similarity_threshold: float = 0.8):
        """Initialize the rule retriever.
        
        Args:
            ltm_storage: LTM storage instance
            similarity_threshold: Minimum similarity for retrieval
        """
        self.logger = get_logger("RuleRetriever")
        self.metrics = MetricsCollector("rule_retrieval")
        self.storage = ltm_storage
        self.similarity_threshold = similarity_threshold
    
    def retrieve_for_task(self, task: Task, max_rules: int = 10) -> List[Rule]:
        """Retrieve relevant rules for a specific task.
        
        Args:
            task: Task to retrieve rules for
            max_rules: Maximum number of rules to retrieve
            
        Returns:
            List of relevant rules
        """
        start_time = datetime.utcnow()
        
        # Build retrieval context from task
        context = self._build_context_from_task(task)
        context["max_rules"] = max_rules
        
        self.logger.info(f"Retrieving rules for task {task.id} with context: {list(context.keys())}")
        
        # Retrieve from storage
        relevant_rules = self.storage.retrieve_relevant_rules(context)
        
        # Filter by similarity threshold
        filtered_rules = []
        for rule in relevant_rules:
            similarity = self._calculate_task_rule_similarity(task, rule)
            if similarity >= self.similarity_threshold:
                filtered_rules.append(rule)
                self.logger.debug(f"Rule {rule.id} passed threshold with similarity {similarity:.2f}")
        
        # Record metrics
        retrieval_time = (datetime.utcnow() - start_time).total_seconds()
        self.metrics.record("retrieval_time", retrieval_time, task_id=task.id)
        self.metrics.record("rules_retrieved", len(filtered_rules), task_id=task.id)
        self.metrics.record("rules_filtered", len(relevant_rules) - len(filtered_rules))
        
        self.logger.info(f"Retrieved {len(filtered_rules)} rules for task {task.id} "
                        f"(filtered from {len(relevant_rules)} candidates)")
        
        return filtered_rules
    
    def _build_context_from_task(self, task: Task) -> Dict[str, Any]:
        """Build retrieval context from a task.
        
        Args:
            task: Task to build context from
            
        Returns:
            Context dictionary
        """
        context = {
            "task_type": task.type,
            "language": task.language,
            "description": task.description
        }
        
        # Extract keywords from description
        keywords = self._extract_keywords(task.description)
        if keywords:
            context["keywords"] = keywords
        
        # Add task-specific context
        if task.context:
            # Extract relevant fields
            if "variables_needed" in task.context:
                context["keywords"] = context.get("keywords", []) + \
                                    [var for var in task.context["variables_needed"] if isinstance(var, str)]
            
            if "operation" in task.context:
                context["operation"] = task.context["operation"]
            
            if "requirements" in task.context:
                requirements = task.context["requirements"]
                if isinstance(requirements, list):
                    context["keywords"] = context.get("keywords", []) + requirements
        
        return context
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction
        # Remove common words and extract significant terms
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "about", "as", "and", "or", "but",
            "if", "then", "else", "when", "where", "how", "why", "what", "which",
            "who", "whom", "this", "that", "these", "those", "it", "its"
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = []
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]  # Limit to top 10 keywords
    
    def _calculate_task_rule_similarity(self, task: Task, rule: Rule) -> float:
        """Calculate similarity between a task and a rule.
        
        Args:
            task: Task to compare
            rule: Rule to compare
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0
        
        # Language match
        if task.language and rule.match_criteria.context:
            rule_lang = rule.match_criteria.context.get("language", "").lower()
            if rule_lang == task.language.lower():
                score += 0.3
            elif rule_lang == "general" or not rule_lang:
                score += 0.1
        
        # Task type relevance
        task_type_keywords = {
            "code_generation": ["create", "implement", "write", "generate"],
            "refactoring": ["refactor", "improve", "optimize", "clean"],
            "debugging": ["fix", "debug", "error", "issue"],
            "testing": ["test", "verify", "validate", "check"]
        }
        
        if task.type in task_type_keywords:
            relevant_keywords = task_type_keywords[task.type]
            rule_text = rule.action.description.lower()
            if any(kw in rule_text for kw in relevant_keywords):
                score += 0.2
        
        # Description keyword match
        task_keywords = set(self._extract_keywords(task.description))
        rule_keywords = set(self._extract_keywords(rule.action.description))
        
        if task_keywords and rule_keywords:
            overlap = len(task_keywords & rule_keywords)
            if overlap > 0:
                score += min(0.3 * overlap / min(len(task_keywords), len(rule_keywords)), 0.3)
        
        # Context match
        if task.context and rule.match_criteria.value:
            # Check if rule match criteria applies to task context
            match_value = rule.match_criteria.value.lower()
            context_str = str(task.context).lower()
            
            if match_value in context_str:
                score += 0.2
        
        return min(score, 1.0)
    
    def batch_retrieve(self, tasks: List[Task], max_rules_per_task: int = 10) -> Dict[str, List[Rule]]:
        """Retrieve rules for multiple tasks.
        
        Args:
            tasks: List of tasks
            max_rules_per_task: Maximum rules per task
            
        Returns:
            Dictionary mapping task IDs to retrieved rules
        """
        results = {}
        
        for task in tasks:
            rules = self.retrieve_for_task(task, max_rules_per_task)
            results[task.id] = rules
        
        # Calculate batch statistics
        total_rules = sum(len(rules) for rules in results.values())
        avg_rules = total_rules / len(tasks) if tasks else 0
        
        self.metrics.record("batch_size", len(tasks))
        self.metrics.record("avg_rules_per_task", avg_rules)
        
        return results
    
    def explain_retrieval(self, task: Task, rule: Rule) -> Dict[str, Any]:
        """Explain why a rule was retrieved for a task.
        
        Args:
            task: Task that triggered retrieval
            rule: Rule that was retrieved
            
        Returns:
            Explanation dictionary
        """
        explanation = {
            "task_id": task.id,
            "rule_id": rule.id,
            "rule_description": rule.action.description,
            "similarity_score": self._calculate_task_rule_similarity(task, rule),
            "factors": []
        }
        
        # Check language match
        if task.language and rule.match_criteria.context:
            rule_lang = rule.match_criteria.context.get("language", "")
            if rule_lang.lower() == task.language.lower():
                explanation["factors"].append({
                    "factor": "language_match",
                    "description": f"Rule language '{rule_lang}' matches task language '{task.language}'"
                })
        
        # Check keyword overlap
        task_keywords = set(self._extract_keywords(task.description))
        rule_keywords = set(self._extract_keywords(rule.action.description))
        overlap = task_keywords & rule_keywords
        
        if overlap:
            explanation["factors"].append({
                "factor": "keyword_overlap",
                "description": f"Common keywords: {', '.join(overlap)}"
            })
        
        # Check task type relevance
        if task.type == "code_generation" and "create" in rule.action.description.lower():
            explanation["factors"].append({
                "factor": "task_type_match",
                "description": "Rule is relevant for code generation tasks"
            })
        
        # Check match criteria
        if rule.match_criteria.value:
            if rule.match_criteria.value.lower() in str(task.context).lower():
                explanation["factors"].append({
                    "factor": "context_match",
                    "description": f"Rule match criteria '{rule.match_criteria.value}' found in task context"
                })
        
        return explanation
    
    def get_retrieval_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics.
        
        Returns:
            Dictionary of statistics
        """
        summary = self.metrics.get_summary()
        
        # Add storage statistics
        storage_stats = self.storage.get_statistics()
        
        return {
            "retrieval_metrics": summary,
            "storage_stats": storage_stats,
            "performance": {
                "avg_retrieval_time": summary["metrics_by_name"].get("retrieval_time", {}).get("mean", 0),
                "avg_rules_retrieved": summary["metrics_by_name"].get("rules_retrieved", {}).get("mean", 0),
                "total_retrievals": summary["metrics_by_name"].get("retrieval_time", {}).get("count", 0)
            }
        }