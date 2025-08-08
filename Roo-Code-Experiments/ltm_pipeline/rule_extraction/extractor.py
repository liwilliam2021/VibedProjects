"""Rule extraction implementation for the LTM pipeline."""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time

from ..common.models import (
    Rule, Transcript, TranscriptSegment, 
    MatchCriteria, Action, RuleType,
    MatchType, ActionType
)
from ..common.logger import get_logger
from ..common.metrics import MetricsCollector


class RuleExtractor:
    """Extract rules from transcripts using pattern matching and NLP."""
    
    def __init__(self, extraction_patterns: Optional[Dict[str, str]] = None,
                 confidence_threshold: float = 0.7):
        """Initialize the rule extractor.
        
        Args:
            extraction_patterns: Custom extraction patterns
            confidence_threshold: Minimum confidence for rule extraction
        """
        self.logger = get_logger("RuleExtractor")
        self.metrics = MetricsCollector("rule_extraction")
        self.confidence_threshold = confidence_threshold
        
        # Default extraction patterns
        self.patterns = extraction_patterns or {
            "persistent_rule": r"(?i)(always|must|should|never)\s+(\w+.*?)(?:\.|$)",
            "naming_rule": r"(?i)(use|prefer|follow)\s+(camelCase|snake_case|PascalCase|kebab-case)\s+(?:for\s+)?(\w+)",
            "style_rule": r"(?i)(use|prefer)\s+(\d+|tabs?)\s+(spaces?|tabs?)\s+(?:for\s+)?(?:indentation|indent)",
            "structure_rule": r"(?i)(organize|group|keep|separate)\s+(\w+.*?)\s+(?:by|in|together)",
            "behavior_rule": r"(?i)(always|never|prefer)\s+(\w+.*?)\s+(?:before|after|when|over)\s+(\w+.*?)(?:\.|$)",
            "convention_rule": r"(?i)(?:convention|standard|format|style)\s+(?:is|should be|must be)\s+(\w+.*?)(?:\.|$)"
        }
        
        # Rule type indicators
        self.rule_indicators = {
            "persistent": ["always", "never", "must", "should", "convention", "standard"],
            "short_term": ["for this", "in this case", "temporarily", "just for now", "specific"],
            "naming": ["camelCase", "snake_case", "PascalCase", "kebab-case", "naming"],
            "style": ["indentation", "spaces", "tabs", "brackets", "braces", "line length"],
            "structure": ["organize", "group", "separate", "files", "modules", "directories"],
            "behavior": ["validate", "check", "log", "handle", "process", "before", "after"]
        }
    
    def extract_rules(self, transcript: Transcript) -> List[Rule]:
        """Extract candidate rules from a transcript.
        
        Args:
            transcript: Transcript to extract rules from
            
        Returns:
            List of extracted Rule objects
        """
        start_time = time.time()
        rules = []
        
        self.logger.info(f"Starting rule extraction for transcript {transcript.id}")
        
        for segment in transcript.segments:
            # Skip irrelevant segments
            if segment.type == RuleType.IRRELEVANT:
                continue
            
            # Check if segment contains rule indicators
            if self._contains_rule_indicator(segment.content):
                extracted_rules = self._extract_rules_from_segment(segment, transcript.id)
                rules.extend(extracted_rules)
        
        # Post-process rules
        rules = self._post_process_rules(rules)
        
        processing_time = time.time() - start_time
        self.logger.log_rule_extraction(
            transcript_id=transcript.id,
            rules_found=len(rules),
            processing_time=processing_time
        )
        
        self.metrics.record("rules_extracted", len(rules), 
                          transcript_id=transcript.id,
                          processing_time=processing_time)
        
        return rules
    
    def _contains_rule_indicator(self, text: str) -> bool:
        """Check if text likely contains a rule.
        
        Args:
            text: Text to check
            
        Returns:
            True if text likely contains a rule
        """
        text_lower = text.lower()
        
        # Check for any rule indicators
        for indicators in self.rule_indicators.values():
            if any(indicator in text_lower for indicator in indicators):
                return True
        
        return False
    
    def _extract_rules_from_segment(self, segment: TranscriptSegment, 
                                   transcript_id: str) -> List[Rule]:
        """Extract rules from a single segment.
        
        Args:
            segment: Segment to extract from
            transcript_id: ID of the parent transcript
            
        Returns:
            List of extracted rules
        """
        rules = []
        content = segment.content
        
        # Try each extraction pattern
        for pattern_name, pattern in self.patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                rule = self._create_rule_from_match(
                    match, pattern_name, segment, transcript_id
                )
                if rule and rule.confidence >= self.confidence_threshold:
                    rules.append(rule)
        
        # If no pattern matches, try general extraction
        if not rules and self._is_likely_rule(content):
            rule = self._create_general_rule(segment, transcript_id)
            if rule and rule.confidence >= self.confidence_threshold:
                rules.append(rule)
        
        return rules
    
    def _create_rule_from_match(self, match: re.Match, pattern_name: str,
                               segment: TranscriptSegment, 
                               transcript_id: str) -> Optional[Rule]:
        """Create a rule from a regex match.
        
        Args:
            match: Regex match object
            pattern_name: Name of the pattern that matched
            segment: Source segment
            transcript_id: ID of the transcript
            
        Returns:
            Created Rule or None
        """
        try:
            # Extract components based on pattern type
            if "naming" in pattern_name:
                return self._create_naming_rule(match, segment, transcript_id)
            elif "style" in pattern_name:
                return self._create_style_rule(match, segment, transcript_id)
            elif "structure" in pattern_name:
                return self._create_structure_rule(match, segment, transcript_id)
            elif "behavior" in pattern_name:
                return self._create_behavior_rule(match, segment, transcript_id)
            else:
                return self._create_general_rule(segment, transcript_id)
        except Exception as e:
            self.logger.debug(f"Failed to create rule from match: {e}")
            return None
    
    def _create_naming_rule(self, match: re.Match, segment: TranscriptSegment,
                           transcript_id: str) -> Rule:
        """Create a naming convention rule."""
        groups = match.groups()
        convention = groups[1] if len(groups) > 1 else "unknown"
        construct = groups[2] if len(groups) > 2 else "code"
        
        return Rule(
            match_criteria=MatchCriteria(
                type=MatchType.PATTERN,
                value=f"{construct}.*naming",
                context={"language": self._detect_language(segment.content)}
            ),
            action=Action(
                type=ActionType.NAMING,
                description=f"Use {convention} for {construct}",
                parameters={"convention": convention, "construct": construct}
            ),
            rationale=f"Naming convention specified in {segment.speaker} statement",
            confidence=self._calculate_confidence(segment, "naming"),
            source_id=transcript_id,
            timestamp=segment.timestamp
        )
    
    def _create_style_rule(self, match: re.Match, segment: TranscriptSegment,
                          transcript_id: str) -> Rule:
        """Create a code style rule."""
        groups = match.groups()
        amount = groups[1] if len(groups) > 1 else "4"
        unit = groups[2] if len(groups) > 2 else "spaces"
        
        return Rule(
            match_criteria=MatchCriteria(
                type=MatchType.KEYWORD,
                value="indentation",
                context={"file_type": "source_code"}
            ),
            action=Action(
                type=ActionType.STYLE,
                description=f"Use {amount} {unit} for indentation",
                parameters={"amount": amount, "unit": unit}
            ),
            rationale=f"Style preference from {segment.speaker}",
            confidence=self._calculate_confidence(segment, "style"),
            source_id=transcript_id,
            timestamp=segment.timestamp
        )
    
    def _create_structure_rule(self, match: re.Match, segment: TranscriptSegment,
                              transcript_id: str) -> Rule:
        """Create a project structure rule."""
        groups = match.groups()
        action_word = groups[0] if groups else "organize"
        target = groups[1] if len(groups) > 1 else "files"
        
        return Rule(
            match_criteria=MatchCriteria(
                type=MatchType.CONTEXT,
                value="project_structure",
                context={"target": target}
            ),
            action=Action(
                type=ActionType.STRUCTURE,
                description=f"{action_word.capitalize()} {target}",
                parameters={"action": action_word, "target": target}
            ),
            rationale=f"Project organization guideline",
            confidence=self._calculate_confidence(segment, "structure"),
            source_id=transcript_id,
            timestamp=segment.timestamp
        )
    
    def _create_behavior_rule(self, match: re.Match, segment: TranscriptSegment,
                             transcript_id: str) -> Rule:
        """Create a behavioral rule."""
        groups = match.groups()
        modifier = groups[0] if groups else "always"
        action = groups[1] if len(groups) > 1 else "validate"
        condition = groups[2] if len(groups) > 2 else "processing"
        
        return Rule(
            match_criteria=MatchCriteria(
                type=MatchType.PATTERN,
                value=f"{action}.*{condition}",
                context={"modifier": modifier}
            ),
            action=Action(
                type=ActionType.BEHAVIOR,
                description=f"{modifier.capitalize()} {action} when {condition}",
                parameters={"modifier": modifier, "action": action, "condition": condition}
            ),
            rationale=f"Behavioral guideline from conversation",
            confidence=self._calculate_confidence(segment, "behavior"),
            source_id=transcript_id,
            timestamp=segment.timestamp
        )
    
    def _create_general_rule(self, segment: TranscriptSegment,
                            transcript_id: str) -> Rule:
        """Create a general rule when specific patterns don't match."""
        # Determine rule type from content
        rule_type = self._determine_rule_type(segment.content)
        
        return Rule(
            match_criteria=MatchCriteria(
                type=MatchType.KEYWORD,
                value=self._extract_key_terms(segment.content),
                context={"original_text": segment.content[:100]}
            ),
            action=Action(
                type=rule_type,
                description=segment.content.strip(),
                parameters={}
            ),
            rationale="General rule extracted from conversation",
            confidence=self._calculate_confidence(segment, "general"),
            source_id=transcript_id,
            timestamp=segment.timestamp
        )
    
    def _is_likely_rule(self, text: str) -> bool:
        """Check if text is likely a rule even without pattern match."""
        text_lower = text.lower()
        
        # Count rule indicators
        indicator_count = 0
        for indicators in self.rule_indicators.values():
            indicator_count += sum(1 for ind in indicators if ind in text_lower)
        
        # Check for imperative mood or directive language
        directive_words = ["use", "prefer", "avoid", "ensure", "make sure", "remember"]
        has_directive = any(word in text_lower for word in directive_words)
        
        return indicator_count >= 2 or (indicator_count >= 1 and has_directive)
    
    def _calculate_confidence(self, segment: TranscriptSegment, 
                             rule_type: str) -> float:
        """Calculate confidence score for a rule.
        
        Args:
            segment: Source segment
            rule_type: Type of rule
            
        Returns:
            Confidence score (0-1)
        """
        base_confidence = 0.5
        
        # Adjust based on segment type
        if segment.type == RuleType.PERSISTENT:
            base_confidence += 0.3
        elif segment.type == RuleType.SHORT_TERM:
            base_confidence += 0.1
        
        # Adjust based on speaker
        if segment.speaker == "user":
            base_confidence += 0.1
        
        # Adjust based on rule type specificity
        if rule_type in ["naming", "style"]:
            base_confidence += 0.1
        
        # Check for strong indicators
        strong_indicators = ["always", "never", "must"]
        if any(ind in segment.content.lower() for ind in strong_indicators):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _determine_rule_type(self, text: str) -> ActionType:
        """Determine the action type for a rule based on text content."""
        text_lower = text.lower()
        
        # Check each category
        type_scores = {
            ActionType.NAMING: sum(1 for ind in self.rule_indicators["naming"] if ind in text_lower),
            ActionType.STYLE: sum(1 for ind in self.rule_indicators["style"] if ind in text_lower),
            ActionType.STRUCTURE: sum(1 for ind in self.rule_indicators["structure"] if ind in text_lower),
            ActionType.BEHAVIOR: sum(1 for ind in self.rule_indicators["behavior"] if ind in text_lower)
        }
        
        # Return type with highest score, default to BEHAVIOR
        return max(type_scores.items(), key=lambda x: x[1])[0] if max(type_scores.values()) > 0 else ActionType.BEHAVIOR
    
    def _extract_key_terms(self, text: str) -> str:
        """Extract key terms from text for matching."""
        # Simple keyword extraction
        important_words = []
        words = text.lower().split()
        
        # Skip common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", 
                     "being", "have", "has", "had", "do", "does", "did", "will", 
                     "would", "could", "should", "may", "might", "must", "shall",
                     "to", "of", "in", "for", "on", "with", "at", "by", "from"}
        
        for word in words:
            word = word.strip(".,!?;:")
            if word and word not in stop_words and len(word) > 2:
                important_words.append(word)
        
        # Return first few important words
        return " ".join(important_words[:3]) if important_words else "general"
    
    def _detect_language(self, text: str) -> str:
        """Detect programming language mentioned in text."""
        languages = ["javascript", "python", "typescript", "java", "go", "rust", 
                    "c++", "c#", "ruby", "php", "swift", "kotlin"]
        
        text_lower = text.lower()
        for lang in languages:
            if lang in text_lower:
                return lang.title()
        
        return "General"
    
    def _post_process_rules(self, rules: List[Rule]) -> List[Rule]:
        """Post-process extracted rules to remove duplicates and improve quality.
        
        Args:
            rules: List of extracted rules
            
        Returns:
            Processed list of rules
        """
        if not rules:
            return rules
        
        # Remove exact duplicates
        unique_rules = []
        seen_descriptions = set()
        
        for rule in rules:
            desc = rule.action.description.lower().strip()
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique_rules.append(rule)
        
        # Merge similar rules
        merged_rules = self._merge_similar_rules(unique_rules)
        
        self.logger.info(f"Post-processing: {len(rules)} -> {len(merged_rules)} rules")
        
        return merged_rules
    
    def _merge_similar_rules(self, rules: List[Rule]) -> List[Rule]:
        """Merge rules that are very similar.
        
        Args:
            rules: List of rules to merge
            
        Returns:
            Merged list of rules
        """
        if len(rules) <= 1:
            return rules
        
        merged = []
        processed = set()
        
        for i, rule1 in enumerate(rules):
            if i in processed:
                continue
            
            # Find similar rules
            similar_indices = [i]
            for j, rule2 in enumerate(rules[i+1:], i+1):
                if j not in processed and self._are_rules_similar(rule1, rule2):
                    similar_indices.append(j)
                    processed.add(j)
            
            # Merge if multiple similar rules found
            if len(similar_indices) > 1:
                merged_rule = self._merge_rules([rules[idx] for idx in similar_indices])
                merged.append(merged_rule)
            else:
                merged.append(rule1)
        
        return merged
    
    def _are_rules_similar(self, rule1: Rule, rule2: Rule) -> bool:
        """Check if two rules are similar enough to merge."""
        # Check if same action type
        if rule1.action.type != rule2.action.type:
            return False
        
        # Check if match criteria are similar
        if rule1.match_criteria.type == rule2.match_criteria.type:
            # Simple similarity check on values
            value1 = rule1.match_criteria.value.lower()
            value2 = rule2.match_criteria.value.lower()
            
            # Check for common words
            words1 = set(value1.split())
            words2 = set(value2.split())
            common = words1 & words2
            
            if len(common) >= min(len(words1), len(words2)) * 0.5:
                return True
        
        return False
    
    def _merge_rules(self, rules: List[Rule]) -> Rule:
        """Merge multiple similar rules into one."""
        # Use the rule with highest confidence as base
        base_rule = max(rules, key=lambda r: r.confidence)
        
        # Average confidence scores
        avg_confidence = sum(r.confidence for r in rules) / len(rules)
        
        # Combine descriptions
        descriptions = [r.action.description for r in rules]
        combined_description = "; ".join(set(descriptions))
        
        # Create merged rule
        merged = Rule(
            id=base_rule.id,
            match_criteria=base_rule.match_criteria,
            action=Action(
                type=base_rule.action.type,
                description=combined_description,
                parameters=base_rule.action.parameters
            ),
            rationale=f"Merged from {len(rules)} similar rules",
            confidence=avg_confidence,
            source_id=base_rule.source_id,
            timestamp=base_rule.timestamp,
            metadata={"merged_from": [r.id for r in rules]}
        )
        
        return merged