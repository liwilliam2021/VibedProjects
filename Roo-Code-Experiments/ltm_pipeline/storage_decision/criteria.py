"""Storage criteria definitions for evaluating rules."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..common.models import Rule, RuleType


class CriterionType(Enum):
    """Types of criteria for storage decisions."""
    CROSS_SESSION_VALUE = "cross_session_value"
    STABILITY = "stability"
    CLEAR_TRIGGERS = "clear_triggers"
    REDUCES_INCONSISTENCY = "reduces_inconsistency"
    SPECIFICITY = "specificity"
    CONFIDENCE = "confidence"


@dataclass
class CriterionResult:
    """Result of evaluating a single criterion."""
    criterion_type: CriterionType
    score: float  # 0.0 to 1.0
    reasoning: str
    metadata: Dict[str, Any] = None


class StorageCriteria:
    """Evaluate rules against storage criteria."""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize storage criteria.
        
        Args:
            weights: Custom weights for each criterion
        """
        self.weights = weights or {
            CriterionType.CROSS_SESSION_VALUE.value: 0.3,
            CriterionType.STABILITY.value: 0.25,
            CriterionType.CLEAR_TRIGGERS.value: 0.2,
            CriterionType.REDUCES_INCONSISTENCY.value: 0.15,
            CriterionType.SPECIFICITY.value: 0.05,
            CriterionType.CONFIDENCE.value: 0.05
        }
        
        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
    
    def evaluate_all_criteria(self, rule: Rule, context: Optional[Dict[str, Any]] = None) -> List[CriterionResult]:
        """Evaluate a rule against all criteria.
        
        Args:
            rule: Rule to evaluate
            context: Additional context for evaluation
            
        Returns:
            List of criterion results
        """
        results = []
        
        # Evaluate each criterion
        results.append(self.evaluate_cross_session_value(rule, context))
        results.append(self.evaluate_stability(rule, context))
        results.append(self.evaluate_clear_triggers(rule, context))
        results.append(self.evaluate_reduces_inconsistency(rule, context))
        results.append(self.evaluate_specificity(rule, context))
        results.append(self.evaluate_confidence(rule, context))
        
        return results
    
    def evaluate_cross_session_value(self, rule: Rule, context: Optional[Dict[str, Any]] = None) -> CriterionResult:
        """Evaluate if rule has value across multiple sessions.
        
        A rule has high cross-session value if it:
        - Addresses persistent patterns or conventions
        - Is not tied to specific temporary contexts
        - Has broad applicability
        """
        score = 0.0
        reasoning_parts = []
        
        # Check if rule is marked as persistent
        if context and context.get("rule_type") == RuleType.PERSISTENT:
            score += 0.4
            reasoning_parts.append("Rule is marked as persistent")
        
        # Check for persistent keywords in action description
        persistent_keywords = ["always", "never", "convention", "standard", "must", "should"]
        description_lower = rule.action.description.lower()
        keyword_count = sum(1 for kw in persistent_keywords if kw in description_lower)
        
        if keyword_count > 0:
            score += min(0.3 * keyword_count, 0.6)
            reasoning_parts.append(f"Contains {keyword_count} persistent keyword(s)")
        
        # Check if rule has broad match criteria
        if rule.match_criteria.type.value in ["pattern", "keyword"]:
            score += 0.2
            reasoning_parts.append("Has broad matching criteria")
        
        # Check for temporal limitations
        temporal_keywords = ["today", "now", "currently", "temporarily", "for this"]
        if any(kw in description_lower for kw in temporal_keywords):
            score *= 0.5
            reasoning_parts.append("Contains temporal limitations")
        
        # Ensure score is in valid range
        score = min(max(score, 0.0), 1.0)
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No specific indicators found"
        
        return CriterionResult(
            criterion_type=CriterionType.CROSS_SESSION_VALUE,
            score=score,
            reasoning=reasoning,
            metadata={"keyword_count": keyword_count}
        )
    
    def evaluate_stability(self, rule: Rule, context: Optional[Dict[str, Any]] = None) -> CriterionResult:
        """Evaluate rule stability.
        
        A stable rule:
        - Has clear, unambiguous conditions
        - Doesn't conflict with other rules
        - Has consistent application
        """
        score = 0.5  # Start neutral
        reasoning_parts = []
        
        # Check confidence score
        if rule.confidence >= 0.8:
            score += 0.3
            reasoning_parts.append(f"High confidence ({rule.confidence:.2f})")
        elif rule.confidence >= 0.6:
            score += 0.1
            reasoning_parts.append(f"Moderate confidence ({rule.confidence:.2f})")
        else:
            score -= 0.2
            reasoning_parts.append(f"Low confidence ({rule.confidence:.2f})")
        
        # Check for clear action type
        if rule.action.type.value in ["naming", "style"]:
            score += 0.2
            reasoning_parts.append("Clear action type (naming/style)")
        
        # Check for specific match criteria
        if rule.match_criteria.value and len(rule.match_criteria.value.split()) >= 2:
            score += 0.1
            reasoning_parts.append("Specific match criteria")
        
        # Check for potential conflicts (simplified check)
        if context and "existing_rules" in context:
            existing_rules = context["existing_rules"]
            conflicts = self._check_conflicts(rule, existing_rules)
            if conflicts:
                score -= 0.3
                reasoning_parts.append(f"Potential conflicts with {len(conflicts)} existing rule(s)")
        
        score = min(max(score, 0.0), 1.0)
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Neutral stability indicators"
        
        return CriterionResult(
            criterion_type=CriterionType.STABILITY,
            score=score,
            reasoning=reasoning
        )
    
    def evaluate_clear_triggers(self, rule: Rule, context: Optional[Dict[str, Any]] = None) -> CriterionResult:
        """Evaluate if rule has clear triggering conditions.
        
        Clear triggers mean:
        - Well-defined match criteria
        - Unambiguous conditions
        - Easy to determine when to apply
        """
        score = 0.0
        reasoning_parts = []
        
        # Check match criteria type
        if rule.match_criteria.type.value == "pattern":
            score += 0.4
            reasoning_parts.append("Pattern-based matching")
        elif rule.match_criteria.type.value == "keyword":
            score += 0.3
            reasoning_parts.append("Keyword-based matching")
        elif rule.match_criteria.type.value == "context":
            score += 0.2
            reasoning_parts.append("Context-based matching")
        
        # Check match value specificity
        if rule.match_criteria.value:
            value_words = rule.match_criteria.value.split()
            if len(value_words) >= 3:
                score += 0.3
                reasoning_parts.append("Specific match value")
            elif len(value_words) >= 2:
                score += 0.2
                reasoning_parts.append("Moderately specific match value")
            else:
                score += 0.1
                reasoning_parts.append("Generic match value")
        
        # Check for context information
        if rule.match_criteria.context:
            score += 0.2
            reasoning_parts.append("Has context information")
        
        # Check action clarity
        if rule.action.parameters:
            score += 0.1
            reasoning_parts.append("Has action parameters")
        
        score = min(max(score, 0.0), 1.0)
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No clear trigger indicators"
        
        return CriterionResult(
            criterion_type=CriterionType.CLEAR_TRIGGERS,
            score=score,
            reasoning=reasoning
        )
    
    def evaluate_reduces_inconsistency(self, rule: Rule, context: Optional[Dict[str, Any]] = None) -> CriterionResult:
        """Evaluate if rule helps reduce inconsistency.
        
        Rules that reduce inconsistency:
        - Standardize behavior
        - Enforce conventions
        - Prevent variations
        """
        score = 0.0
        reasoning_parts = []
        
        # Check for standardization keywords
        standardization_keywords = ["standard", "convention", "consistent", "uniform", "always", "never"]
        description_lower = rule.action.description.lower()
        
        keyword_matches = [kw for kw in standardization_keywords if kw in description_lower]
        if keyword_matches:
            score += min(0.2 * len(keyword_matches), 0.6)
            reasoning_parts.append(f"Contains standardization keywords: {', '.join(keyword_matches)}")
        
        # Check action type
        if rule.action.type.value in ["naming", "style", "structure"]:
            score += 0.3
            reasoning_parts.append(f"Enforces {rule.action.type.value} consistency")
        
        # Check if rule prevents variations
        if any(word in description_lower for word in ["must", "should", "require"]):
            score += 0.2
            reasoning_parts.append("Contains enforcement language")
        
        # Bonus for rules that explicitly mention consistency
        if "consistency" in description_lower or "inconsisten" in description_lower:
            score += 0.2
            reasoning_parts.append("Explicitly addresses consistency")
        
        score = min(max(score, 0.0), 1.0)
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No consistency indicators found"
        
        return CriterionResult(
            criterion_type=CriterionType.REDUCES_INCONSISTENCY,
            score=score,
            reasoning=reasoning,
            metadata={"keywords_found": keyword_matches}
        )
    
    def evaluate_specificity(self, rule: Rule, context: Optional[Dict[str, Any]] = None) -> CriterionResult:
        """Evaluate rule specificity.
        
        Specific rules are:
        - Not too broad or generic
        - Targeted to particular scenarios
        - Have clear scope
        """
        score = 0.5  # Start neutral
        reasoning_parts = []
        
        # Check match criteria specificity
        if rule.match_criteria.value:
            value_length = len(rule.match_criteria.value.split())
            if value_length >= 3:
                score += 0.3
                reasoning_parts.append("Highly specific match criteria")
            elif value_length == 2:
                score += 0.1
                reasoning_parts.append("Moderately specific match criteria")
            elif value_length == 1:
                score -= 0.2
                reasoning_parts.append("Generic match criteria")
        
        # Check for context constraints
        if rule.match_criteria.context:
            context_keys = len(rule.match_criteria.context.keys())
            score += min(0.1 * context_keys, 0.3)
            reasoning_parts.append(f"Has {context_keys} context constraint(s)")
        
        # Check action specificity
        if rule.action.parameters:
            param_count = len(rule.action.parameters)
            score += min(0.1 * param_count, 0.2)
            reasoning_parts.append(f"Has {param_count} action parameter(s)")
        
        # Penalize overly broad rules
        broad_terms = ["all", "any", "every", "always", "never"]
        description_lower = rule.action.description.lower()
        broad_count = sum(1 for term in broad_terms if term in description_lower)
        if broad_count > 1:
            score -= 0.2
            reasoning_parts.append("Contains multiple broad terms")
        
        score = min(max(score, 0.0), 1.0)
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Neutral specificity"
        
        return CriterionResult(
            criterion_type=CriterionType.SPECIFICITY,
            score=score,
            reasoning=reasoning
        )
    
    def evaluate_confidence(self, rule: Rule, context: Optional[Dict[str, Any]] = None) -> CriterionResult:
        """Evaluate based on rule confidence score.
        
        Higher confidence rules are more likely to be correct and valuable.
        """
        score = rule.confidence
        
        if score >= 0.9:
            reasoning = "Very high confidence rule"
        elif score >= 0.7:
            reasoning = "High confidence rule"
        elif score >= 0.5:
            reasoning = "Moderate confidence rule"
        else:
            reasoning = "Low confidence rule"
        
        return CriterionResult(
            criterion_type=CriterionType.CONFIDENCE,
            score=score,
            reasoning=reasoning,
            metadata={"raw_confidence": rule.confidence}
        )
    
    def calculate_weighted_score(self, criterion_results: List[CriterionResult]) -> float:
        """Calculate weighted average score from criterion results.
        
        Args:
            criterion_results: List of criterion evaluation results
            
        Returns:
            Weighted score (0.0 to 1.0)
        """
        total_score = 0.0
        
        for result in criterion_results:
            weight = self.weights.get(result.criterion_type.value, 0.0)
            total_score += result.score * weight
        
        return total_score
    
    def _check_conflicts(self, rule: Rule, existing_rules: List[Rule]) -> List[Rule]:
        """Check for potential conflicts with existing rules.
        
        Args:
            rule: Rule to check
            existing_rules: List of existing rules
            
        Returns:
            List of potentially conflicting rules
        """
        conflicts = []
        
        for existing in existing_rules:
            # Simple conflict detection based on same match criteria but different actions
            if (rule.match_criteria.type == existing.match_criteria.type and
                rule.match_criteria.value == existing.match_criteria.value and
                rule.action.description != existing.action.description):
                conflicts.append(existing)
            
            # Check for contradictory actions on same target
            if (rule.action.type == existing.action.type and
                self._are_actions_contradictory(rule.action, existing.action)):
                conflicts.append(existing)
        
        return conflicts
    
    def _are_actions_contradictory(self, action1: Any, action2: Any) -> bool:
        """Check if two actions are contradictory.
        
        Args:
            action1: First action
            action2: Second action
            
        Returns:
            True if actions are contradictory
        """
        # Simple contradiction detection
        desc1 = action1.description.lower()
        desc2 = action2.description.lower()
        
        # Check for opposite keywords
        opposites = [
            ("always", "never"),
            ("must", "must not"),
            ("should", "should not"),
            ("use", "avoid"),
            ("enable", "disable")
        ]
        
        for word1, word2 in opposites:
            if (word1 in desc1 and word2 in desc2) or (word2 in desc1 and word1 in desc2):
                return True
        
        return False