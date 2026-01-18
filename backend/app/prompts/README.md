# Prompt Management System

## Overview

This directory contains LLM prompts organized by category and stored in YAML format with Jinja2 templating support. This approach provides:

- **Centralized Management**: All prompts in one location
- **Version Control**: Easy to track changes and collaborate
- **Template Support**: Dynamic content injection via Jinja2
- **Performance**: LRU caching for fast access
- **Maintainability**: Separate concerns (code vs. content)

## Directory Structure

```
app/prompts/
├── README.md                          # This file
├── insight/                           # Psychology & memory analysis prompts
│   ├── psychology_analysis.yaml      # User psychological profiling
│   └── memory_extraction.yaml        # Long-term memory extraction
├── chat/                              # (Future) Chat agent prompts
└── recommendation/                    # (Future) Product recommendation prompts
```

## Usage

### Basic Usage

```python
from app.core.prompt_manager import prompt_manager

# Render a prompt with variables
system_prompt = prompt_manager.render(
    category="insight",
    filename="psychology_analysis",
    key="system_instruction"
)

user_prompt = prompt_manager.render(
    category="insight",
    filename="psychology_analysis",
    key="user_instruction",
    conversation_text="User: Hello\nAI: Hi there!"
)
```

### Get Raw Prompt (No Rendering)

```python
# Get raw template without Jinja2 rendering
raw_prompt = prompt_manager.get_raw(
    category="insight",
    filename="psychology_analysis",
    key="system_instruction"
)
```

### Clear Cache (Development)

```python
# Clear LRU cache to reload files from disk
prompt_manager.clear_cache()
```

## YAML File Format

Each YAML file should contain one or more prompt templates:

```yaml
# Comments are supported
system_instruction: |
  You are a helpful assistant.
  
  Your task is to analyze the following:
  - Point 1
  - Point 2

user_instruction: |
  Please analyze the following conversation:
  
  {{ conversation_text }}
  
  Provide your analysis in JSON format.
```

### Key Conventions

- Use descriptive keys: `system_instruction`, `user_instruction`, `extraction_prompt`
- Use `|` for multi-line strings (preserves newlines)
- Use Jinja2 syntax for variables: `{{ variable_name }}`
- Include comments to explain prompt purpose

## Jinja2 Template Syntax

### Variables

```yaml
prompt: |
  Hello {{ user_name }}, your balance is {{ balance }}.
```

```python
rendered = prompt_manager.render(
    category="example",
    filename="greeting",
    key="prompt",
    user_name="Alice",
    balance=1000
)
# Output: "Hello Alice, your balance is 1000."
```

### Conditionals (Advanced)

```yaml
prompt: |
  {% if is_premium %}
  Welcome, premium user!
  {% else %}
  Welcome, standard user!
  {% endif %}
```

### Loops (Advanced)

```yaml
prompt: |
  Your assets:
  {% for asset in assets %}
  - {{ asset.name }}: ${{ asset.value }}
  {% endfor %}
```

## Migration Guide

### Converting Python f-strings to Jinja2

**Before (Python f-string):**
```python
user_prompt = f"""Please analyze:

{conversation_text}

Provide results."""
```

**After (YAML + Jinja2):**
```yaml
user_instruction: |
  Please analyze:

  {{ conversation_text }}

  Provide results.
```

**Critical:** Replace `{variable}` with `{{ variable }}`

### Migration Checklist

1. ✅ Create YAML file in appropriate category directory
2. ✅ Copy prompt text from Python file
3. ✅ Convert f-string syntax `{var}` to Jinja2 `{{ var }}`
4. ✅ Add descriptive keys for each prompt section
5. ✅ Update Python code to use `prompt_manager.render()`
6. ✅ Test with actual variables
7. ✅ Remove hardcoded prompts from Python files

## Best Practices

### 1. Organize by Category

Group related prompts in subdirectories:
- `insight/` - Psychology analysis, memory extraction
- `chat/` - Conversational AI prompts
- `recommendation/` - Product recommendation prompts

### 2. Use Descriptive Filenames

- ✅ `psychology_analysis.yaml`
- ✅ `memory_extraction.yaml`
- ❌ `prompt1.yaml`
- ❌ `temp.yaml`

### 3. Document Your Prompts

Add comments explaining:
- Purpose of the prompt
- Expected input variables
- Output format
- Usage context

```yaml
# Psychology Analysis Prompts
# Used by InsightService for deep psychological profiling
# Input: conversation_text (string)
# Output: JSON with risk_profile, sentiment, traits

system_instruction: |
  You are a financial psychology expert...
```

### 4. Version Control

- Commit prompt changes with descriptive messages
- Review prompt changes in PRs like code changes
- Tag major prompt versions if needed

### 5. Testing

Always test prompts after changes:

```python
# Test rendering
rendered = prompt_manager.render(
    category="insight",
    filename="psychology_analysis",
    key="user_instruction",
    conversation_text="Test conversation"
)

assert "Test conversation" in rendered
assert "{{ conversation_text }}" not in rendered
```

## Performance

### Caching

The PromptManager uses `@lru_cache(maxsize=100)` to cache loaded YAML files:

- First load: Reads from disk (~1-5ms)
- Subsequent loads: Returns from cache (~0.01ms)
- Cache is shared across all requests
- Cache persists for the lifetime of the process

### Cache Management

```python
# Check cache statistics
cache_info = prompt_manager._load_yaml.cache_info()
print(f"Hits: {cache_info.hits}, Misses: {cache_info.misses}")

# Clear cache (development only)
prompt_manager.clear_cache()
```

## Troubleshooting

### FileNotFoundError

```
FileNotFoundError: Prompt file not found: app/prompts/insight/missing.yaml
```

**Solution:** Check that:
1. File exists in correct directory
2. Filename matches (case-sensitive)
3. File has `.yaml` extension

### KeyError

```
KeyError: Key 'wrong_key' not found in insight/psychology_analysis.yaml
```

**Solution:** Check available keys in YAML file

### Jinja2 Template Error

```
jinja2.exceptions.UndefinedError: 'conversation_text' is undefined
```

**Solution:** Pass all required variables to `render()`:

```python
prompt_manager.render(
    category="insight",
    filename="psychology_analysis",
    key="user_instruction",
    conversation_text="..."  # Don't forget this!
)
```

## Future Enhancements

- [ ] Add prompt versioning support
- [ ] Implement prompt A/B testing framework
- [ ] Add prompt validation (schema checking)
- [ ] Support for multi-language prompts
- [ ] Prompt performance monitoring
- [ ] Hot-reload prompts in development mode

## References

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [LRU Cache in Python](https://docs.python.org/3/library/functools.html#functools.lru_cache)
