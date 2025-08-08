"""Synthetic data generator for the LTM pipeline."""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from ..common.models import (
    Rule, Transcript, TranscriptSegment, Task,
    RuleType, MatchType, ActionType, MatchCriteria, Action
)


class SyntheticDataGenerator:
    """Generate synthetic data for testing the LTM pipeline."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        
        # Templates for generating rules
        self.rule_templates = {
            "naming": [
                ("always use {convention} for {language} {construct}", "naming"),
                ("prefer {convention} naming for {construct}", "naming"),
                ("{construct} should follow {convention} convention", "naming")
            ],
            "style": [
                ("use {spaces} spaces for indentation in {language}", "style"),
                ("always put {bracket_style} on {position}", "style"),
                ("limit line length to {length} characters", "style")
            ],
            "structure": [
                ("organize {language} files by {organization}", "structure"),
                ("keep {construct} in separate files", "structure"),
                ("group related {construct} together", "structure")
            ],
            "behavior": [
                ("always {action} before {event}", "behavior"),
                ("never {action} without {condition}", "behavior"),
                ("prefer {approach} over {alternative}", "behavior")
            ]
        }
        
        # Vocabulary for generating content
        self.vocabulary = {
            "convention": ["camelCase", "snake_case", "PascalCase", "kebab-case"],
            "language": ["JavaScript", "Python", "TypeScript", "Java", "Go"],
            "construct": ["variables", "functions", "classes", "interfaces", "constants"],
            "spaces": ["2", "4", "tabs"],
            "bracket_style": ["opening braces", "closing braces", "brackets"],
            "position": ["same line", "new line", "next line"],
            "length": ["80", "100", "120"],
            "organization": ["feature", "type", "module"],
            "action": ["validate input", "log errors", "clean up resources", "check permissions"],
            "event": ["processing", "saving", "returning", "throwing"],
            "condition": ["validation", "authorization", "error handling"],
            "approach": ["async/await", "composition", "functional programming"],
            "alternative": ["callbacks", "inheritance", "imperative programming"]
        }
        
        # Chatter templates
        self.chatter_templates = [
            "That sounds good",
            "I understand",
            "Let me think about that",
            "The weather is {weather} today",
            "I had {meal} for {time}",
            "Have you seen the latest {topic}?",
            "That reminds me of {memory}",
            "Interesting point about {subject}"
        ]
        
        self.chatter_vocabulary = {
            "weather": ["nice", "rainy", "sunny", "cloudy", "cold"],
            "meal": ["pizza", "salad", "sandwich", "soup", "pasta"],
            "time": ["breakfast", "lunch", "dinner", "brunch"],
            "topic": ["news", "movie", "book", "article", "video"],
            "memory": ["a project", "a conversation", "an idea", "a meeting"],
            "subject": ["technology", "design", "architecture", "testing"]
        }
    
    def generate_transcript(
        self, 
        rule_mix: Dict[str, float],
        num_segments: int = 20,
        session_duration: int = 1800
    ) -> Transcript:
        """Generate a synthetic transcript with specified rule mix.
        
        Args:
            rule_mix: Dictionary with keys 'persistent', 'short_term', 'irrelevant'
                     and values as proportions (should sum to 1.0)
            num_segments: Number of segments in the transcript
            session_duration: Duration of session in seconds
            
        Returns:
            Generated Transcript object
        """
        # Normalize rule mix
        total = sum(rule_mix.values())
        rule_mix = {k: v/total for k, v in rule_mix.items()}
        
        # Generate segments
        segments = []
        current_time = datetime.utcnow()
        time_increment = session_duration / num_segments
        
        for i in range(num_segments):
            # Determine segment type based on mix
            rand = random.random()
            if rand < rule_mix.get('persistent', 0.3):
                segment_type = RuleType.PERSISTENT
                content = self._generate_rule_content("persistent")
            elif rand < rule_mix.get('persistent', 0.3) + rule_mix.get('short_term', 0.2):
                segment_type = RuleType.SHORT_TERM
                content = self._generate_rule_content("short_term")
            else:
                segment_type = RuleType.IRRELEVANT
                content = self._generate_chatter()
            
            # Alternate between user and assistant
            speaker = "user" if i % 2 == 0 else "assistant"
            
            segment = TranscriptSegment(
                speaker=speaker,
                content=content,
                type=segment_type,
                timestamp=current_time + timedelta(seconds=i * time_increment)
            )
            segments.append(segment)
        
        # Create transcript
        transcript = Transcript(
            id=f"transcript_{uuid.uuid4().hex[:8]}",
            segments=segments,
            session_id=f"session_{uuid.uuid4().hex[:8]}",
            duration=session_duration,
            tags=self._generate_tags(segments)
        )
        
        return transcript
    
    def _generate_rule_content(self, rule_type: str) -> str:
        """Generate content for a rule segment.
        
        Args:
            rule_type: Type of rule (persistent or short_term)
            
        Returns:
            Generated rule content
        """
        # Choose a random category
        category = random.choice(list(self.rule_templates.keys()))
        template, _ = random.choice(self.rule_templates[category])
        
        # Fill in the template
        content = template
        for placeholder in self.vocabulary:
            if f"{{{placeholder}}}" in content:
                value = random.choice(self.vocabulary[placeholder])
                content = content.replace(f"{{{placeholder}}}", value)
        
        # Add context for short-term rules
        if rule_type == "short_term":
            context_phrases = [
                "For this specific project, ",
                "In this case, ",
                "Just for now, ",
                "Temporarily, "
            ]
            content = random.choice(context_phrases) + content.lower()
        
        return content
    
    def _generate_chatter(self) -> str:
        """Generate irrelevant chatter content.
        
        Returns:
            Generated chatter content
        """
        template = random.choice(self.chatter_templates)
        
        # Fill in the template
        content = template
        for placeholder in self.chatter_vocabulary:
            if f"{{{placeholder}}}" in content:
                value = random.choice(self.chatter_vocabulary[placeholder])
                content = content.replace(f"{{{placeholder}}}", value)
        
        return content
    
    def _generate_tags(self, segments: List[TranscriptSegment]) -> List[str]:
        """Generate tags based on segment content.
        
        Args:
            segments: List of transcript segments
            
        Returns:
            List of tags
        """
        tags = []
        
        # Check for rule types
        has_persistent = any(s.type == RuleType.PERSISTENT for s in segments)
        has_short_term = any(s.type == RuleType.SHORT_TERM for s in segments)
        
        if has_persistent:
            tags.append("persistent_rules")
        if has_short_term:
            tags.append("short_term_rules")
        
        # Check for specific content
        content = " ".join(s.content for s in segments).lower()
        if "naming" in content or "convention" in content:
            tags.append("naming_conventions")
        if "style" in content or "indentation" in content:
            tags.append("code_style")
        if "structure" in content or "organize" in content:
            tags.append("project_structure")
        
        return tags
    
    def generate_test_task(
        self, 
        rule_types: List[str],
        language: str = "JavaScript"
    ) -> Task:
        """Generate a test task that should trigger specific rules.
        
        Args:
            rule_types: Types of rules this task should trigger
            language: Programming language for the task
            
        Returns:
            Generated Task object
        """
        # Task templates based on rule types
        task_templates = {
            "naming": {
                "description": "Create a function to {action} {data}",
                "context": {
                    "variables_needed": ["userName", "userAge", "totalScore"],
                    "existing_code": "function getUserData() { return {}; }"
                }
            },
            "style": {
                "description": "Format the following code according to project standards",
                "context": {
                    "code_to_format": "function calculate(x,y){return x+y;}",
                    "current_indentation": "mixed"
                }
            },
            "structure": {
                "description": "Organize the {module} module files",
                "context": {
                    "files": ["index.js", "utils.js", "helpers.js", "constants.js"],
                    "current_structure": "flat"
                }
            },
            "behavior": {
                "description": "Implement error handling for {operation}",
                "context": {
                    "operation": "database connection",
                    "requirements": ["logging", "retry logic", "graceful degradation"]
                }
            }
        }
        
        # Choose a task type
        task_type = random.choice(rule_types) if rule_types else "general"
        
        if task_type in task_templates:
            template = task_templates[task_type]
            description = template["description"].format(
                action=random.choice(["calculate", "process", "validate", "transform"]),
                data=random.choice(["user statistics", "order totals", "inventory levels"]),
                module=random.choice(["authentication", "payment", "notification"])
            )
            context = template["context"].copy()
        else:
            description = "Implement a generic coding task"
            context = {"requirements": ["clean code", "proper documentation"]}
        
        task = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            type="code_generation",
            language=language,
            description=description,
            context=context,
            expected_rules=rule_types
        )
        
        return task
    
    def generate_ground_truth(self, transcript: Transcript) -> List[Rule]:
        """Generate ground truth rules for a transcript.
        
        Args:
            transcript: Transcript to generate ground truth for
            
        Returns:
            List of ground truth Rule objects
        """
        rules = []
        
        for segment in transcript.segments:
            if segment.type in [RuleType.PERSISTENT, RuleType.SHORT_TERM]:
                # Try to extract a rule from the segment
                rule = self._extract_rule_from_segment(segment)
                if rule:
                    rules.append(rule)
        
        return rules
    
    def _extract_rule_from_segment(self, segment: TranscriptSegment) -> Optional[Rule]:
        """Extract a rule from a segment.
        
        Args:
            segment: Transcript segment
            
        Returns:
            Extracted Rule or None
        """
        content = segment.content.lower()
        
        # Determine rule category
        category = None
        for cat, templates in self.rule_templates.items():
            for template, _ in templates:
                # Simple check - in practice, this would be more sophisticated
                keywords = ["naming", "style", "structure", "behavior", "convention", "organize"]
                if any(keyword in content for keyword in keywords):
                    category = cat
                    break
            if category:
                break
        
        if not category:
            return None
        
        # Create match criteria
        match_type = MatchType.KEYWORD
        if "always" in content or "never" in content:
            match_type = MatchType.PATTERN
        
        # Extract key terms for matching
        match_value = self._extract_match_value(content)
        
        # Create action
        action_type = ActionType.NAMING if category == "naming" else \
                     ActionType.STYLE if category == "style" else \
                     ActionType.STRUCTURE if category == "structure" else \
                     ActionType.BEHAVIOR
        
        # Create rule
        rule = Rule(
            id=f"rule_{uuid.uuid4().hex[:8]}",
            match_criteria=MatchCriteria(
                type=match_type,
                value=match_value
            ),
            action=Action(
                type=action_type,
                description=content
            ),
            rationale=f"Extracted from {segment.speaker} statement",
            confidence=0.9 if segment.type == RuleType.PERSISTENT else 0.7,
            source_id=segment.timestamp.isoformat()
        )
        
        return rule
    
    def _extract_match_value(self, content: str) -> str:
        """Extract a match value from content.
        
        Args:
            content: Content to extract from
            
        Returns:
            Extracted match value
        """
        # Simple extraction - look for key terms
        for term in ["javascript", "python", "typescript", "variables", "functions", "classes"]:
            if term in content:
                return term
        
        # Default to general matching
        return "code"
    
    def generate_dataset(
        self,
        num_transcripts: int = 10,
        num_tasks: int = 20
    ) -> Dict[str, Any]:
        """Generate a complete dataset for testing.
        
        Args:
            num_transcripts: Number of transcripts to generate
            num_tasks: Number of test tasks to generate
            
        Returns:
            Dictionary containing transcripts, ground truth, and tasks
        """
        dataset = {
            "transcripts": [],
            "ground_truth": {},
            "tasks": []
        }
        
        # Generate transcripts with varying rule mixes
        rule_mixes = [
            {"persistent": 0.5, "short_term": 0.2, "irrelevant": 0.3},
            {"persistent": 0.3, "short_term": 0.4, "irrelevant": 0.3},
            {"persistent": 0.2, "short_term": 0.2, "irrelevant": 0.6},
            {"persistent": 0.6, "short_term": 0.1, "irrelevant": 0.3},
        ]
        
        for i in range(num_transcripts):
            rule_mix = rule_mixes[i % len(rule_mixes)]
            transcript = self.generate_transcript(rule_mix)
            ground_truth = self.generate_ground_truth(transcript)
            
            dataset["transcripts"].append(transcript.to_dict())
            dataset["ground_truth"][transcript.id] = [rule.to_dict() for rule in ground_truth]
        
        # Generate test tasks
        rule_type_options = [["naming"], ["style"], ["structure"], ["behavior"], 
                           ["naming", "style"], ["structure", "behavior"]]
        
        for i in range(num_tasks):
            rule_types = rule_type_options[i % len(rule_type_options)]
            task = self.generate_test_task(rule_types)
            dataset["tasks"].append(task.to_dict())
        
        return dataset