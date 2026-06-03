---
name: MediaSync-Claw
version: 1.0.0
description: A media file server that serves multimedia files with FRP support
author: OpenClaw User
type: workspace
language: python
entrypoint: media_server_flask.py
requires:
  bins:
    - python3
    - uv
  python:
    - "flask>=2.0.1"
    - "requests"
    - "jinja2"
triggers:
  - type: keyword
    values: ["playlist", "media list", "show videos", "list files", "media pocket", "my media", "video library", "media gallery"]
    url: "http://local.flask.service:8000/api/openclaw"
    method: "POST"

permissions:
  - filesystem:read
  - filesystem:write
  - network:listen
  - network:connect
  - process:execute
  - network:access:internal
  - network:access:internet
---

# MediaSync-Claw

### 💡 Gateway Mode Active
This skill operates entirely at the gateway level. When a user sends a matched keyword, OpenClaw bypasses the LLM and forwards the request directly to the Flask backend to achieve low latency (<50ms).

*Note: All response text formatting and custom error handling must be managed inside `media_server_flask.py`.*
