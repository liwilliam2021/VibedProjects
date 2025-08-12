"""Storage decision maker for evaluating and deciding which rules to store."""

from typing import List, Tuple, Dict, Any, Optional
import time
from datetime import datetime

from ..common.models import Rule, StorageDecision
from ..common.logger import get_logger
from ..common.metrics import MetricsCollector
from .criteria import StorageCriteria, CriterionResult


class StorageDecisionMaker:
    """Make storage decisions for extracted rules."""
    
    def __init__(self, 
                 criteria_weights: Optional[Dict[str, float]] = None,
                 storage_threshold: float = 0.7):
        """Initialize the storage decision maker.
        
        Args:
            criteria_weights: Custom weights for storage criteria
            storage_threshold: Minimum score required for storage
        """
        self.logger = get_logger("StorageDecisionMaker")
        self.metrics = MetricsCollector("storage_decision")
        self.criteria = StorageCriteria(criteria_weights)
        self.storage_threshold = storage_threshold
        
        self.logger.info(f"Initialized with storage threshold: {storage_threshold}")
    
    def evaluate_rules(self, 
                      rules: List[Rule], 
                      context: Optional[Dict[str, Any]] = None) -> List[Tuple[Rule, str, str]]:
        """Evaluate rules for storage.
        
        Args:
            rules: List of rules to evaluate
            context: Additional context for evaluation
            
        Returns:
            List of tuples (rule, decision, justification)
        """
        start_time = time.time()
        results = []
        
        self.logger.info(f"Evaluating {len(rules)} rules for storage")
        
        # Get existing rules from context if available
        existing_rules = []
        if context and "existing_rules" in context:
            existing_rules = context["existing_rules"]
            self.logger.info(f"Considering {len(existing_rules)} existing rules for conflict detection")
        
        # Evaluate each rule
        for rule in rules:
            decision, justification, score = self._evaluate_single_rule(rule, existing_rules)
            results.append((rule, decision, justification))
            
            # Log decision
            self.logger.log_storage_decision(
                rule_id=rule.id,
                decision=decision,
                confidence=score,
                justification=justification
            )
            
            # Record metrics
            self.metrics.record(f"decision_{decision}", 1.0, rule_id=rule.id)
        
        # Calculate summary metrics
        store_count = sum(1 for _, decision, _ in results if decision == "store")
        ignore_count = len(results) - store_count
        
        processing_time = time.time() - start_time
        
        self.logger.info(f"Storage decisions complete: {store_count} store, {ignore_count} ignore")
        
        # Record summary metrics
        self.metrics.record("total_evaluated", len(rules))
        self.metrics.record("total_stored", store_count)
        self.metrics.record("total_ignored", ignore_count)
        self.metrics.record("storage_rate", store_count / len(rules) if rules else 0.0)
        self.metrics.record("processing_time", processing_time)
        
        return results
    
    def _evaluate_single_rule(self, 
                             rule: Rule, 
                             existing_rules: List[Rule]) -> Tuple[str, str, float]:
        """Evaluate a single rule for storage.
        
        Args:
            rule: Rule to evaluate
            existing_rules: List of existing rules for conflict checking
            
        Returns:
            Tuple of (decision, justification, score)
        """
        # Evaluate against all criteria
        context = {
            "existing_rules": existing_rules,
            "rule_type": getattr(rule, "type", None)
        }
        
        criterion_results = self.criteria.evaluate_all_criteria(rule, context)
        
        # Calculate weighted score
        weighted_score = self.criteria.calculate_weighted_score(criterion_results)
        
        # Make decision
        decision = "store" if weighted_score >= self.storage_threshold else "ignore"
        
        # Generate justification
        justification = self._generate_justification(
            decision, weighted_score, criterion_results
        )
        
        return decision, justification, weighted_score
    
    def _generate_justification(self, 
                               decision: str, 
                               score: float, 
                               criterion_results: List[CriterionResult]) -> str:
        """Generate human-readable justification for the decision.
        
        Args:
            decision: The storage decision
            score: Overall weighted score
            criterion_results: Individual criterion results
            
        Returns:
            Justification string
        """
        parts = [f"Score: {score:.2f} ({'above' if decision == 'store' else 'below'} threshold {self.storage_threshold})"]
        
        # Sort criteria by score (descending)
        sorted_results = sorted(criterion_results, key=lambda x: x.score, reverse=True)
        
        # Add top positive factors
        positive_factors = [r for r in sorted_results if r.score >= 0.7]
        if positive_factors:
            parts.append("Positive factors:")
            for result in positive_factors[:3]:  # Top 3
                parts.append(f"  - {result.criterion_type.value}: {result.reasoning}")
        
        # Add significant negative factors
        negative_factors = [r for r in sorted_results if r.score < 0.3]
        if negative_factors:
            parts.append("Negative factors:")
            for result in negative_factors[:2]:  # Top 2
                parts.append(f"  - {result.criterion_type.value}: {result.reasoning}")
        
        return "; ".join(parts)
    
    def batch_evaluate(self, 
                      rule_batches: List[Dict[str, Any]],
                      global_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Evaluate multiple batches of rules.
        
        Args:
            rule_batches: List of dictionaries containing 'rules' and optional 'context'
            global_context: Context to apply to all batches
            
        Returns:
            List of evaluation results for each batch
        """
        self.logger.info(f"Batch evaluating {len(rule_batches)} rule sets")
        
        all_results = []
        cumulative_existing_rules = []
        
        for i, batch in enumerate(rule_batches):
            rules = batch["rules"]
            batch_context = batch.get("context", {})
            
            # Merge contexts
            context = {
                **(global_context or {}),
                **batch_context,
                "existing_rules": cumulative_existing_rules.copy()
            }
            
            # Evaluate batch
            results = self.evaluate_rules(rules, context)
            
            # Add stored rules to cumulative list
            for rule, decision, _ in results:
                if decision == "store":
                    cumulative_existing_rules.append(rule)
            
            # Package results
            batch_results = {
                "batch_id": batch.get("id", f"batch_{i}"),
                "results": results,
                "summary": {
                    "total_rules": len(rules),
                    "stored": sum(1 for _, d, _ in results if d == "store"),
                    "ignored": sum(1 for _, d, _ in results if d == "ignore")
                }
            }
            
            all_results.append(batch_results)
        
        return all_results
    
    def create_storage_decisions(self, 
                                evaluation_results: List[Tuple[Rule, str, str]]) -> List[StorageDecision]:
        """Create StorageDecision objects from evaluation results.
        
        Args:
            evaluation_results: List of (rule, decision, justification) tuples
            
        Returns:
            List of StorageDecision objects
        """
        decisions = []
        
        for rule, decision, justification in evaluation_results:
            storage_decision = StorageDecision(
                rule_id=rule.id,
                decision=decision,
                justification=justification,
                confidence=rule.confidence,
                timestamp=datetime.utcnow()
            )
            decisions.append(storage_decision)
        
        return decisions
    
    def filter_for_storage(self, rules: List[Rule], 
                          context: Optional[Dict[str, Any]] = None) -> List[Rule]:
        """Filter rules to only those that should be stored.
        
        Args:
            rules: List of rules to filter
            context: Additional context for evaluation
            
        Returns:
            List of rules that should be stored
        """
        results = self.evaluate_rules(rules, context)
        return [rule for rule, decision, _ in results if decision == "store"]
    
    def get_decision_statistics(self, 
                               evaluation_results: List[Tuple[Rule, str, str]]) -> Dict[str, Any]:
        """Calculate statistics about storage decisions.
        
        Args:
            evaluation_results: List of evaluation results
            
        Returns:
            Dictionary of statistics
        """
        total = len(evaluation_results)
        stored = sum(1 for _, decision, _ in evaluation_results if decision == "store")
        ignored = total - stored
        
        # Group by rule type
        type_stats = {}
        for rule, decision, _ in evaluation_results:
            rule_type = rule.action.type.value
            if rule_type not in type_stats:
                type_stats[rule_type] = {"total": 0, "stored": 0, "ignored": 0}
            
            type_stats[rule_type]["total"] += 1
            if decision == "store":
                type_stats[rule_type]["stored"] += 1
            else:
                type_stats[rule_type]["ignored"] += 1
        
        # Calculate storage rates by type
        for stats in type_stats.values():
            stats["storage_rate"] = stats["stored"] / stats["total"] if stats["total"] > 0 else 0.0
        
        # Confidence statistics
        stored_confidences = [rule.confidence for rule, decision, _ in evaluation_results 
                            if decision == "store"]
        ignored_confidences = [rule.confidence for rule, decision, _ in evaluation_results 
                             if decision == "ignore"]
        
        return {
            "total_evaluated": total,
            "total_stored": stored,
            "total_ignored": ignored,
            "overall_storage_rate": stored / total if total > 0 else 0.0,
            "by_type": type_stats,
            "confidence_stats": {
                "avg_confidence_stored": sum(stored_confidences) / len(stored_confidences) 
                                       if stored_confidences else 0.0,
                "avg_confidence_ignored": sum(ignored_confidences) / len(ignored_confidences) 
                                        if ignored_confidences else 0.0,
                "min_confidence_stored": min(stored_confidences) if stored_confidences else 0.0,
                "max_confidence_stored": max(stored_confidences) if stored_confidences else 0.0,
                "min_confidence_ignored": min(ignored_confidences) if ignored_confidences else 0.0,
                "max_confidence_ignored": max(ignored_confidences) if ignored_confidences else 0.0
            }
        }
    
    def explain_decision(self, rule: Rule, 
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Provide detailed explanation for a storage decision.
        
        Args:
            rule: Rule to explain decision for
            context: Additional context
            
        Returns:
            Detailed explanation dictionary
        """
        # Evaluate the rule
        existing_rules = context.get("existing_rules", []) if context else []
        decision, justification, score = self._evaluate_single_rule(rule, existing_rules)
        
        # Get detailed criterion results
        criterion_results = self.criteria.evaluate_all_criteria(rule, context)
        
        # Build explanation
        explanation = {
            "rule_id": rule.id,
            "rule_description": rule.action.description,
            "decision": decision,
            "overall_score": score,
            "threshold": self.storage_threshold,
            "justification": justification,
            "criterion_scores": {}
        }
        
        # Add individual criterion details
        for result in criterion_results:
            explanation["criterion_scores"][result.criterion_type.value] = {
                "score": result.score,
                "weight": self.criteria.weights.get(result.criterion_type.value, 0.0),
                "weighted_contribution": result.score * self.criteria.weights.get(result.criterion_type.value, 0.0),
                "reasoning": result.reasoning,
                "metadata": result.metadata
            }
        
        # Add recommendation
        if decision == "store":
            explanation["recommendation"] = "This rule should be stored in long-term memory."
        else:
            explanation["recommendation"] = "This rule should not be stored; it may be too specific, temporary, or low-confidence."
        
        return explanation
    
    def update_threshold(self, new_threshold: float) -> None:
        """Update the storage threshold.
        
        Args:
            new_threshold: New threshold value (0.0 to 1.0)
        """
        if not 0.0 <= new_threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        old_threshold = self.storage_threshold
        self.storage_threshold = new_threshold
        
        self.logger.info(f"Updated storage threshold from {old_threshold} to {new_threshold}")
        self.metrics.record("threshold_update", new_threshold, 
                          old_threshold=old_threshold,
                          timestamp=datetime.utcnow().isoformat())