"""
Prompt Management System
Centralized management of LLM prompts using YAML configuration files and Jinja2 templating
Enhanced with configuration file support for asset types, risk rules, and SP quadrant settings
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Manages LLM prompts stored in YAML files with Jinja2 templating support
    Enhanced with configuration file support for modular prompt system
    
    Features:
    - File-based prompt configuration
    - Jinja2 template rendering for dynamic content
    - LRU caching for performance
    - Organized by category (insight, chat, memory, extraction, etc.)
    - Configuration file support (asset types, risk rules, SP quadrant)
    - Modular prompt architecture
    
    Usage:
        prompt_manager = PromptManager()
        
        # Render a prompt with variables
        system_prompt = prompt_manager.render(
            category="extraction",
            filename="asset_extraction",
            key="system_instruction",
        )
        
        # Load configuration data
        asset_config = prompt_manager.get_config("asset_type_mapping")
        risk_rules = prompt_manager.get_config("risk_assessment_rules")
    """
    
    def __init__(self, base_path: str = "app/prompts"):
        """
        Initialize PromptManager
        
        Args:
            base_path: Base directory for prompt files (relative to backend/)
        """
        self.base_path = Path(base_path)
        self.config_path = self.base_path / "config"
        
        # Ensure base path exists
        if not self.base_path.exists():
            logger.warning(f"Prompt base path does not exist: {self.base_path}")
        
        # Ensure config path exists
        if not self.config_path.exists():
            logger.warning(f"Config path does not exist: {self.config_path}")
    
    @lru_cache(maxsize=100)
    def _load_yaml(self, category: str, filename: str) -> dict[str, Any]:
        """
        Load YAML file from disk with caching
        
        Args:
            category: Subdirectory name (e.g., "insight", "chat", "extraction")
            filename: YAML filename without extension
            
        Returns:
            Parsed YAML content as dictionary
            
        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML is malformed
        """
        file_path = self.base_path / category / f"{filename}.yaml"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {file_path}\n"
                f"Expected location: {file_path.absolute()}"
            )
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                
            if not isinstance(content, dict):
                raise ValueError(f"YAML file must contain a dictionary: {file_path}")
            
            logger.debug(f"Loaded prompt file: {file_path}")
            return content
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading prompt file {file_path}: {e}")
            raise
    
    @lru_cache(maxsize=50)
    def _load_config(self, filename: str) -> dict[str, Any]:
        """
        Load configuration YAML file from config directory with caching
        
        Args:
            filename: Config filename without extension
            
        Returns:
            Parsed YAML content as dictionary
            
        Raises:
            FileNotFoundError: If the config file doesn't exist
            yaml.YAMLError: If the YAML is malformed
        """
        file_path = self.config_path / f"{filename}.yaml"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {file_path}\n"
                f"Expected location: {file_path.absolute()}"
            )
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                
            if not isinstance(content, dict):
                raise ValueError(f"Config file must contain a dictionary: {file_path}")
            
            logger.debug(f"Loaded config file: {file_path}")
            return content
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse config file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config file {file_path}: {e}")
            raise
    
    def render(
        self, 
        category: str, 
        filename: str, 
        key: str, 
        **kwargs: Any
    ) -> str:
        """
        Load a prompt template and render it with Jinja2
        
        Args:
            category: Subdirectory name (e.g., "insight", "chat")
            filename: YAML filename without extension
            key: Key in the YAML file to extract (e.g., "system_instruction")
            **kwargs: Variables to pass to Jinja2 template
            
        Returns:
            Rendered prompt string
            
        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            KeyError: If the key doesn't exist in the YAML file
            
        Example:
            >>> prompt_manager.render(
            ...     category="insight",
            ...     filename="psychology_analysis",
            ...     key="user_instruction",
            ...     conversation_text="User: Hello"
            ... )
            "请分析以下用户对话...\\n\\n【对话历史】\\nUser: Hello\\n\\n请严格按照JSON格式输出分析结果。"
        """
        # Load YAML content (cached)
        yaml_content = self._load_yaml(category, filename)
        
        # Extract the specific prompt string
        if key not in yaml_content:
            raise KeyError(
                f"Key '{key}' not found in {category}/{filename}.yaml\n"
                f"Available keys: {list(yaml_content.keys())}"
            )
        
        template_text = yaml_content[key]
        
        if not isinstance(template_text, str):
            raise ValueError(
                f"Prompt value for key '{key}' must be a string, "
                f"got {type(template_text)}"
            )
        
        # Render with Jinja2
        try:
            template = Template(template_text)
            rendered = template.render(**kwargs)
            
            logger.debug(
                f"Rendered prompt: {category}/{filename}.yaml[{key}] "
                f"with {len(kwargs)} variables"
            )
            
            return rendered
            
        except Exception as e:
            logger.error(
                f"Failed to render template {category}/{filename}.yaml[{key}]: {e}"
            )
            raise
    
    def get_raw(self, category: str, filename: str, key: str) -> str:
        """
        Get raw prompt text without rendering (no Jinja2 processing)
        
        Args:
            category: Subdirectory name
            filename: YAML filename without extension
            key: Key in the YAML file
            
        Returns:
            Raw prompt string
        """
        yaml_content = self._load_yaml(category, filename)
        
        if key not in yaml_content:
            raise KeyError(
                f"Key '{key}' not found in {category}/{filename}.yaml"
            )
        
        return yaml_content[key]
    
    def get_config(self, filename: str) -> dict[str, Any]:
        """
        Get configuration data from config directory
        
        Args:
            filename: Config filename without extension
            
        Returns:
            Configuration dictionary
            
        Example:
            >>> asset_config = prompt_manager.get_config("asset_type_mapping")
            >>> risk_rules = prompt_manager.get_config("risk_assessment_rules")
        """
        return self._load_config(filename)
    
    def get_asset_type_mapping(self) -> dict[str, Any]:
        """Get asset type mapping configuration"""
        return self.get_config("asset_type_mapping")
    
    def get_sp_quadrant_config(self) -> dict[str, Any]:
        """Get Standard & Poor's 4-quadrant configuration"""
        return self.get_config("sp_quadrant_config")
    
    def get_risk_assessment_rules(self) -> dict[str, Any]:
        """Get risk assessment rules configuration"""
        return self.get_config("risk_assessment_rules")
    
    def clear_cache(self) -> None:
        """Clear the LRU cache (useful for development/testing)"""
        self._load_yaml.cache_clear()
        self._load_config.cache_clear()
        logger.info("Prompt and config cache cleared")


# Global singleton instance
prompt_manager = PromptManager()
