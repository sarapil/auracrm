# Contributing to AuraCRM

Thank you for your interest in contributing to AuraCRM! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/ArkanLab/auracrm/issues) first
2. Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include: Frappe version, AuraCRM version, steps to reproduce, expected vs actual behavior

### Suggesting Features

1. Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
2. Describe the use case and expected behavior
3. Check if it aligns with free or premium tier

### Submitting Code

#### Setup Development Environment

```bash
# Clone and install
bench get-app auracrm https://github.com/ArkanLab/auracrm.git --branch develop
bench --site dev.localhost install-app auracrm

# Install dev dependencies
cd apps/auracrm
pip install ruff

# Enable developer mode
bench --site dev.localhost set-config developer_mode 1
```

#### Development Workflow

1. **Fork** the repository
2. **Branch** from `develop`: `git checkout -b feature/my-feature develop`
3. **Code** your changes following our style guide
4. **Test** your changes: `bench --site dev.localhost run-tests --app auracrm`
5. **Lint**: `ruff check .`
6. **Commit** with clear messages (see below)
7. **Push** and open a Pull Request against `develop`

#### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add custom scoring model for SaaS industry
fix: resolve SLA breach calculation for weekends
docs: update API reference for enrichment endpoints
test: add tests for distribution engine round-robin
refactor: simplify lead scoring cache invalidation
chore: update Ruff to latest version
```

#### Pull Request Guidelines

- Fill in the [PR template](.github/PULL_REQUEST_TEMPLATE.md)
- Keep PRs focused — one feature or fix per PR
- Include tests for new functionality
- Update translations if adding user-facing strings
- Ensure CI passes (linters + tests)

## Code Style

### Python

- **Formatter**: Ruff (configured in pyproject.toml)
- **Line length**: 110 characters
- **Indent**: Tabs
- **Quotes**: Double quotes
- **Type hints**: Not required but welcome
- **Docstrings**: For public methods and classes

```python
# Good
@frappe.whitelist()
def get_lead_score(lead_name):
    """Calculate and return the lead score.
    
    Args:
        lead_name: The name (ID) of the Aura Lead document.
    
    Returns:
        dict: Score value and breakdown.
    """
    lead = frappe.get_doc("Aura Lead", lead_name)
    return calculate_score(lead)
```

### JavaScript

- **Indent**: Tabs
- **Quotes**: Double quotes
- **Namespace**: Use `frappe.auracrm.*` for global functions
- **Translation**: Always use `__("string")` for user-facing text

```javascript
// Good
frappe.auracrm.myFeature = {
    init: function() {
        // Implementation
    },
    refresh: function() {
        frappe.call({
            method: "auracrm.api.my_method",
            callback: function(r) {
                frappe.show_alert(__("Success"));
            }
        });
    }
};
```

### Translations

When adding user-facing strings:

1. Always wrap in `frappe._()` (Python) or `__()` (JavaScript)
2. Add the string to `auracrm/translations/ar.csv` with Arabic translation
3. Add the string to `auracrm/translations/en.csv` (identity mapping)
4. Use placeholders: `_("{0} leads assigned").format(count)`

## Architecture Guide

### Adding a New DocType

1. Create via `bench --site dev.localhost new-doctype "My DocType" --module AuraCRM`
2. Add fields, permissions, and naming in the JSON
3. Create controller in `my_doctype.py`
4. Add tests in `test_my_doctype.py`
5. Register in hooks.py if needed (doc_events, scheduler, etc.)

### Adding a New Engine

See [EXTENSION_GUIDE.md](docs/developer/EXTENSION_GUIDE.md) for the engine pattern.

### Adding an API Endpoint

```python
# In auracrm/api.py or a relevant module
@frappe.whitelist()
def my_new_endpoint(param1, param2=None):
    frappe.has_permission("Aura Lead", "read", throw=True)
    # Implementation
    return result
```

### Feature Gating

For premium features, use the feature flag system:

```python
from auracrm.utils.feature_flags import require_premium, is_feature_enabled

@require_premium("my_feature_key")
def premium_function():
    pass

# Or check manually
if is_feature_enabled("my_feature_key"):
    # premium logic
    pass
```

## Questions?

- Open a [Discussion](https://github.com/ArkanLab/auracrm/discussions) on GitHub
- Email: moatazsarapil@gmail.com
- Community: [Frappe Forum](https://discuss.frappe.io)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
