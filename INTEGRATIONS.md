# 🔗 AuraCRM — Integrations Guide

> **Domain:** Customer Relationship Management
> **Prefix:** AC

---

## Integration Map

```
AuraCRM
  ├── ERPNext
  ├── CAPS
  ├── frappe_visual
  ├── WhatsApp
  ├── Social Media APIs
```

---

## ERPNext

### Connection Type
- **Direction:** Bidirectional
- **Protocol:** Python API / REST
- **Authentication:** Frappe session / API key

### Data Flow
| Source | Target | Trigger | Data |
|--------|--------|---------|------|
| AuraCRM | ERPNext | On submit | Document data |
| ERPNext | AuraCRM | On change | Updated data |

### Configuration
```python
# In AC Settings or site_config.json
# erpnext_enabled = 1
```

---

## CAPS

### Connection Type
- **Direction:** Bidirectional
- **Protocol:** Python API / REST
- **Authentication:** Frappe session / API key

### Data Flow
| Source | Target | Trigger | Data |
|--------|--------|---------|------|
| AuraCRM | CAPS | On submit | Document data |
| CAPS | AuraCRM | On change | Updated data |

### Configuration
```python
# In AC Settings or site_config.json
# caps_enabled = 1
```

---

## frappe_visual

### Connection Type
- **Direction:** Bidirectional
- **Protocol:** Python API / REST
- **Authentication:** Frappe session / API key

### Data Flow
| Source | Target | Trigger | Data |
|--------|--------|---------|------|
| AuraCRM | frappe_visual | On submit | Document data |
| frappe_visual | AuraCRM | On change | Updated data |

### Configuration
```python
# In AC Settings or site_config.json
# frappe_visual_enabled = 1
```

---

## WhatsApp

### Connection Type
- **Direction:** Bidirectional
- **Protocol:** Python API / REST
- **Authentication:** Frappe session / API key

### Data Flow
| Source | Target | Trigger | Data |
|--------|--------|---------|------|
| AuraCRM | WhatsApp | On submit | Document data |
| WhatsApp | AuraCRM | On change | Updated data |

### Configuration
```python
# In AC Settings or site_config.json
# whatsapp_enabled = 1
```

---

## Social Media APIs

### Connection Type
- **Direction:** Bidirectional
- **Protocol:** Python API / REST
- **Authentication:** Frappe session / API key

### Data Flow
| Source | Target | Trigger | Data |
|--------|--------|---------|------|
| AuraCRM | Social Media APIs | On submit | Document data |
| Social Media APIs | AuraCRM | On change | Updated data |

### Configuration
```python
# In AC Settings or site_config.json
# social_media_apis_enabled = 1
```

---

## API Endpoints

All integration APIs use the standard response format from `auracrm.api.response`:

```python
from auracrm.api.response import success, error

@frappe.whitelist()
def sync_data():
    return success(data={}, message="Sync completed")
```

---

*Part of AuraCRM by Arkan Lab*
