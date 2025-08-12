"""Core data models for the LTM pipeline."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class RuleType(Enum):
    """Classification of rule types in transcripts."""
    PERSISTENT = "persistent"
    SHORT_TERM = "short_term"
    IRRELEVANT = "irrelevant"


class MatchType(Enum):
    """Types of matching criteria for rules."""
    PATTERN = "pattern"      # Regex or pattern matching
    KEYWORD = "keyword"      # Keyword-based matching
    CONTEXT = "context"      # Context-aware matching


class ActionType(Enum):
    """Types of actions that rules can specify."""
    STYLE = "style"          # Code style rules
    NAMING = "naming"        # Naming conventions
    STRUCTURE = "structure"  # Code structure rules
    BEHAVIOR = "behavior"    # Behavioral rules


@dataclass
class MatchCriteria:
    """Criteria for when a rule should be applied."""
    type: MatchType
    value: str
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type.value,
            "value": self.value,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchCriteria':
        """Create from dictionary representation."""
        return cls(
            type=MatchType(data["type"]),
            value=data["value"],
            context=data.get("context")
        )


@dataclass
class Action:
    """Action to take when a rule matches."""
    type: ActionType
    description: str
    parameters: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type.value,
            "description": self.description,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create from dictionary representation."""
        return cls(
            type=ActionType(data["type"]),
            description=data["description"],
            parameters=data.get("parameters")
        )


@dataclass
class Rule:
    """A rule extracted from transcripts."""
    id: str = field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    match_criteria: MatchCriteria = None
    action: Action = None
    rationale: str = ""
    confidence: float = 1.0
    source_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "match_criteria": self.match_criteria.to_dict() if self.match_criteria else None,
            "action": self.action.to_dict() if self.action else None,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "source_id": self.source_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            match_criteria=MatchCriteria.from_dict(data["match_criteria"]) if data.get("match_criteria") else None,
            action=Action.from_dict(data["action"]) if data.get("action") else None,
            rationale=data.get("rationale", ""),
            confidence=data.get("confidence", 1.0),
            source_id=data.get("source_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            metadata=data.get("metadata", {})
        )


@dataclass
class TranscriptSegment:
    """A segment of conversation in a transcript."""
    speaker: str  # "user" or "assistant"
    content: str
    type: RuleType = RuleType.IRRELEVANT
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "speaker": self.speaker,
            "content": self.content,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptSegment':
        """Create from dictionary representation."""
        return cls(
            speaker=data["speaker"],
            content=data["content"],
            type=RuleType(data.get("type", "irrelevant")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            metadata=data.get("metadata")
        )


@dataclass
class Transcript:
    """A complete transcript containing multiple segments."""
    id: str = field(default_factory=lambda: f"transcript_{uuid.uuid4().hex[:8]}")
    segments: List[TranscriptSegment] = field(default_factory=list)
    session_id: str = ""
    duration: int = 0  # seconds
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "segments": [seg.to_dict() for seg in self.segments],
            "session_id": self.session_id,
            "duration": self.duration,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transcript':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            segments=[TranscriptSegment.from_dict(seg) for seg in data.get("segments", [])],
            session_id=data.get("session_id", ""),
            duration=data.get("duration", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class Task:
    """A task used for testing rule application."""
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    type: str = ""
    language: str = ""
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    expected_rules: List[str] = field(default_factory=list)  # Expected rule IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type,
            "language": self.language,
            "description": self.description,
            "context": self.context,
            "expected_rules": self.expected_rules
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            type=data.get("type", ""),
            language=data.get("language", ""),
            description=data.get("description", ""),
            context=data.get("context", {}),
            expected_rules=data.get("expected_rules", [])
        )


@dataclass
class StorageDecision:
    """Decision about whether to store a rule."""
    rule_id: str
    decision: str  # "store" or "ignore"
    justification: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "decision": self.decision,
            "justification": self.justification,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ApplicationResult:
    """Result of applying rules to a task."""
    task_id: str
    applied_rules: List[str] = field(default_factory=list)
    modifications: List[Dict[str, Any]] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "task_id": self.task_id,
            "applied_rules": self.applied_rules,
            "modifications": self.modifications,
            "skipped_rules": self.skipped_rules,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }