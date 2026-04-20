# Security Documentation — Agent CLI

This document outlines the security measures implemented in Agent CLI to protect user data, API credentials, and system integrity.

---

## Overview

Agent CLI handles sensitive data including:
- API keys for various services (Gmail, Twitter, Slack, etc.)
- OAuth credentials and tokens
- User messages and content
- Agent configuration

All security measures are designed to protect this data throughout the application lifecycle.

---

## 1. Encryption at Rest

### API Key Storage

All API keys and sensitive credentials are encrypted using **AES-256-GCM** before storage.

```
┌─────────────────────────────────────────────────────────────┐
│                    Encryption Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Input ──► PBKDF2 Key Derivation ──► AES-256-GCM      │
│  (password)   (100,000 iterations)          (encrypt)      │
│                                                              │
│                    ▼                                         │
│                                                              │
│           Base64 Encode ──► Store in keys.enc              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Details

- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salt**: Unique per-installation salt (stored in code)
- **Algorithm**: AES-256-GCM (authenticated encryption)
- **Storage Location**: `~/.hermes/agent-cli/config/keys.enc`

### Master Password Requirements

- Minimum 8 characters
- Never stored in plain text
- Required on every agent startup

---

## 2. Encryption in Transit

### TLS/SSL Requirements

All network communications must use TLS 1.2+:

| Service | Protocol | Certificate |
|---------|----------|-------------|
| Gmail API | HTTPS (TLS 1.3) | Google-managed |
| Twitter API | HTTPS (TLS 1.2) | Twitter-managed |
| Discord Gateway | WSS (TLS 1.2) | Discord-managed |
| Slack API | HTTPS (TLS 1.3) | Slack-managed |

### Internal Communication

For local inter-process communication:
- Use Unix socket files with restricted permissions (600)
- Avoid exposing sensitive data in environment variables

---

## 3. Sandboxed Execution

### Process Isolation

Each agent runs in an isolated environment:

```
┌─────────────────────────────────────────────────────────────┐
│                      Sandboxed Environment                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│   │  Email Agent │   │ Social Agent │   │Research Agent│  │
│   │   (PID 1234) │   │  (PID 1235)  │   │  (PID 1236)  │  │
│   └──────────────┘   └──────────────┘   └──────────────┘  │
│          │                 │                  │             │
│          └─────────────────┼──────────────────┘            │
│                            │                                │
│                    ┌───────▼───────┐                       │
│                    │  Secure IPC   │                       │
│                    │   Bridge      │                       │
│                    └───────────────┘                       │
│                            │                                │
│                    ┌───────▼───────┐                       │
│                    │ Encrypted     │                       │
│                    │ Key Store     │                       │
│                    └───────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Resource Limits

- **Memory**: 512MB max per agent
- **CPU**: 1 core max per agent  
- **Disk**: 100MB working directory
- **Network**: Limited to configured API endpoints only

### Containerization (Future)

Plan for Docker-based sandboxing:
```yaml
# docker-compose.yml (planned)
services:
  agent:
    build: ./agent
    read_only: true
    tmpfs: /tmp
    mem_limit: 512m
    cpus: 1.0
    network_mode: "none"  # Allowlist instead
```

---

## 4. Audit Logging

### What's Logged (Safe)

All logs must exclude sensitive data:

| Logged | NOT Logged |
|--------|------------|
| ✓ Agent start/stop | ✗ API keys |
| ✓ Message timestamps | ✗ OAuth tokens |
| ✓ Action types | ✗ Message content |
| ✓ Error types | ✗ User credentials |
| ✓ Performance metrics | ✗ File contents |
| ✓ Configuration changes | ✗ Raw API responses |

### Log Format

```
2024-01-15T10:30:00Z [INFO] agent=email-01 action=start status=success
2024-01-15T10:30:05Z [INFO] agent=email-01 action=process_email status=received
2024-01-15T10:30:06Z [INFO] agent=email-01 action=respond status=success
2024-01-15T10:30:10Z [ERROR] agent=email-01 action=api_call error=rate_limit
```

### Log Storage

- Location: `~/.hermes/agent-cli/logs/`
- Rotation: Daily, keep 30 days
- Permissions: 600 (owner read/write only)

---

## 5. No External Dependencies on Secrets

### Principle

The agent should never log, cache, or transmit secrets to external services.

### Rules

1. **Never log API keys** — even in error messages
2. **Never include secrets in environment variables** that might be logged
3. **Never send keys to third-party services** — all API calls go directly to providers
4. **Never store secrets in code** — always prompt or load from encrypted store
5. **Never transmit keys over unencrypted channels**

### Code Example (What NOT to do)

```python
# ❌ NEVER DO THIS
logger.info(f"API call with key {api_key}")  # LEAKS KEY!

# ❌ NEVER DO THIS  
raise ValueError(f"Invalid key: {api_key}")  # LEAKS KEY!

# ✅ DO THIS INSTEAD
logger.info("API call failed")
raise ValueError("Authentication failed - check your API key")
```

---

## 6. Input Validation & Sanitization

### User Input

All user-provided data must be validated:

```python
def sanitize_input(user_input: str) -> str:
    # Remove null bytes
    sanitized = user_input.replace('\x00', '')
    
    # Limit length
    sanitized = sanitized[:10000]
    
    # Remove control characters (except newlines/tabs)
    sanitized = ''.join(
        c for c in sanitized 
        if c in '\n\t' or 32 <= ord(c) < 127
    )
    
    return sanitized
```

### API Responses

Validate all external data:
- Check response types
- Limit data sizes
- Sanitize before processing

---

## 7. Access Control

### File Permissions

All sensitive files must have restricted permissions:

```bash
# Set restrictive permissions
chmod 600 ~/.hermes/agent-cli/config/keys.enc
chmod 700 ~/.hermes/agent-cli/config/
chmod 600 ~/.hermes/agent-cli/config/agents/*.json
```

### Principle of Least Privilege

- Agents run with minimal permissions
- No root/sudo access required
- No access to unintended files

---

## 8. Security Checklist

### Before Deployment

- [ ] Master password set (8+ chars)
- [ ] API keys encrypted
- [ ] File permissions set (600 for keys)
- [ ] No secrets in code
- [ ] Audit logging enabled
- [ ] Network access restricted to known endpoints

### Regular Maintenance

- [ ] Rotate API keys periodically
- [ ] Review audit logs
- [ ] Update dependencies
- [ ] Check for security advisories

---

## 9. Incident Response

### If You Suspect a Compromise

1. **Immediately stop all agents**
   ```bash
   python3 agent-cli.py stop
   ```

2. **Rotate all API keys** — Generate new keys for each service

3. **Change master password** — Run setup wizard again

4. **Review audit logs** — Check for unauthorized actions

5. **Re-deploy** — Clean install with new credentials

---

## 10. Future Security Enhancements

Planned improvements:

| Feature | Status | Description |
|---------|--------|-------------|
| Hardware keys | Planned | Support for YubiKey/Titan |
| MFA | Planned | Multi-factor authentication |
| Docker sandbox | Planned | Container-based isolation |
| Secrets manager | Planned | Integration with Vault |
| SIEM integration | Planned | External security monitoring |

---

## Summary

Agent CLI implements defense in depth with multiple security layers:

1. **AES-256 encryption** for all stored secrets
2. **TLS 1.2+/1.3** for data in transit
3. **Process isolation** to limit blast radius
4. **No sensitive data in logs** (audit trail)
5. **Input validation** to prevent injection
6. **Strict file permissions** to protect data at rest
7. **Incident response plan** for quick recovery

If you have security concerns or discover a vulnerability, please open an issue on GitHub.

---

*Last updated: 2024-01-15*
*Version: 0.1.0*