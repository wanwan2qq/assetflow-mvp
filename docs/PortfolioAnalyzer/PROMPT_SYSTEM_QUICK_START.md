# Prompt Management System - Quick Start Guide

## 🚀 Quick Start (30 seconds)

### Using Existing Prompts

```python
from app.core.prompt_manager import prompt_manager

# Load and render a prompt
system_prompt = prompt_manager.render(
    category="insight",
    filename="psychology_analysis",
    key="system_instruction"
)

user_prompt = prompt_manager.render(
    category="insight",
    filename="psychology_analysis",
    key="user_instruction",
    conversation_text="User: Hello\nAI: Hi!"
)
```

### Creating New Prompts

1. **Create YAML file:** `app/prompts/chat/greeting.yaml`
   ```yaml
   welcome_message: |
     Hello {{ user_name }}!
     Welcome to our service.
   ```

2. **Use in code:**
   ```python
   message = prompt_manager.render(
       category="chat",
       filename="greeting",
       key="welcome_message",
       user_name="Alice"
   )
   ```

## 📁 Directory Structure

```
app/prompts/
├── insight/
│   ├── psychology_analysis.yaml    # User profiling
│   └── memory_extraction.yaml      # Memory extraction
├── chat/                            # (Your prompts here)
└── recommendation/                  # (Your prompts here)
```

## 🔧 Common Tasks

### Task 1: Add a New Prompt

```yaml
# app/prompts/chat/onboarding.yaml
greeting: |
  Welcome {{ user_name }}!
  
  Let's get started with your financial profile.

first_question: |
  What are your main financial goals?
  
  Please choose from:
  {% for goal in goals %}
  - {{ goal }}
  {% endfor %}
```

```python
# In your service
greeting = prompt_manager.render(
    category="chat",
    filename="onboarding",
    key="greeting",
    user_name="Alice"
)
```

### Task 2: Update an Existing Prompt

1. Edit the YAML file: `app/prompts/insight/psychology_analysis.yaml`
2. Save changes
3. Clear cache (development only): `prompt_manager.clear_cache()`
4. Test your changes

### Task 3: Convert f-string to Jinja2

**Before:**
```python
prompt = f"Hello {name}, your balance is {balance}."
```

**After:**
```yaml
# prompts/greeting.yaml
message: |
  Hello {{ name }}, your balance is {{ balance }}.
```

```python
prompt = prompt_manager.render(
    category="greeting",
    filename="greeting",
    key="message",
    name="Alice",
    balance=1000
)
```

## 🧪 Testing

### Run Tests
```bash
cd backend
python -m pytest tests/test_prompt_manager.py -v
```

### Validate System
```bash
cd backend
python scripts/validate_prompt_system.py
```

## 📊 Performance

- **First load:** ~1-5ms (reads from disk)
- **Cached load:** ~0.01ms (100x faster)
- **Cache size:** 100 files (configurable)

## 🐛 Troubleshooting

### Error: FileNotFoundError
```
FileNotFoundError: Prompt file not found: app/prompts/chat/missing.yaml
```
**Fix:** Check file path and name (case-sensitive)

### Error: KeyError
```
KeyError: Key 'wrong_key' not found in chat/greeting.yaml
```
**Fix:** Check available keys in YAML file

### Error: Jinja2 UndefinedError
```
jinja2.exceptions.UndefinedError: 'user_name' is undefined
```
**Fix:** Pass all required variables to `render()`

## 📚 Full Documentation

- **Comprehensive Guide:** `app/prompts/README.md`
- **Implementation Summary:** `PROMPT_REFACTOR_SUMMARY.md`
- **Test Suite:** `tests/test_prompt_manager.py`

## ✅ Validation Checklist

Before deploying:
- [ ] All tests pass: `pytest tests/test_prompt_manager.py`
- [ ] Validation script passes: `python scripts/validate_prompt_system.py`
- [ ] No syntax errors: Check with IDE/linter
- [ ] Prompts render correctly with test data
- [ ] LLM responses are as expected

## 🎯 Best Practices

1. **Organize by category** - Group related prompts
2. **Use descriptive names** - `psychology_analysis.yaml` not `prompt1.yaml`
3. **Document your prompts** - Add comments explaining purpose
4. **Test after changes** - Always validate prompt rendering
5. **Version control** - Commit prompt changes with clear messages

## 🔗 Quick Links

- [Jinja2 Docs](https://jinja.palletsprojects.com/)
- [PyYAML Docs](https://pyyaml.org/)
- [Project README](README.md)

---

**Need help?** Check `app/prompts/README.md` for detailed documentation.
