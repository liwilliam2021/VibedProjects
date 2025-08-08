"""Consistency checker for measuring drift between outputs."""

from typing import Dict, List, Any, Optional, Tuple
import re
from difflib import SequenceMatcher
import json
from collections import Counter

from ..common.logger import get_logger
from ..common.metrics import MetricsCollector


class ConsistencyChecker:
    """Check consistency between outputs to measure drift."""
    
    def __init__(self, similarity_metrics: Optional[List[str]] = None,
                 weights: Optional[Dict[str, float]] = None):
        """Initialize the consistency checker.
        
        Args:
            similarity_metrics: List of metrics to use
            weights: Weights for each metric
        """
        self.logger = get_logger("ConsistencyChecker")
        self.metrics = MetricsCollector("consistency_checking")
        
        self.similarity_metrics = similarity_metrics or [
            "naming_consistency",
            "style_consistency", 
            "structure_consistency"
        ]
        
        self.weights = weights or {
            "naming_consistency": 0.4,
            "style_consistency": 0.3,
            "structure_consistency": 0.3
        }
        
        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
    
    def compare_outputs(self, output1: Dict[str, Any], 
                       output2: Dict[str, Any]) -> Dict[str, float]:
        """Compare two outputs for consistency.
        
        Args:
            output1: First output
            output2: Second output
            
        Returns:
            Dictionary of consistency scores
        """
        self.logger.debug("Comparing outputs for consistency")
        
        scores = {}
        
        # Check each type of consistency
        if "naming_consistency" in self.similarity_metrics:
            scores["naming_consistency"] = self._check_naming_consistency(output1, output2)
        
        if "style_consistency" in self.similarity_metrics:
            scores["style_consistency"] = self._check_style_consistency(output1, output2)
        
        if "structure_consistency" in self.similarity_metrics:
            scores["structure_consistency"] = self._check_structure_consistency(output1, output2)
        
        # Calculate overall consistency
        overall = sum(scores.get(metric, 0) * self.weights.get(metric, 0) 
                     for metric in self.similarity_metrics)
        scores["overall_consistency"] = overall
        
        # Record metrics
        for metric, score in scores.items():
            self.metrics.record(metric, score)
        
        return scores
    
    def _check_naming_consistency(self, output1: Dict[str, Any], 
                                 output2: Dict[str, Any]) -> float:
        """Check naming convention consistency.
        
        Args:
            output1: First output
            output2: Second output
            
        Returns:
            Naming consistency score (0-1)
        """
        # Extract identifiers from both outputs
        identifiers1 = self._extract_identifiers(output1)
        identifiers2 = self._extract_identifiers(output2)
        
        if not identifiers1 and not identifiers2:
            return 1.0
        
        # Check naming patterns
        pattern1 = self._detect_naming_pattern(identifiers1)
        pattern2 = self._detect_naming_pattern(identifiers2)
        
        # Score based on pattern consistency
        if pattern1 == pattern2:
            # Same pattern, check individual names
            common_names = set(identifiers1.keys()) & set(identifiers2.keys())
            if common_names:
                consistent_names = sum(1 for name in common_names 
                                     if identifiers1[name] == identifiers2[name])
                score = consistent_names / len(common_names)
            else:
                score = 1.0 if pattern1 else 0.5
        else:
            # Different patterns
            score = 0.0
        
        self.logger.debug(f"Naming consistency: {score:.2f} (patterns: {pattern1} vs {pattern2})")
        return score
    
    def _check_style_consistency(self, output1: Dict[str, Any], 
                                output2: Dict[str, Any]) -> float:
        """Check code style consistency.
        
        Args:
            output1: First output
            output2: Second output
            
        Returns:
            Style consistency score (0-1)
        """
        style_features1 = self._extract_style_features(output1)
        style_features2 = self._extract_style_features(output2)
        
        if not style_features1 and not style_features2:
            return 1.0
        
        # Compare style features
        consistency_scores = []
        
        # Indentation consistency
        if "indentation" in style_features1 and "indentation" in style_features2:
            if style_features1["indentation"] == style_features2["indentation"]:
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.0)
        
        # Bracket style consistency
        if "bracket_style" in style_features1 and "bracket_style" in style_features2:
            if style_features1["bracket_style"] == style_features2["bracket_style"]:
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.0)
        
        # Line length consistency
        if "avg_line_length" in style_features1 and "avg_line_length" in style_features2:
            diff = abs(style_features1["avg_line_length"] - style_features2["avg_line_length"])
            score = max(0, 1 - diff / 50)  # Penalty for every 50 chars difference
            consistency_scores.append(score)
        
        # Quote style consistency
        if "quote_style" in style_features1 and "quote_style" in style_features2:
            if style_features1["quote_style"] == style_features2["quote_style"]:
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.0)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def _check_structure_consistency(self, output1: Dict[str, Any], 
                                    output2: Dict[str, Any]) -> float:
        """Check structural consistency.
        
        Args:
            output1: First output
            output2: Second output
            
        Returns:
            Structure consistency score (0-1)
        """
        structure1 = self._extract_structure(output1)
        structure2 = self._extract_structure(output2)
        
        if not structure1 and not structure2:
            return 1.0
        
        # Compare structures
        consistency_scores = []
        
        # File organization consistency
        if "files" in structure1 and "files" in structure2:
            files1 = set(structure1["files"])
            files2 = set(structure2["files"])
            
            if files1 or files2:
                overlap = len(files1 & files2)
                total = len(files1 | files2)
                score = overlap / total if total > 0 else 0.0
                consistency_scores.append(score)
        
        # Module structure consistency
        if "modules" in structure1 and "modules" in structure2:
            modules1 = set(structure1["modules"])
            modules2 = set(structure2["modules"])
            
            if modules1 or modules2:
                overlap = len(modules1 & modules2)
                total = len(modules1 | modules2)
                score = overlap / total if total > 0 else 0.0
                consistency_scores.append(score)
        
        # Function/class organization consistency
        if "components" in structure1 and "components" in structure2:
            # Compare component organization
            org_score = self._compare_component_organization(
                structure1["components"],
                structure2["components"]
            )
            consistency_scores.append(org_score)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def _extract_identifiers(self, output: Dict[str, Any]) -> Dict[str, str]:
        """Extract identifiers and their types from output.
        
        Args:
            output: Output to analyze
            
        Returns:
            Dictionary mapping identifier names to types
        """
        identifiers = {}
        
        # Extract from code if present
        if "code" in output:
            code = output["code"]
            
            # Simple regex patterns for common identifiers
            # Variables
            var_pattern = r'(?:let|const|var|def)\s+(\w+)'
            for match in re.finditer(var_pattern, code):
                identifiers[match.group(1)] = "variable"
            
            # Functions
            func_pattern = r'(?:function|def)\s+(\w+)'
            for match in re.finditer(func_pattern, code):
                identifiers[match.group(1)] = "function"
            
            # Classes
            class_pattern = r'class\s+(\w+)'
            for match in re.finditer(class_pattern, code):
                identifiers[match.group(1)] = "class"
        
        # Extract from structured data
        if "identifiers" in output:
            identifiers.update(output["identifiers"])
        
        return identifiers
    
    def _detect_naming_pattern(self, identifiers: Dict[str, str]) -> str:
        """Detect the predominant naming pattern.
        
        Args:
            identifiers: Dictionary of identifiers
            
        Returns:
            Detected pattern name
        """
        if not identifiers:
            return "unknown"
        
        patterns = {
            "camelCase": 0,
            "snake_case": 0,
            "PascalCase": 0,
            "kebab-case": 0
        }
        
        for name in identifiers.keys():
            if re.match(r'^[a-z][a-zA-Z0-9]*$', name) and any(c.isupper() for c in name[1:]):
                patterns["camelCase"] += 1
            elif '_' in name and name.islower():
                patterns["snake_case"] += 1
            elif re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                patterns["PascalCase"] += 1
            elif '-' in name:
                patterns["kebab-case"] += 1
        
        # Return the most common pattern
        if max(patterns.values()) == 0:
            return "mixed"
        
        return max(patterns.items(), key=lambda x: x[1])[0]
    
    def _extract_style_features(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Extract style features from output.
        
        Args:
            output: Output to analyze
            
        Returns:
            Dictionary of style features
        """
        features = {}
        
        if "code" in output:
            code = output["code"]
            lines = code.split('\n')
            
            # Detect indentation
            indents = []
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    if indent > 0:
                        indents.append(indent)
            
            if indents:
                # Most common indent
                indent_counts = Counter(indents)
                common_indent = indent_counts.most_common(1)[0][0]
                if common_indent % 4 == 0:
                    features["indentation"] = "4 spaces"
                elif common_indent % 2 == 0:
                    features["indentation"] = "2 spaces"
                elif '\t' in code:
                    features["indentation"] = "tabs"
            
            # Bracket style
            if '{' in code:
                # Check if opening braces are on same line
                same_line = sum(1 for line in lines if line.rstrip().endswith('{'))
                new_line = sum(1 for line in lines if line.strip() == '{')
                
                if same_line > new_line:
                    features["bracket_style"] = "same_line"
                elif new_line > same_line:
                    features["bracket_style"] = "new_line"
                else:
                    features["bracket_style"] = "mixed"
            
            # Average line length
            if lines:
                lengths = [len(line) for line in lines if line.strip()]
                features["avg_line_length"] = sum(lengths) / len(lengths) if lengths else 0
            
            # Quote style
            single_quotes = code.count("'")
            double_quotes = code.count('"')
            if single_quotes > double_quotes * 2:
                features["quote_style"] = "single"
            elif double_quotes > single_quotes * 2:
                features["quote_style"] = "double"
            else:
                features["quote_style"] = "mixed"
        
        # Extract from style metadata if present
        if "style" in output:
            features.update(output["style"])
        
        return features
    
    def _extract_structure(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structural information from output.
        
        Args:
            output: Output to analyze
            
        Returns:
            Dictionary of structural features
        """
        structure = {}
        
        # Extract file structure
        if "files" in output:
            structure["files"] = output["files"]
        elif "code" in output:
            # Try to infer from imports/includes
            code = output["code"]
            files = []
            
            # Python imports
            import_pattern = r'(?:from|import)\s+(\S+)'
            for match in re.finditer(import_pattern, code):
                module = match.group(1).replace('.', '/')
                files.append(f"{module}.py")
            
            # JavaScript imports
            js_import_pattern = r'(?:import|require)\s*\(?[\'"]([^\'")]+)[\'"]'
            for match in re.finditer(js_import_pattern, code):
                files.append(match.group(1))
            
            if files:
                structure["files"] = list(set(files))
        
        # Extract module structure
        if "modules" in output:
            structure["modules"] = output["modules"]
        
        # Extract component organization
        if "components" in output:
            structure["components"] = output["components"]
        elif "code" in output:
            # Simple component extraction
            components = []
            
            # Functions
            func_pattern = r'(?:function|def)\s+(\w+)'
            components.extend(re.findall(func_pattern, output["code"]))
            
            # Classes
            class_pattern = r'class\s+(\w+)'
            components.extend(re.findall(class_pattern, output["code"]))
            
            if components:
                structure["components"] = components
        
        return structure
    
    def _compare_component_organization(self, components1: List[str], 
                                      components2: List[str]) -> float:
        """Compare organization of components.
        
        Args:
            components1: First component list
            components2: Second component list
            
        Returns:
            Organization similarity score (0-1)
        """
        if not components1 and not components2:
            return 1.0
        
        if not components1 or not components2:
            return 0.0
        
        # Check order similarity using sequence matching
        matcher = SequenceMatcher(None, components1, components2)
        return matcher.ratio()
    
    def calculate_drift(self, outputs_without_rules: List[Dict[str, Any]],
                       outputs_with_rules: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate drift metrics between outputs with and without rules.
        
        Args:
            outputs_without_rules: Outputs generated without rules
            outputs_with_rules: Outputs generated with rules
            
        Returns:
            Dictionary of drift metrics
        """
        # Calculate consistency within each group
        consistency_without = self._calculate_group_consistency(outputs_without_rules)
        consistency_with = self._calculate_group_consistency(outputs_with_rules)
        
        # Calculate drift
        drift_without = 1.0 - consistency_without
        drift_with = 1.0 - consistency_with
        
        # Calculate improvement
        drift_reduction = (drift_without - drift_with) / drift_without * 100 if drift_without > 0 else 0.0
        
        metrics = {
            "consistency_without_rules": consistency_without,
            "consistency_with_rules": consistency_with,
            "drift_without_rules": drift_without,
            "drift_with_rules": drift_with,
            "drift_reduction_percentage": drift_reduction,
            "improvement_factor": consistency_with / consistency_without if consistency_without > 0 else 1.0
        }
        
        # Record metrics
        for metric, value in metrics.items():
            self.metrics.record(metric, value)
        
        self.logger.info(f"Drift analysis complete: {drift_reduction:.1f}% reduction in drift")
        
        return metrics
    
    def _calculate_group_consistency(self, outputs: List[Dict[str, Any]]) -> float:
        """Calculate average consistency within a group of outputs.
        
        Args:
            outputs: List of outputs
            
        Returns:
            Average consistency score (0-1)
        """
        if len(outputs) < 2:
            return 1.0
        
        consistency_scores = []
        
        # Compare all pairs
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                scores = self.compare_outputs(outputs[i], outputs[j])
                consistency_scores.append(scores["overall_consistency"])
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
    
    def generate_consistency_report(self, comparison_results: List[Dict[str, float]]) -> str:
        """Generate a consistency report from comparison results.
        
        Args:
            comparison_results: List of comparison result dictionaries
            
        Returns:
            Report as string
        """
        report_lines = [
            "Consistency Analysis Report",
            "=" * 40,
            ""
        ]
        
        # Aggregate metrics
        metric_totals = {}
        for result in comparison_results:
            for metric, value in result.items():
                if metric not in metric_totals:
                    metric_totals[metric] = []
                metric_totals[metric].append(value)
        
        # Calculate averages
        report_lines.append("Average Consistency Scores:")
        report_lines.append("-" * 30)
        
        for metric, values in metric_totals.items():
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            
            report_lines.append(f"{metric}:")
            report_lines.append(f"  Average: {avg_value:.3f}")
            report_lines.append(f"  Range: [{min_value:.3f}, {max_value:.3f}]")
            report_lines.append("")
        
        return "\n".join(report_lines)