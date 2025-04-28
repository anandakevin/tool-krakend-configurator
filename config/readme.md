## 🧩 Config Composition

This generator supports modular configuration through several base files stored in the config/ directory. These are appended directly into the generated krakend.json under appropriate keys, without additional interpretation.

---

`krakend_extra_config.json`
📍 Target path in final config:

```json
"extra_config": { ... }
```

📄 Example:

```json
{
  "telemetry/logging": {
    "level": "DEBUG",
    "stdout": true,
    "format": "logstash"
  },
  "security/cors": {
    "allow_origins": ["*"],
    "allow_methods": [],
    "allow_headers": [],
    "allow_credentials": true
  }
}
```

📚 Reference: KrakenD extra_config docs

---

`krakend_security_config.json`
📍 Merged into: extra_config.security

📄 Example:

```json
{
  "security/http": {
    "content_security_policy": "default-src 'self';",
    "frame_deny": true
  }
}
```

📚 KrakenD security reference

---

`krakend_opentelemetry_config.json`
📍 Merged into:

```json
"extra_config": {
  "telemetry/opentelemetry": { ... }
}
```

📄 Example:

```json
{
  "telemetry/opentelemetry": {
    "trace_sample_rate": 1,
    "metric_reporting_period": 1
  }
}
```

📚 OpenTelemetry integration

---

`origin_allow_list.json`

📍 Used to populate:

```json
extra_config.security/cors.allow_origins
```

📄 Example:

```json
{
  "allow_origins": [
    "https://app.example.com",
    "https://admin.example.com"
  ]
}
```

> ☝️ This file is env-specific (config/dev/, config/prod/, etc).
>


## 🌐 CORS Configuration Per Environment

CORS origins are managed in:

```
config/{ENV}/origin_allow_list.json
```

### 🧾 Example

```json
{
    "allow_origins": [
        "https://subdomain1.domain.com",
        "https://subdomain2.domain.com"
    ]
}
```

### 💡 Behavior

- Injected into `security/cors.allow_origins`
- `allow_methods` and `allow_headers` inferred from defined endpoints
