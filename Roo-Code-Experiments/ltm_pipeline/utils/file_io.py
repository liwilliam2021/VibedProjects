"""File I/O utilities for the LTM pipeline."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
from datetime import datetime


class FileIO:
    """Utility class for file input/output operations."""
    
    @staticmethod
    def read_json(filepath: Union[str, Path]) -> Dict[str, Any]:
        """Read JSON file and return as dictionary.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Dictionary containing JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def write_json(data: Dict[str, Any], filepath: Union[str, Path], 
                   indent: int = 2, ensure_ascii: bool = False) -> None:
        """Write dictionary to JSON file.
        
        Args:
            data: Dictionary to write
            filepath: Path to output file
            indent: JSON indentation level
            ensure_ascii: Whether to escape non-ASCII characters
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)
    
    @staticmethod
    def read_yaml(filepath: Union[str, Path]) -> Dict[str, Any]:
        """Read YAML file and return as dictionary.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            Dictionary containing YAML data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If file is not valid YAML
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def write_yaml(data: Dict[str, Any], filepath: Union[str, Path]) -> None:
        """Write dictionary to YAML file.
        
        Args:
            data: Dictionary to write
            filepath: Path to output file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    @staticmethod
    def read_jsonl(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
        """Read JSON Lines file and return as list of dictionaries.
        
        Args:
            filepath: Path to JSONL file
            
        Returns:
            List of dictionaries, one per line
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        
        return data
    
    @staticmethod
    def write_jsonl(data: List[Dict[str, Any]], filepath: Union[str, Path]) -> None:
        """Write list of dictionaries to JSON Lines file.
        
        Args:
            data: List of dictionaries to write
            filepath: Path to output file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
    
    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*", 
                   recursive: bool = False) -> List[Path]:
        """List files in directory matching pattern.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern for files
            recursive: Whether to search recursively
            
        Returns:
            List of file paths
        """
        directory = Path(directory)
        if not directory.exists():
            return []
        
        if recursive:
            return list(directory.rglob(pattern))
        else:
            return list(directory.glob(pattern))
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary.
        
        Args:
            directory: Directory path
            
        Returns:
            Path object for the directory
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    @staticmethod
    def create_timestamped_filename(base_name: str, extension: str = "json") -> str:
        """Create filename with timestamp.
        
        Args:
            base_name: Base name for file
            extension: File extension
            
        Returns:
            Filename with timestamp
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{extension}"


class DataLoader:
    """Utility class for loading pipeline data."""
    
    def __init__(self, data_dir: Union[str, Path]):
        """Initialize data loader.
        
        Args:
            data_dir: Base directory for data files
        """
        self.data_dir = Path(data_dir)
    
    def load_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Load a transcript by ID.
        
        Args:
            transcript_id: ID of the transcript
            
        Returns:
            Transcript data as dictionary
        """
        filepath = self.data_dir / "synthetic" / "transcripts" / f"{transcript_id}.json"
        return FileIO.read_json(filepath)
    
    def load_ground_truth(self, transcript_id: str) -> List[Dict[str, Any]]:
        """Load ground truth rules for a transcript.
        
        Args:
            transcript_id: ID of the transcript
            
        Returns:
            List of ground truth rules
        """
        filepath = self.data_dir / "synthetic" / "ground_truth" / f"{transcript_id}_rules.json"
        if filepath.exists():
            return FileIO.read_json(filepath)
        return []
    
    def load_test_tasks(self, task_set: str = "default") -> List[Dict[str, Any]]:
        """Load test tasks.
        
        Args:
            task_set: Name of the task set
            
        Returns:
            List of test tasks
        """
        filepath = self.data_dir / "synthetic" / "test_tasks" / f"{task_set}.json"
        if filepath.exists():
            return FileIO.read_json(filepath)
        return []
    
    def save_results(self, results: Dict[str, Any], module: str, 
                    result_type: str) -> Path:
        """Save results with timestamp.
        
        Args:
            results: Results to save
            module: Module name
            result_type: Type of results
            
        Returns:
            Path to saved file
        """
        filename = FileIO.create_timestamped_filename(f"{module}_{result_type}")
        filepath = self.data_dir / "results" / module / filename
        FileIO.write_json(results, filepath)
        return filepath


class ConfigLoader:
    """Utility class for loading configuration."""
    
    @staticmethod
    def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file (JSON or YAML)
            
        Returns:
            Configuration dictionary
            
        Raises:
            ValueError: If file type is not supported
        """
        config_path = Path(config_path)
        
        if config_path.suffix == '.json':
            return FileIO.read_json(config_path)
        elif config_path.suffix in ['.yaml', '.yml']:
            return FileIO.read_yaml(config_path)
        else:
            raise ValueError(f"Unsupported config file type: {config_path.suffix}")
    
    @staticmethod
    def merge_configs(base_config: Dict[str, Any], 
                     override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries.
        
        Args:
            base_config: Base configuration
            override_config: Configuration to override with
            
        Returns:
            Merged configuration
        """
        import copy
        merged = copy.deepcopy(base_config)
        
        def deep_merge(base: dict, override: dict) -> dict:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        return deep_merge(merged, override_config)