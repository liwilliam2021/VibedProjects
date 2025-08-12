"""Simulated Long-Term Memory storage for rules."""

from typing import Dict, List, Any, Optional, Set, Tuple
import json
from pathlib import Path
from datetime import datetime
import pickle
from collections import defaultdict

from ..common.models import Rule
from ..common.logger import get_logger
from ..utils.file_io import FileIO


class SimulatedLTMStorage:
    """Simulated storage system for long-term memory of rules."""
    
    def __init__(self, storage_path: Optional[str] = None, 
                 index_update_frequency: int = 100,
                 cache_size: int = 1000):
        """Initialize the LTM storage.
        
        Args:
            storage_path: Path to persist storage (optional)
            index_update_frequency: How often to update indices
            cache_size: Maximum number of rules to cache in memory
        """
        self.logger = get_logger("SimulatedLTMStorage")
        self.storage_path = Path(storage_path) if storage_path else None
        self.index_update_frequency = index_update_frequency
        self.cache_size = cache_size
        
        # Primary storage
        self.rules: Dict[str, Rule] = {}
        
        # Indices for efficient retrieval
        self.keyword_index: Dict[str, Set[str]] = defaultdict(set)  # keyword -> rule_ids
        self.type_index: Dict[str, Set[str]] = defaultdict(set)     # action_type -> rule_ids
        self.pattern_index: Dict[str, Set[str]] = defaultdict(set)   # pattern -> rule_ids
        
        # Cache for frequently accessed rules
        self.access_cache: Dict[str, Tuple[Rule, int]] = {}  # rule_id -> (rule, access_count)
        
        # Statistics
        self.stats = {
            "total_stored": 0,
            "total_retrieved": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "index_updates": 0
        }
        
        # Load existing storage if available
        if self.storage_path and self.storage_path.exists():
            self._load_storage()
        
        self.logger.info(f"Initialized LTM storage with {len(self.rules)} existing rules")
    
    def store_rule(self, rule: Rule) -> bool:
        """Store a rule in LTM.
        
        Args:
            rule: Rule to store
            
        Returns:
            True if stored successfully
        """
        try:
            # Store the rule
            self.rules[rule.id] = rule
            
            # Update indices
            self._index_rule(rule)
            
            # Update statistics
            self.stats["total_stored"] += 1
            
            # Check if we need to update indices
            if self.stats["total_stored"] % self.index_update_frequency == 0:
                self._rebuild_indices()
            
            # Persist if configured
            if self.storage_path and self.stats["total_stored"] % 10 == 0:
                self._save_storage()
            
            self.logger.debug(f"Stored rule {rule.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store rule {rule.id}: {e}")
            return False
    
    def store_rules(self, rules: List[Rule]) -> int:
        """Store multiple rules.
        
        Args:
            rules: List of rules to store
            
        Returns:
            Number of rules successfully stored
        """
        stored_count = 0
        
        for rule in rules:
            if self.store_rule(rule):
                stored_count += 1
        
        self.logger.info(f"Stored {stored_count} out of {len(rules)} rules")
        return stored_count
    
    def retrieve_rule(self, rule_id: str) -> Optional[Rule]:
        """Retrieve a specific rule by ID.
        
        Args:
            rule_id: ID of the rule to retrieve
            
        Returns:
            Rule if found, None otherwise
        """
        # Check cache first
        if rule_id in self.access_cache:
            rule, count = self.access_cache[rule_id]
            self.access_cache[rule_id] = (rule, count + 1)
            self.stats["cache_hits"] += 1
            return rule
        
        # Retrieve from main storage
        rule = self.rules.get(rule_id)
        if rule:
            self.stats["cache_misses"] += 1
            self.stats["total_retrieved"] += 1
            
            # Add to cache
            self._add_to_cache(rule_id, rule)
        
        return rule
    
    def retrieve_relevant_rules(self, context: Dict[str, Any]) -> List[Rule]:
        """Retrieve rules relevant to a given context.
        
        Args:
            context: Context dictionary containing:
                     - keywords: List of keywords to match
                     - task_type: Type of task
                     - language: Programming language
                     - description: Task description
                     
        Returns:
            List of relevant rules, sorted by relevance
        """
        self.logger.debug(f"Retrieving rules for context: {list(context.keys())}")
        
        # Collect candidate rule IDs
        candidate_ids: Set[str] = set()
        
        # Search by keywords
        if "keywords" in context:
            for keyword in context["keywords"]:
                keyword_lower = keyword.lower()
                if keyword_lower in self.keyword_index:
                    candidate_ids.update(self.keyword_index[keyword_lower])
        
        # Search by task type
        if "task_type" in context:
            task_type = context["task_type"]
            if task_type in self.type_index:
                candidate_ids.update(self.type_index[task_type])
        
        # Search by language
        if "language" in context:
            language_lower = context["language"].lower()
            if language_lower in self.keyword_index:
                candidate_ids.update(self.keyword_index[language_lower])
        
        # If no candidates found, try broader search
        if not candidate_ids and "description" in context:
            description_words = context["description"].lower().split()
            for word in description_words:
                if len(word) > 3:  # Skip short words
                    if word in self.keyword_index:
                        candidate_ids.update(self.keyword_index[word])
        
        # Retrieve and score rules
        scored_rules = []
        for rule_id in candidate_ids:
            rule = self.retrieve_rule(rule_id)
            if rule:
                score = self._calculate_relevance_score(rule, context)
                scored_rules.append((rule, score))
        
        # Sort by relevance score
        scored_rules.sort(key=lambda x: x[1], reverse=True)
        
        # Return top rules
        max_rules = context.get("max_rules", 10)
        relevant_rules = [rule for rule, score in scored_rules[:max_rules] if score > 0]
        
        self.logger.info(f"Retrieved {len(relevant_rules)} relevant rules from {len(candidate_ids)} candidates")
        return relevant_rules
    
    def _index_rule(self, rule: Rule) -> None:
        """Add a rule to the indices.
        
        Args:
            rule: Rule to index
        """
        rule_id = rule.id
        
        # Index by action type
        self.type_index[rule.action.type.value].add(rule_id)
        
        # Index by keywords in match criteria
        if rule.match_criteria.value:
            words = rule.match_criteria.value.lower().split()
            for word in words:
                if len(word) > 2:  # Skip very short words
                    self.keyword_index[word].add(rule_id)
        
        # Index by keywords in action description
        description_words = rule.action.description.lower().split()
        for word in description_words:
            if len(word) > 3 and word not in ["the", "and", "for", "with"]:
                self.keyword_index[word].add(rule_id)
        
        # Index by pattern if applicable
        if rule.match_criteria.type.value == "pattern":
            pattern_key = f"pattern:{rule.match_criteria.value[:20]}"  # First 20 chars
            self.pattern_index[pattern_key].add(rule_id)
    
    def _rebuild_indices(self) -> None:
        """Rebuild all indices from scratch."""
        self.logger.info("Rebuilding indices")
        
        # Clear existing indices
        self.keyword_index.clear()
        self.type_index.clear()
        self.pattern_index.clear()
        
        # Re-index all rules
        for rule in self.rules.values():
            self._index_rule(rule)
        
        self.stats["index_updates"] += 1
        self.logger.info(f"Rebuilt indices for {len(self.rules)} rules")
    
    def _calculate_relevance_score(self, rule: Rule, context: Dict[str, Any]) -> float:
        """Calculate relevance score for a rule given a context.
        
        Args:
            rule: Rule to score
            context: Context to match against
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        
        # Check keyword matches
        if "keywords" in context:
            rule_text = f"{rule.match_criteria.value} {rule.action.description}".lower()
            keyword_matches = sum(1 for kw in context["keywords"] if kw.lower() in rule_text)
            score += min(0.4 * keyword_matches / len(context["keywords"]), 0.4)
        
        # Check task type match
        if "task_type" in context:
            if context["task_type"] == rule.action.type.value:
                score += 0.3
        
        # Check language match
        if "language" in context and rule.match_criteria.context:
            rule_lang = rule.match_criteria.context.get("language", "").lower()
            if rule_lang == context["language"].lower():
                score += 0.2
        
        # Boost by rule confidence
        score += 0.1 * rule.confidence
        
        return min(score, 1.0)
    
    def _add_to_cache(self, rule_id: str, rule: Rule) -> None:
        """Add a rule to the cache.
        
        Args:
            rule_id: ID of the rule
            rule: Rule object
        """
        # Check cache size
        if len(self.access_cache) >= self.cache_size:
            # Evict least accessed rule
            least_accessed = min(self.access_cache.items(), key=lambda x: x[1][1])
            del self.access_cache[least_accessed[0]]
        
        # Add to cache
        self.access_cache[rule_id] = (rule, 1)
    
    def search_rules(self, query: str, search_type: str = "keyword") -> List[Rule]:
        """Search for rules using various search types.
        
        Args:
            query: Search query
            search_type: Type of search ("keyword", "pattern", "type")
            
        Returns:
            List of matching rules
        """
        matching_ids = set()
        
        if search_type == "keyword":
            query_lower = query.lower()
            if query_lower in self.keyword_index:
                matching_ids = self.keyword_index[query_lower]
        elif search_type == "pattern":
            pattern_key = f"pattern:{query[:20]}"
            if pattern_key in self.pattern_index:
                matching_ids = self.pattern_index[pattern_key]
        elif search_type == "type":
            if query in self.type_index:
                matching_ids = self.type_index[query]
        
        # Retrieve rules
        rules = []
        for rule_id in matching_ids:
            rule = self.retrieve_rule(rule_id)
            if rule:
                rules.append(rule)
        
        return rules
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary of statistics
        """
        cache_hit_rate = self.stats["cache_hits"] / (self.stats["cache_hits"] + self.stats["cache_misses"]) \
                        if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0 else 0.0
        
        return {
            "total_rules": len(self.rules),
            "total_stored": self.stats["total_stored"],
            "total_retrieved": self.stats["total_retrieved"],
            "cache_size": len(self.access_cache),
            "cache_hit_rate": cache_hit_rate,
            "index_updates": self.stats["index_updates"],
            "indices": {
                "keyword_index_size": len(self.keyword_index),
                "type_index_size": len(self.type_index),
                "pattern_index_size": len(self.pattern_index)
            }
        }
    
    def clear(self) -> None:
        """Clear all stored rules and indices."""
        self.rules.clear()
        self.keyword_index.clear()
        self.type_index.clear()
        self.pattern_index.clear()
        self.access_cache.clear()
        
        # Reset statistics
        self.stats = {
            "total_stored": 0,
            "total_retrieved": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "index_updates": 0
        }
        
        self.logger.info("Cleared all storage")
    
    def _save_storage(self) -> None:
        """Save storage to disk."""
        if not self.storage_path:
            return
        
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for saving
            storage_data = {
                "rules": {rid: rule.to_dict() for rid, rule in self.rules.items()},
                "stats": self.stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Save as JSON
            FileIO.write_json(storage_data, self.storage_path)
            
            # Also save indices separately for faster loading
            indices_path = self.storage_path.with_suffix('.indices')
            indices_data = {
                "keyword_index": {k: list(v) for k, v in self.keyword_index.items()},
                "type_index": {k: list(v) for k, v in self.type_index.items()},
                "pattern_index": {k: list(v) for k, v in self.pattern_index.items()}
            }
            FileIO.write_json(indices_data, indices_path)
            
            self.logger.debug(f"Saved storage to {self.storage_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save storage: {e}")
    
    def _load_storage(self) -> None:
        """Load storage from disk."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            # Load main storage
            storage_data = FileIO.read_json(self.storage_path)
            
            # Restore rules
            for rule_id, rule_dict in storage_data.get("rules", {}).items():
                rule = Rule.from_dict(rule_dict)
                self.rules[rule_id] = rule
            
            # Restore stats
            self.stats.update(storage_data.get("stats", {}))
            
            # Load indices if available
            indices_path = self.storage_path.with_suffix('.indices')
            if indices_path.exists():
                indices_data = FileIO.read_json(indices_path)
                
                # Restore indices
                for k, v in indices_data.get("keyword_index", {}).items():
                    self.keyword_index[k] = set(v)
                for k, v in indices_data.get("type_index", {}).items():
                    self.type_index[k] = set(v)
                for k, v in indices_data.get("pattern_index", {}).items():
                    self.pattern_index[k] = set(v)
            else:
                # Rebuild indices if not available
                self._rebuild_indices()
            
            self.logger.info(f"Loaded {len(self.rules)} rules from storage")
            
        except Exception as e:
            self.logger.error(f"Failed to load storage: {e}")
            # Start fresh if loading fails
            self.clear()