# Optexity Codebase (Summarized)

This document provides a summary of the source code and documentation for the entire project. Python files display class and function signatures. Documentation files display headers. Configuration and other files display previews to maintain a concise overview.

## File: `LICENSE`

**File Type**: Text/Config/Other
*File size*: 1065 bytes, 21 lines.
```
MIT License

Copyright (c) 2025 Optexity

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
... [content truncated]
```

---

## File: `README.md`

**File Type**: Markdown Documentation
**Headers found**:
*   # Optexity
*   ## Features
*   ## Quick Start
*   ### 1. Create an Account
*   ### 2. Get Your API Key
*   ### 3. Install the Recorder Extension
*   ### Prerequisites
*   ## Create and Activate a Python Environment (Optional)
*   #### Option A – Conda (includes Python 3.11 and Node.js)
*   #### Option B – Python `venv`
*   ## Installation
*   ### Quick Installation (from PyPI)
*   ### Installation from Source
*   ## Set required environment variables:
*   ### Choosing the LLM

---

## File: `SECURITY_ONBOARDING.md`

**File Type**: Markdown Documentation
**Headers found**:
*   # Security Onboarding — `optexity`
*   ## One-time machine setup
*   # Install uv (Python package manager with built-in audit + age-gating)
*   # or:  curl -LsSf https://astral.sh/uv/install.sh | sh
*   # Ensure pre-commit is available (you almost certainly already have it)
*   # Verify
*   ## Per-clone activation
*   ## What runs when
*   ## Install-time protection — package age-gating
*   ## Troubleshooting
*   ## Conventions
*   ## Evidence for compliance auditors

---

## File: `pyproject.toml`

**File Type**: Text/Config/Other
*File size*: 1381 bytes, 69 lines.
```
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "optexity"
version = "0.1.5.134"
readme = "README.md"
description = "Optexity is a platform for building and running browser and computer agents."
authors = [{ name = "Optexity", email = "founders@optexity.com" }]
... [content truncated]
```

---

## File: `pyrightconfig.json`

**File Type**: JSON Configuration
```json
{
    "venvPath": ".",
    "extraPaths": ["../browser-use"]
}
... [content truncated]
```

---

## File: `requirements.txt`

**File Type**: Text/Config/Other
*File size*: 273 bytes, 20 lines.
```
# core
"pydantic>=2",
"pydantic-settings",

# optexity forked dependency
"optexity-browser-use>=0.9.5",

# web / infra
"fastapi",
"httpx",
... [content truncated]
```

---

## File: `docker/Dockerfile`

**File Type**: Text/Config/Other
*File size*: 3660 bytes, 94 lines.
```
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# Software rendering for WebGL on GPU-less EC2 instances
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV GALLIUM_DRIVER=llvmpipe
ENV MESA_GL_VERSION_OVERRIDE=4.5
ENV MESA_GLSL_VERSION_OVERRIDE=450
... [content truncated]
```

---

## File: `docker/build.sh`

**File Type**: Text/Config/Other
*File size*: 7023 bytes, 271 lines.
```
#!/usr/bin/env bash
#
# Optexity Docker image build (use this `docker/` directory for all future container builds).
#
# VNC / browser-view work: latest flow lives on the `vnc` branch in optexity; build artifacts still
# ship from here (`docker/Dockerfile`, this script, supervisord, etc.).
#
# --- build.sh usage ---
#
#   ./build.sh --dev -t vnc --local
... [content truncated]
```

---

## File: `docker/install.sh`

**File Type**: Text/Config/Other
*File size*: 199 bytes, 6 lines.
```
#!/usr/bin/env bash
set -x

brew install colima docker docker-buildx gh
mkdir -p ~/.docker/cli-plugins
ln -sfn $(brew --prefix)/opt/docker-buildx/bin/docker-buildx ~/.docker/cli-plugins/docker-buildx
... [content truncated]
```

---

## File: `docker/openbox-rc.xml`

**File Type**: Text/Config/Other
*File size*: 827 bytes, 32 lines.
```
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <resistance>
    <strength>100</strength>
    <screen_edge_strength>100</screen_edge_strength>
  </resistance>
  <keyboard/>
  <mouse>
    <context name="Root"/>
    <context name="Client">
... [content truncated]
```

---

## File: `docker/supervisord.conf`

**File Type**: Text/Config/Other
*File size*: 1290 bytes, 50 lines.
```
[supervisord]
nodaemon=true
logfile=/tmp/supervisord.log
user=optexity

[program:xvfb]
command=Xvfb :99 -screen 0 1920x1080x24 -ac
autorestart=true
priority=10
user=optexity
... [content truncated]
```

---

## File: `docs/AGENTS.md`

**File Type**: Markdown Documentation
**Headers found**:
*   # Documentation Writing Standards
*   ## Core Principles
*   ## Page Structure
*   ### Title and Description
*   ### Section Organization
*   ## Overview
*   ## Properties
*   ### Property Details
*   ## Examples
*   ## Tables
*   ### Use Tables For
*   ### Property Table Format
*   ### Comparison Table Format
*   ## Code Examples
*   ### Lead with Minimal Examples

---

## File: `docs/package.json`

**File Type**: JSON Configuration
```json
{
    "name": "optexity-docs",
    "private": true,
    "scripts": {
        "dev": "mintlify dev"
    },
    "dependencies": {
        "@mintlify/cli": "^4.0.1128"
    }
}
... [content truncated]
```

---

## File: `docs/examples/example_workflows/if-else-and-email-2fa.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Minimal example
*   ## Full automation
*   ## What this workflow demonstrates
*   ## What the final state extraction returns
*   ## When to use this

---

## File: `docs/examples/example_workflows/pointclickcare-detailed-census-report.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Minimal example
*   ## Full automation
*   ## What this workflow demonstrates
*   ## When to use this

---

## File: `docs/examples/healthcare/peachstate-medicaid.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ### Part 1: Record the base workflow
*   ### Part 2: Refine the automation
*   #### 2.1. ForLoopNode to iterate over multiple links to extract data
*   ### Part 3: Run the `peachstate_medicaid_insurance` automation via inference
*   #### 3.1. Start the inference server
*   #### 3.2. Invoke the `peachstate_medicaid_insurance` endpoint
*   ### Final Automation

---

## File: `docs/examples/data_extraction/i94.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   # Quickstart using built-in automation
*   ## Add automation to the dashboard
*   # Run the `i94` automation via inference
*   ## Start the inference server
*   ## Invoke the `i94` endpoint
*   ## Viewing the task run
*   # I94 Travel History
*   ## Add automation to the dashboard
*   ## Invoke the `get_i94_travel_history` endpoint
*   # Build the automation from scratch
*   ## Record the base workflow
*   ## Refine the automation
*   ### Clarify the nationality selection
*   ### Add a network‑call extraction action
*   ### Scroll the popup via Python script

---

## File: `docs/examples/qa_testing/supabase-login.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ### Part 1: Record the base workflow
*   ### Part 2: Refine the automation
*   #### 2.1. Add a assertion action to verify the login was successful
*   ### Part 3: Run the `supabase_login` automation via inference
*   #### 3.1. Start the inference server
*   #### 3.2. Invoke the `supabase_login` endpoint
*   ### Final Automation

---

## File: `docs/examples/fetching_cookies/fetching-cookies-and-local-session-storage.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Minimal example
*   ## Full automation (from `login_cookies.json`)
*   ## What you get back
*   ## When to use this

---

## File: `docs/docs/extra.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ### Variable Flow Example
*   ## Execution Model
*   ## Next Steps

---

## File: `docs/docs/getting_started/marketplace.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Install from the Marketplace
*   ## Run it with curl

---

## File: `docs/docs/getting_started/recording-first-inference.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Prerequisites
*   ### Create an account
*   ### Get your API key
*   ### Install the Recorder Extension
*   ## Record the Automation
*   ## Understand the Automation Structure
*   ## Extracting the Stock Price
*   ## Video Tutorial
*   ## Next Steps

---

## File: `docs/docs/getting_started/running-first-inference.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Start the inference child process server
*   ## Call the `/inference` endpoint
*   ### Request schema
*   ### Example `curl` request
*   ## Monitor health and execution
*   ## Video Tutorial

---

## File: `docs/docs/building-automations/action-node.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Structure
*   ## Action Types
*   ## Timing Properties
*   ### Default Timing by Action Type
*   ## Examples
*   ### Basic Click
*   ### With Custom Timing
*   ### Sleep-Only Node
*   ### Fail State Node
*   ### Opens New Tab

---

## File: `docs/docs/building-automations/automation-structure.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Complete Example
*   ## Properties
*   ## Parameters
*   ## Node Types
*   ## Browser Channel
*   ## Expected Downloads
*   ## OS Emulation
*   ## Max Retries
*   ## Reuse Page If Already On URL

---

## File: `docs/docs/building-automations/for-loop-node.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Structure
*   ### Variable loop
*   ### Locator loop
*   ## Properties
*   ## The Index Variable
*   ### Variable loops
*   ### Locator loops
*   ### Using Multiple Variables in a Loop
*   ## Waiting for Matches
*   ## Storing One Value Per Iteration
*   ## Nested Loops
*   ## Data Sources
*   ## Reset Nodes
*   ### Reset Strategy Recommendations
*   ## Error Handling

---

## File: `docs/docs/building-automations/if-else-node.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Structure
*   ## Properties
*   ## Using Extraction Nodes to Set Conditions
*   ### How It Works
*   ### Variable Naming and Syntax
*   ## Condition Syntax
*   ### Operators
*   ## Examples
*   ### Extract and Check Page State
*   ### Handle Optional 2FA
*   ### Branch Based on Extracted Value
*   ### Nested Conditions

---

## File: `docs/docs/building-automations/local-setup.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ### 1. Create an Account
*   ### 2. Get Your API Key
*   ### 3. Install the Recorder Extension
*   ### Prerequisites
*   ## Create and Activate a Python Environment (Optional)
*   #### Option A – Conda (includes Python 3.11 and Node.js)
*   #### Option B – Python `venv`
*   ## Installation
*   ### Quick Installation (from PyPI)
*   ### Installation from Source
*   ## Set required environment variables:
*   ### Using a Different LLM

---

## File: `docs/docs/building-automations/parameters.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Parameter Types
*   ## Defining Parameters
*   ## Accessing Parameters
*   ### Where Substitution Works
*   ## Input Parameters
*   ## Generated Parameters
*   ## Secure Parameters
*   ### 1Password Integration
*   ### TOTP Codes
*   ## Loop Index Variable
*   ## Complete Example
*   ## Best Practices

---

## File: `docs/docs/building-automations/quickstart.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Prerequisites
*   ### Install the Recorder Extension
*   ## What We're Building
*   ## Step 1: Record the Automation
*   ## Step 2: Understand the Automation Structure
*   ### The Complete Automation
*   ### Breaking Down Each Component
*   ## Step 3: Edit and Customize
*   ### Parameterizing Values
*   # Before: Hardcoded email
*   # After: Parameterized
*   ### Adding Descriptive Instructions
*   # Basic (less reliable)
*   # Descriptive (more reliable)
*   ### Adjusting Timing

---

## File: `docs/docs/advanced/aws-secrets-manager.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Setup
*   ### Create a Secret in AWS
*   ### Create IAM Credentials
*   ### Configure Environment
*   ## Usage
*   ## Properties
*   ## TOTP from AWS Secrets Manager
*   ## Revoking Access

---

## File: `docs/docs/advanced/best-practices.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Design Principles
*   ## Locator Strategy
*   ### Priority Order
*   ### Always Provide Fallback
*   ### Avoid Dynamic IDs
*   ## Naming Conventions
*   ## Timing Guidelines
*   ## Error Handling
*   ### Optional Elements
*   ### Skip Optional Steps
*   ## Security
*   ## Performance
*   ## Debugging
*   ### Common Issues
*   ### Debug with Screenshots

---

## File: `docs/docs/advanced/callbacks.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Local Development
*   ## Production
*   ## Callback Payload
*   ## Authentication

---

## File: `docs/docs/advanced/downloads-files.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Download Methods
*   ## Click to Download
*   ## Download Metadata
*   ## Save a File from a Python Script
*   ## Select to Download
*   ## Save Page as PDF
*   ## Multiple Downloads
*   ## Upload Files
*   ## Download Storage
*   ## Waiting for Downloads
*   ## Failure on Missing Download
*   ## Best Practices

---

## File: `docs/docs/advanced/locators.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Locator Methods
*   ## Playwright Commands
*   ### Role-Based (Recommended)
*   ### Label-Based
*   ### Text-Based
*   ### Test ID
*   ### CSS Selector
*   ### Chaining
*   ### Iframes
*   ## XPath Locators
*   ### Common Patterns
*   ## Prompt Instructions
*   ### Writing Good Instructions
*   ## Locator Selection Strategy
*   ## Dynamic Elements

---

## File: `docs/docs/advanced/model-configuration.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Environment Variables
*   ## Model Strings
*   ## Resolution Order
*   ### Task-Level Override
*   ### Action-Level Override
*   ## Fallbacks
*   ## Cost Tracking
*   ## Migrating from `llm_provider`

---

## File: `docs/docs/advanced/onepassword.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Setup
*   ### Create an Item in 1Password
*   ### Get Service Account Token
*   ### Configure Environment
*   ## Usage
*   ## Properties
*   ## TOTP from 1Password
*   ## Revoking Access

---

## File: `docs/docs/advanced/orchestration.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Architecture
*   ## Minimal Example
*   ## Dependencies
*   ## Running
*   ## How It Works
*   ### Flow
*   ## Benefits

---

## File: `docs/docs/advanced/proxy-setup.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Local Development
*   ## Production
*   ## Enabling Proxy in Inference
*   ## Proxy Providers
*   ### Webshare

---

## File: `docs/docs/advanced/timing-retries.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Timing Controls
*   ## Sleep Times
*   ### before_sleep_time
*   ### end_sleep_time
*   ### Default Values
*   ## Automation-Level Retries
*   ## Element-Level Retry Configuration
*   ### How Retries Work
*   ## Handling New Tabs
*   ### expect_new_tab
*   ## Common Patterns
*   ### Slow-Loading Pages
*   ### Dynamic AJAX Content
*   ### Optional Elements
*   ## Troubleshooting

---

## File: `docs/docs/advanced/totp-integration.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Get Your TOTP Secret
*   ## Direct TOTP Secret
*   ## TOTP via 1Password (Recommended)
*   ## Using in Automations
*   ## Complete Example

---

## File: `docs/docs/advanced/two-fa-integration.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Methods
*   ## Setup
*   ### Twilio SMS
*   ## Email 2FA
*   ### Properties
*   ## Slack 2FA
*   ### Properties
*   ## SMS 2FA
*   ### Properties
*   ## Common Properties
*   ## Using the Code

---

## File: `docs/docs/faqs/AGENTS.md`

**File Type**: Markdown Documentation
**Headers found**:
*   ### Accordions

---

## File: `docs/docs/faqs/faqs.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## General
*   ## Parameters & Credentials
*   ## Control Flow
*   ## Two-Factor Authentication
*   ## Data & Downloads
*   ## Form Interactions
*   ## Pricing & Access
*   ## Troubleshooting

---

## File: `docs/docs/action-types/agentic-tasks.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## When to Use
*   ## AgenticTask
*   ### Properties
*   ### max_steps Guidelines
*   ### Writing Good Task Descriptions
*   ### Vision Mode
*   ## CloseOverlayPopup
*   ### Default Behavior
*   ### What It Handles
*   ## Variables in Agentic Tasks
*   ## Combining with Static Actions
*   ## Best Practices

---

## File: `docs/docs/action-types/assertion-action.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Structure
*   ## Properties
*   ## Assertions
*   ## Examples
*   ### Dismiss an element only when it appears
*   ### Wait for a spinner to disappear, then branch
*   ### Variable substitution in the locator
*   ## assert_locator_node vs if_else_node
*   ## Locator Syntax

---

## File: `docs/docs/action-types/count-locator-action.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Properties
*   ## JSON Example
*   ## Waiting for Matches
*   ## Count Locator vs Locator For-Loop

---

## File: `docs/docs/action-types/extraction-action.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Extraction Types
*   ## Common Properties
*   ### `allow_none`
*   ## LLM Extraction
*   ### Properties
*   ### Source Selection
*   ### Extraction Format
*   ### Storing as Variables
*   ### Writing Good Instructions
*   ## Locator Extraction
*   ### Properties
*   ### Fallback Behavior
*   ### When to Use Locator vs LLM
*   ## Network Call Extraction
*   ### Properties

---

## File: `docs/docs/action-types/human-in-loop.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Properties
*   ## JSON Example
*   ## The HITL Flow
*   ## Complete Automation Example
*   ## Timeout Behavior
*   ## Best Practices
*   ### Place HITL nodes at natural breakpoints
*   ### Keep `max_wait_time` realistic
*   ### Only one HITL pause per task at a time
*   ## Next Steps

---

## File: `docs/docs/action-types/interaction-action.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Available Actions
*   ## Common Properties
*   ## Click Element
*   ### Click Properties
*   ### Examples
*   ## Input Text
*   ### Input Properties
*   ### Fill vs Type
*   ## Select Option
*   ### Select Properties
*   ## Check (Checkbox/Radio)
*   ## Navigation Actions
*   ### Go to URL
*   ### Go Back
*   ### Close Tabs Until

---

## File: `docs/docs/action-types/llm-query-action.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Properties
*   ## JSON Example
*   ## Output Format
*   ## Using Variables in Prompts
*   ## Storing Output as Variables
*   ## Choosing a Model
*   ## LLM Query vs LLM Extraction

---

## File: `docs/docs/action-types/python-script-action.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Properties
*   ## Script Contract
*   ## JSON Example
*   ## Common Patterns
*   ### Scroll to the bottom of the page
*   ### Wait for a custom JavaScript condition
*   ### Dispatch a custom browser event
*   ### Interact with a shadow DOM element
*   ## Python Script Extraction
*   ### Properties
*   ### Script Contract
*   ## The Script Context (`ctx`)
*   ### `ctx.save_download()` — emit a file as a task download
*   ### `ctx.state` — share data between script nodes

---

## File: `docs/docs/action-types/sleep-action.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Properties
*   ## JSON Example
*   ## When to Use `sleep_action` vs `end_sleep_time`

---

## File: `docs/docs/action-types/two-factor-auth.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## The 2FA Flow
*   ## Starting the 2FA Timer
*   ## Email 2FA
*   ### Properties
*   ### How It Works
*   ## TOTP 2FA
*   ### Properties
*   ### Getting the TOTP Secret
*   ## API 2FA
*   ### Properties
*   ## Tuning the Fetch Window
*   ### Properties
*   ## Using the 2FA Code
*   ## Complete Example: Login with Email 2FA

---

## File: `docs/docs/inference/dedicated-instances.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Quick start
*   ## Request fields
*   ## How it works
*   ## Examples
*   ### One login, a burst of tasks
*   ### Multiple unique logins, isolated
*   ### More logins than capacity
*   ## Controlling the queue
*   ## Task priority
*   ## Things to take special care of
*   ## FAQ

---

## File: `docs/docs/inference/inference-api.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## Overview
*   ## Configuration
*   ## Models
*   ### `InferenceRequest`
*   ### `Task`
*   ## HTTP endpoints (child process server)

---

## File: `docs/api-reference/callback.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ### Callback Response

---

## File: `docs/api-reference/inference-endpoint.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## POST /inference
*   ## Description
*   ## Authentication
*   ## Parameters
*   ### Headers
*   ### Body Parameters
*   ## Code Examples
*   ### Example with Secure Parameters
*   ## Response
*   ### Success Response (202 Accepted)
*   ## Error Responses
*   ### 400 Bad Request
*   ### 404 Not Found
*   ### 401 Unauthorized
*   ### 500 Internal Server Error

---

## File: `docs/api-reference/stream-endpoint.mdx`

**File Type**: Markdown Documentation
**Headers found**:
*   ## GET /api/v1/tasks/{task_id}/stream
*   ## Description
*   ## Authentication
*   ## Parameters
*   ### Path Parameters
*   ### Headers
*   ## Code Examples
*   ### Fetch the stream URL
*   ## Success Response (200 OK)
*   ## Error Responses
*   ### 401 Unauthorized
*   ### 404 Not Found
*   ### 409 Conflict
*   ## Frontend Integration
*   ### Reference implementations

---

## File: `optexity/__init__.py`

**File Type**: Python Source

---

## File: `optexity/cli.py`

**File Type**: Python Source

*   **Function**: `def install_browsers(...)`
    *   *Docstring*: Install Playwright + Patchright browsers.

*   **Function**: `def run_inference(...)`

*   **Function**: `def main(...)`

---

## File: `optexity/exceptions.py`

**File Type**: Python Source

*   **Class**: `AssertLocatorPresenceException`
    *   **Method**: `def __init__(...)`

*   **Class**: `ElementNotFoundInAxtreeException`
    *   **Method**: `def __init__(...)`

*   **Class**: `AxtreeIndexActionFailedException`
    *   **Method**: `def __init__(...)`

*   **Class**: `HumanInLoopTimeoutException`
    *   **Method**: `def __init__(...)`

*   **Class**: `ExpectedDownloadFailedException`
    *   *Docstring*: Raised when a node has expect_download=True but the action did not
    *   **Method**: `def __init__(...)`

---

## File: `optexity/onepassword_integration.py`

**File Type**: Python Source

---

## File: `optexity/private_nodes.py`

**File Type**: Python Source
**Module Docstring**:
```
Extension point for node handlers that live outside this package.

The public SDK owns the ``private_node`` schema and this registry; closed-source
distributions ship a separate package that registers handlers against it at
import time, advertised through the ``optexity.plugins`` entry-point group.
Nothing here imports a plugin by name, so the public SDK builds and runs with no
plugin installed — a ``private_node`` naming an absent handler then fails at that
node with ``HandlerNotRegistered`` while the rest of the automation proceeds.
```

*   **Class**: `HandlerNotRegistered`
    *   **Method**: `def __init__(...)`

*   **Class**: `HandlerSpec`
    *   *Docstring*: One callable addressable from a ``private_node``.

*   **Class**: `HandlerRegistry`
    *   **Method**: `def register(...)`
    *   **Method**: `def get(...)`
    *   **Method**: `def names(...)`

*   **Function**: `def load_plugins(...)`
    *   *Docstring*: Import and register every installed plugin package. Idempotent.

---

## File: `optexity/test.py`

**File Type**: Python Source

---

## File: `optexity/schema/__init__.py`

**File Type**: Python Source

---

## File: `optexity/schema/automation.py`

**File Type**: Python Source

*   **Class**: `OnePasswordParameter`
    *   **Method**: `def validate_onepassword_parameter(...)`

*   **Class**: `AmazonSecretsManagerParameter`
    *   **Method**: `def validate_amazon_secrets_manager_parameter(...)`

*   **Class**: `TOTPParameter`

*   **Class**: `RDPParameter`

*   **Class**: `SecureParameter`
    *   **Method**: `def validate_secure_parameter(...)`

*   **Class**: `VariableSubstitution`
    *   *Docstring*: ``{name[i]}`` substitution shared by node types that accept variables.
    *   **Method**: `def replace(...)`

*   **Class**: `ActionNode`
    *   **Method**: `def validate_one_node(...)`
    *   **Method**: `def replace(...)`

*   **Function**: `def _replace_in_value(...)`

*   **Class**: `PrivateNode`
    *   *Docstring*: Calls a handler contributed by an installed plugin package.
    *   **Method**: `def replace(...)`

*   **Class**: `ForLoopNode`
    *   **Method**: `def validate_loop_source_and_index(...)`
    *   **Method**: `def replace(...)`
    *   **Method**: `def migrate_old_nodes(...)`

*   **Class**: `IfElseNode`
    *   **Method**: `def replace(...)`
    *   **Method**: `def migrate_old_nodes(...)`

*   **Class**: `AssertLocatorNode`
    *   *Docstring*: Evaluate a Playwright locator assertion and store the boolean result.
    *   **Method**: `def replace(...)`

*   **Class**: `Parameters`
    *   **Method**: `def validate_parameters(...)`

*   **Class**: `Automation`
    *   **Method**: `def migrate_old_nodes(...)`
    *   **Method**: `def validate_rdp_parameter(...)`
    *   **Method**: `def validate_parameters_with_examples(...)`
    *   **Method**: `def assign_default_output_variable_names(...)`
    *   **Method**: `def model_dump(...)`
    *   **Method**: `def _sort_parameters_by_node_order(...)`

---

## File: `optexity/schema/callback.py`

**File Type**: Python Source

*   **Class**: `CallbackResponse`

---

## File: `optexity/schema/enums.py`

**File Type**: Python Source

*   **Class**: `ExitCodes`

---

## File: `optexity/schema/inference.py`

**File Type**: Python Source

*   **Class**: `InferenceRequest`
    *   **Method**: `def validate_use_proxy(...)`
    *   **Method**: `def validate_unique_parameter_names(...)`

*   **Class**: `FetchEmailMessagesRequest`
    *   **Method**: `def validate_time_parameters(...)`

*   **Class**: `FetchSlackMessagesRequest`
    *   **Method**: `def validate_time_parameters(...)`

*   **Class**: `FetchSMSMessagesRequest`
    *   **Method**: `def validate_time_parameters(...)`

*   **Class**: `Message`
    *   **Method**: `def validate_timestamp(...)`

*   **Class**: `FetchMessagesResponse`

---

## File: `optexity/schema/memory.py`

**File Type**: Python Source

*   **Class**: `NetworkRequest`

*   **Class**: `NetworkError`

*   **Class**: `NetworkResponse`

*   **Class**: `AutomationState`
    *   **Method**: `def validate_start_2fa_time(...)`

*   **Class**: `SystemInfo`
    *   **Method**: `def get_effective_memory_mb(...)`

*   **Class**: `BrowserState`

*   **Class**: `ScreenshotData`

*   **Class**: `OutputData`

*   **Class**: `ForLoopStatus`

*   **Class**: `Variables`

*   **Class**: `Memory`
    *   **Method**: `def update_system_info(...)`

---

## File: `optexity/schema/ocr.py`

**File Type**: Python Source

*   **Class**: `BoundingBox`

*   **Class**: `OCRResult`

---

## File: `optexity/schema/task.py`

**File Type**: Python Source

*   **Function**: `def uuid_str_to_base62(...)`

*   **Function**: `def _is_private_ip(...)`
    *   *Docstring*: Check if a hostname is a private/internal IP address.

*   **Function**: `def validate_callback_url_ssrf(...)`
    *   *Docstring*: Validate that a callback URL does not target private/internal networks.

*   **Class**: `CallbackUrl`
    *   **Method**: `def validate_callback_url(...)`

*   **Class**: `Task`
    *   **Method**: `def task_directory(...)`
    *   **Method**: `def logs_directory(...)`
    *   **Method**: `def downloads_directory(...)`
    *   **Method**: `def log_file_path(...)`
    *   **Method**: `def priority_order_key(...)`
    *   **Method**: `def validate_unique_parameters(...)`
    *   **Method**: `def validate_rdp_channel(...)`
    *   **Method**: `def set_dependent_paths(...)`
    *   **Method**: `def proxy_session_id(...)`

*   **Class**: `TaskCreateRequest`
    *   **Method**: `def must_have_timezone(...)`

*   **Class**: `TaskStartedRequest`
    *   **Method**: `def must_have_timezone(...)`

*   **Class**: `TaskCompleteRequest`
    *   **Method**: `def must_have_timezone(...)`

*   **Class**: `TaskOutputDataRequest`
    *   **Method**: `def must_have_valid_final_screenshot(...)`
    *   **Method**: `def is_valid_base64_image(...)`

*   **Class**: `RequestDownloadUploadUrlsRequest`

*   **Class**: `ConfirmDownloadsRequest`

---

## File: `optexity/schema/token_usage.py`

**File Type**: Python Source

*   **Class**: `TokenUsage`
    *   **Method**: `def __add__(...)`
    *   **Method**: `def __sub__(...)`

---

## File: `optexity/schema/types.py`

**File Type**: Python Source

---

## File: `optexity/schema/actions/__init__.py`

**File Type**: Python Source

---

## File: `optexity/schema/actions/assertion_action.py`

**File Type**: Python Source

*   **Class**: `LLMAssertion`
    *   **Method**: `def validate_output_var_in_format(...)`

*   **Class**: `NetworkCallAssertion`

*   **Class**: `PythonScriptAssertion`
    *   **Method**: `def validate_script(...)`

*   **Class**: `AssertionAction`
    *   **Method**: `def validate_one_assertion(...)`
    *   **Method**: `def replace(...)`

---

## File: `optexity/schema/actions/captcha_action.py`

**File Type**: Python Source

*   **Class**: `CaptchaAction`
    *   **Method**: `def merge_config_with_defaults(...)`
    *   **Method**: `def replace(...)`

---

## File: `optexity/schema/actions/extraction_action.py`

**File Type**: Python Source

*   **Class**: `LLMExtraction`
    *   **Method**: `def build_model(...)`
    *   **Method**: `def validate_extraction_format(...)`
    *   **Method**: `def validate_output_var_in_format(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `NetworkCallExtraction`
    *   **Method**: `def download_filename_if_download_from_is_set(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `PythonScriptExtraction`
    *   **Method**: `def validate_script(...)`
    *   **Method**: `def validate_output_var_in_format(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `ScreenshotExtraction`

*   **Class**: `StateExtraction`

*   **Class**: `PDFExtraction`
    *   **Method**: `def build_model(...)`
    *   **Method**: `def validate_extraction_format(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `OCRCoordinatesExtraction`
    *   **Method**: `def validate_bounding_box_variables_length(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `VisionExtraction`
    *   **Method**: `def replace(...)`

*   **Class**: `LocatorExtraction`
    *   **Method**: `def validate_variable_in_format(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `APICallExtraction`
    *   **Method**: `def replace(...)`

*   **Class**: `ExtractionAction`
    *   **Method**: `def validate_one_extraction(...)`
    *   **Method**: `def replace(...)`

---

## File: `optexity/schema/actions/interaction_action.py`

**File Type**: Python Source

*   **Class**: `Locator`

*   **Class**: `DialogAction`

*   **Class**: `BaseAction`
    *   **Method**: `def validate_bounding_box_variables_length(...)`
    *   **Method**: `def parse_coordinates(...)`
    *   **Method**: `def validate_one_extraction(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `CheckAction`

*   **Class**: `UncheckAction`

*   **Class**: `HoverAction`

*   **Class**: `SelectOptionAction`
    *   **Method**: `def set_download_filename(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `ClickElementAction`
    *   **Method**: `def set_download_filename(...)`
    *   **Method**: `def validate_mouse_click_deviation(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `InputTextAction`
    *   **Method**: `def validate_press_enter(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `DownloadUrlAsPdfAction`
    *   **Method**: `def replace(...)`

*   **Class**: `ScrollAction`
    *   **Method**: `def validate_amount(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `UploadFileAction`
    *   **Method**: `def _exactly_one_source(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `GoToUrlAction`
    *   **Method**: `def replace(...)`

*   **Class**: `GoBackAction`

*   **Class**: `SwitchTabAction`

*   **Class**: `CloseCurrentTabAction`

*   **Class**: `CloseAllButLastTabAction`

*   **Class**: `CloseTabsUntil`
    *   **Method**: `def validate_one_of_matching_url_or_tab_index(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `KeyPressType`

*   **Class**: `KeyPressAction`
    *   **Method**: `def validate_key_combination(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `AgenticTask`
    *   **Method**: `def replace(...)`

*   **Class**: `CloseOverlayPopupAction`

*   **Class**: `InteractionAction`
    *   **Method**: `def validate_one_interaction(...)`
    *   **Method**: `def replace(...)`

---

## File: `optexity/schema/actions/keyboard_keys.py`

**File Type**: Python Source

---

## File: `optexity/schema/actions/llm_actions.py`

**File Type**: Python Source

*   **Class**: `LLMAction`

---

## File: `optexity/schema/actions/misc_action.py`

**File Type**: Python Source

*   **Class**: `LLMQueryAction`
    *   **Method**: `def build_model(...)`
    *   **Method**: `def validate_output_format(...)`
    *   **Method**: `def validate_output_var_in_format(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `PythonScriptAction`
    *   **Method**: `def replace(...)`

*   **Class**: `SleepAction`

*   **Class**: `HumanInLoopAction`

*   **Class**: `StateJumpAction`

*   **Class**: `FailStateAction`
    *   **Method**: `def replace(...)`

*   **Class**: `SetVariableAction`
    *   *Docstring*: Set a value in generated_variables.
    *   **Method**: `def validate_one_provided(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `CountLocatorAction`
    *   *Docstring*: Count how many elements a Playwright locator matches on the current page.
    *   **Method**: `def validate_timeout(...)`
    *   **Method**: `def replace(...)`

*   **Class**: `MiscAction`
    *   *Docstring*: Container for miscellaneous actions (set_variable, llm_query, etc.).
    *   **Method**: `def replace(...)`

---

## File: `optexity/schema/actions/powershell_action.py`

**File Type**: Python Source

*   **Class**: `PowerShellAction`
    *   *Docstring*: Run a list of PowerShell commands on the current RDP Windows machine.
    *   **Method**: `def validate_commands(...)`
    *   **Method**: `def replace(...)`

---

## File: `optexity/schema/actions/prompts.py`

**File Type**: Python Source

---

## File: `optexity/schema/actions/two_fa_action.py`

**File Type**: Python Source

*   **Class**: `EmailTwoFAAction`
    *   **Method**: `def replace(...)`

*   **Class**: `SlackTwoFAAction`
    *   **Method**: `def replace(...)`

*   **Class**: `SMS2FAAction`
    *   **Method**: `def replace(...)`

*   **Class**: `TwoFAAction`
    *   **Method**: `def replace(...)`

---

## File: `optexity/examples/__init__.py`

**File Type**: Python Source

---

## File: `optexity/examples/add_example.py`

**File Type**: Python Source

*   **Function**: `def main(...)`

---

## File: `optexity/examples/download_pdf_url.py`

**File Type**: Python Source

---

## File: `optexity/examples/extract_price_stockanalysis.py`

**File Type**: Python Source

---

## File: `optexity/examples/file_upload.py`

**File Type**: Python Source

---

## File: `optexity/examples/i94.py`

**File Type**: Python Source

---

## File: `optexity/examples/i94_travel_history.py`

**File Type**: Python Source

---

## File: `optexity/examples/login_cookies.json`

**File Type**: JSON Configuration
```json
{
    "url": "https://dev.dashboard.optexity.com/login",
    "parameters": {
        "input_parameters": {
            "email": ["test@gmail.com"],
            "password": ["12345678"]
        },
        "generated_parameters": {}
    },
    "nodes": [
        {
            "type": "action_node",
            "interaction_action": {
                "input_text": {
                    "command": "get_by_role(\"textbox\", name=\"Email\")",
... [content truncated]
```

---

## File: `optexity/examples/peachstate_medicaid.py`

**File Type**: Python Source

---

## File: `optexity/examples/supabase_login.py`

**File Type**: Python Source

---

## File: `optexity/utils/__init__.py`

**File Type**: Python Source

---

## File: `optexity/utils/aws_secret_manager.py`

**File Type**: Python Source

*   **Class**: `AWSSecretsManager`
    *   *Docstring*: Wrapper around boto3 Secrets Manager client.
    *   **Method**: `def __init__(...)`
    *   **Method**: `def fetch_secret(...)`

---

## File: `optexity/utils/http.py`

**File Type**: Python Source

---

## File: `optexity/utils/integration_secrets.py`

**File Type**: Python Source

---

## File: `optexity/utils/llm_settings.py`

**File Type**: Python Source
**Module Docstring**:
```
Model routing config, in its own module so that importing it does not
construct the task-runtime `Settings` singleton.

`optexity.inference.models` needs only these four fields. Keeping them here lets
an embedder that uses just the model layer (opcloud's recording processor) import
it without supplying OPTEXITY_API_KEY or a DEPLOYMENT this package recognises —
importing `optexity.utils.settings` would run `Settings()` and fail on both.
```

*   **Class**: `LLMSettings`
    *   **Method**: `def llm_api_key_for(...)`

*   **Function**: `def resolve_llm_api_key(...)`
    *   *Docstring*: The configured key for this litellm model string, else the provider env var.

---

## File: `optexity/utils/settings.py`

**File Type**: Python Source

*   **Class**: `Settings`
    *   **Method**: `def validate_local_callback_url(...)`

---

## File: `optexity/utils/utils.py`

**File Type**: Python Source

*   **Function**: `def decrypt_fernet_payload(...)`

*   **Function**: `def build_model(...)`

*   **Function**: `def get_totp_code(...)`

*   **Function**: `def clean_url(...)`

*   **Function**: `def is_url(...)`

*   **Function**: `def is_local_path(...)`

*   **Function**: `def deep_replace(...)`
    *   *Docstring*: Recursively replace pattern in all string values of a dict/list.

*   **Function**: `def resolve_download_metadata_template(...)`
    *   *Docstring*: Resolve ``{key[index]}`` placeholders in download_metadata from live vars.

---

## File: `optexity/prompts/__init__.py`

**File Type**: Python Source

---

## File: `optexity/prompts/agentic_fallback.md`

**File Type**: Markdown Documentation
**Headers found**:
*   # Agentic Fallback
*   ## Information you have
*   ## The step to perform
*   ## How to handle it

---

## File: `optexity/inference/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/child_process.py`

**File Type**: Python Source

*   **Class**: `ChildProcessIdRequest`

*   **Class**: `HumanInLoopCompletedBody`

*   **Function**: `def _enqueue_task(...)`
    *   *Docstring*: Put a task on the local priority queue: lower priority runs first, None

*   **Function**: `def log_system_info(...)`

*   **Function**: `def get_app_with_endpoints(...)`

*   **Function**: `def main(...)`
    *   *Docstring*: Main function to run the server.

---

## File: `optexity/inference/run_local.py`

**File Type**: Python Source

---

## File: `optexity/inference/worker.py`

**File Type**: Python Source

*   **Function**: `def _force_exit(...)`
    *   *Docstring*: Exit immediately, ignoring leftover non-daemon threads (Playwright/Chrome).

---

## File: `optexity/inference/agents/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/index_prediction/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/index_prediction/action_prediction_locator_axtree.py`

**File Type**: Python Source

*   **Class**: `IndexPredictionOutputAllowNegative`

*   **Class**: `IndexPredictionOutputPositiveOnly`

*   **Class**: `ActionPredictionLocatorAxtree`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def predict_action(...)`

---

## File: `optexity/inference/agents/index_prediction/prompt.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/select_value_prediction/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/select_value_prediction/prompt.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/select_value_prediction/select_value_prediction.py`

**File Type**: Python Source

*   **Class**: `SelectValuePredictionOutput`

*   **Class**: `SelectValuePredictionAgent`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def predict_select_value(...)`

---

## File: `optexity/inference/agents/two_fa_extraction/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/two_fa_extraction/prompt.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/two_fa_extraction/two_fa_extraction.py`

**File Type**: Python Source

*   **Class**: `TwoFAExtractionOutput`

*   **Class**: `TwoFAExtraction`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def extract_code(...)`

---

## File: `optexity/inference/agents/select_option_prediction/prompt.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/select_option_prediction/select_option_prediction.py`

**File Type**: Python Source

*   **Class**: `SelectOptionPredictionOutput`

*   **Class**: `SelectOptionPredictionAgent`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def predict_select_option(...)`

---

## File: `optexity/inference/agents/input_text_prediction/input_text_prediction.py`

**File Type**: Python Source

*   **Class**: `InputTextPredictionOutput`

*   **Class**: `InputTextPredictionAgent`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def predict_input_text(...)`

---

## File: `optexity/inference/agents/input_text_prediction/prompt.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/error_handler/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/agents/error_handler/error_handler.py`

**File Type**: Python Source

*   **Class**: `ErrorHandlerOutput`

*   **Class**: `ErrorHandlerAgent`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def classify_error(...)`

---

## File: `optexity/inference/agents/error_handler/prompt.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/for_loop_placeholders.py`

**File Type**: Python Source
**Module Docstring**:
```
Placeholder expansion helpers for for_loop_node iterations.
```

*   **Function**: `def _bind_index(...)`
    *   *Docstring*: Bind bare ``{<index_variable_name>}`` → ``<N>``.

*   **Function**: `def expand_for_loop_placeholders(...)`
    *   *Docstring*: Bind loop placeholders for one iteration onto a deep-copied node.

*   **Function**: `def expand_locator_for_loop_placeholders(...)`
    *   *Docstring*: Bind locator-loop placeholders for one iteration onto a deep-copied node.

*   **Function**: `def expand_iteration_placeholders(...)`
    *   *Docstring*: Dispatch one iteration's bindings to the right expander.

---

## File: `optexity/inference/core/logging.py`

**File Type**: Python Source

*   **Function**: `def create_tar_in_memory(...)`

*   **Function**: `def _redact_callback_data(...)`
    *   *Docstring*: Return a copy of the callback payload with secrets masked, safe to log.

---

## File: `optexity/inference/core/run_assertion.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/run_automation.py`

**File Type**: Python Source

*   **Function**: `def _is_same_url(...)`
    *   *Docstring*: Exact match apart from a trailing slash on the path.

*   **Function**: `def _store_private_node_result(...)`
    *   *Docstring*: Publish a handler's return value the same way extraction nodes do.

*   **Function**: `def evaluate_condition(...)`

---

## File: `optexity/inference/core/run_extraction.py`

**File Type**: Python Source

*   **Function**: `def _llm_extraction_uses_axtree_or_screenshot(...)`

*   **Function**: `def _extraction_response_contains_null(...)`

*   **Function**: `def _enforce_extraction_not_null(...)`
    *   *Docstring*: Fail the automation if the extraction produced null value(s).

---

## File: `optexity/inference/core/run_human_in_loop.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/run_interaction.py`

**File Type**: Python Source

*   **Function**: `def _get_error_handler(...)`

---

## File: `optexity/inference/core/run_misc.py`

**File Type**: Python Source

*   **Function**: `def _maybe_append_output_data(...)`

---

## File: `optexity/inference/core/run_python_script.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/run_two_fa.py`

**File Type**: Python Source

*   **Function**: `def _get_two_fa_agent(...)`

---

## File: `optexity/inference/core/script_context.py`

**File Type**: Python Source
**Module Docstring**:
```
Runtime context handed to ``python_script`` nodes that ask for it.

Script nodes can compute a file's bytes but historically had no way to say
"this is a downloadable output of the task" — only ``expect_download``
interaction nodes could. That forced authors to base64 the bytes back into
the page, build a ``Blob`` + ``<a download>`` anchor, and add a second
``click_element`` node purely so Chromium would emit a download event.

``ScriptContext.save_download`` closes that gap. It joins the download model
at the point every existing path already converges: write into
``task.downloads_directory``, append to ``memory.downloads``, and register
metadata into ``memory.download_metadata`` using the same
``resolve_download_metadata_template`` helper ``handle_download`` uses. The
capture mechanics of ``expect_download`` are untouched.
```

*   **Function**: `def sanitize_download_filename(...)`
    *   *Docstring*: Make a user-visible label safe to use as a filename.

*   **Function**: `def _unique_path(...)`
    *   *Docstring*: Return a path in ``directory`` that does not collide with an existing file.

*   **Class**: `ScriptContext`
    *   *Docstring*: Optional third argument for ``python_script`` node functions.
    *   **Method**: `def __init__(...)`
    *   **Method**: `def _register_download_metadata(...)`
    *   **Method**: `def downloads_dir(...)`
    *   **Method**: `def state(...)`
    *   **Method**: `def variables(...)`
    *   **Method**: `def input_parameters(...)`
    *   **Method**: `def unique_parameters(...)`
    *   **Method**: `def log(...)`

---

## File: `optexity/inference/core/variable_resolver.py`

**File Type**: Python Source
**Module Docstring**:
```
Dot-path variable resolver for API call response dicts.

Resolves patterns like {var.field}, {var.nested.field}, {var.array[0].field}
in action node string fields. Only applies to dict-valued generated variables
(e.g., API call responses). Does NOT interfere with the existing {key[index]}
replacement system.
```

*   **Function**: `def _parse_path_segments(...)`
    *   *Docstring*: Parse '.foo.bar[0].baz' into [('attr','foo'), ('attr','bar'), ('index',0), ('attr','baz')]

*   **Function**: `def _resolve_path(...)`
    *   *Docstring*: Walk a dict/list structure following a dot/bracket path.

*   **Function**: `def resolve_api_variables_in_node(...)`
    *   *Docstring*: Resolve all {var.path} patterns in an action node using dict-valued generated variables.

*   **Function**: `def evaluate_poll_condition(...)`
    *   *Docstring*: Evaluate a poll condition expression against an API response dict.

---

## File: `optexity/inference/core/interaction/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/interaction/agentic_fallback.py`

**File Type**: Python Source

*   **Function**: `def _load_fallback_prompt_template(...)`

*   **Function**: `def _summarize_action_node(...)`
    *   *Docstring*: Return a short human-readable summary of an action node for context.

*   **Function**: `def _describe_goal(...)`
    *   *Docstring*: Build a complete, self-contained goal for the fallback agent.

*   **Function**: `def _flatten_action_nodes(...)`
    *   *Docstring*: Statically flatten the automation tree into a linear list of ActionNodes.

*   **Function**: `def _describe_node_for_window(...)`
    *   *Docstring*: Value-bearing description of a node for the workflow window.

*   **Function**: `def _build_workflow_window(...)`
    *   *Docstring*: Build a small window (prev + current + next steps) around the failing step.

*   **Function**: `def _render_input_parameters(...)`
    *   *Docstring*: Render the automation's (non-secret) input parameters for the agent.

---

## File: `optexity/inference/core/interaction/handle_agentic_task.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/interaction/handle_captcha.py`

**File Type**: Python Source

*   **Class**: `CaptchaBoxes`

*   **Class**: `CaptchaRefreshCheck`

---

## File: `optexity/inference/core/interaction/handle_check.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/interaction/handle_click.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/interaction/handle_command.py`

**File Type**: Python Source

*   **Function**: `def _action_method(...)`
    *   *Docstring*: The trailing Playwright call for an action, e.g. ``.click(button='left')`` —

---

## File: `optexity/inference/core/interaction/handle_hover.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/interaction/handle_input.py`

**File Type**: Python Source

*   **Function**: `def _get_input_text_prediction_agent(...)`

---

## File: `optexity/inference/core/interaction/handle_keypress.py`

**File Type**: Python Source

---

## File: `optexity/inference/core/interaction/handle_select.py`

**File Type**: Python Source

*   **Function**: `def _get_select_option_prediction_agent(...)`

*   **Function**: `def _build_css_selector(...)`
    *   *Docstring*: Build a CSS selector from the node's attributes to locate it in the live DOM.

---

## File: `optexity/inference/core/interaction/handle_select_utils.py`

**File Type**: Python Source

*   **Function**: `def _get_select_prediction_agent(...)`

*   **Class**: `SelectOptionValue`

*   **Function**: `def llm_select_match(...)`

*   **Function**: `def score_match(...)`

---

## File: `optexity/inference/core/interaction/handle_upload.py`

**File Type**: Python Source

*   **Function**: `def _derive_suffix(...)`

---

## File: `optexity/inference/core/interaction/utils.py`

**File Type**: Python Source

*   **Class**: `LocatorExtraction`
    *   *Docstring*: Builds a stable, copy-pasteable Playwright locator for a DOM element and records
    *   **Method**: `def _quote_locator_value(...)`
    *   **Method**: `def _short_element_text(...)`
    *   **Method**: `def _looks_dynamic(...)`
    *   **Method**: `def _css_attr(...)`
    *   **Method**: `def _scored_candidates(...)`
    *   **Method**: `def build_playwright_locator(...)`
    *   **Method**: `def locator_candidates(...)`
    *   **Method**: `def record_locator_candidates(...)`

*   **Function**: `def _get_index_prediction_agent(...)`

*   **Function**: `def _snapshot_dir(...)`
    *   *Docstring*: Return {filename: mtime} for all files in directory.

---

## File: `optexity/inference/core/two_factor_auth/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/models/__init__.py`

**File Type**: Python Source

*   **Function**: `def normalize_model(...)`
    *   *Docstring*: Build a litellm model string from the task's (provider, model) pair.

*   **Function**: `def get_llm_model(...)`

*   **Function**: `def get_llm_model_with_fallback(...)`
    *   *Docstring*: Fallback is handled inside litellm via llm_settings.LLM_MODEL_FALLBACK.

---

## File: `optexity/inference/models/chat_litellm.py`

**File Type**: Python Source
**Module Docstring**:
```
browser-use ``BaseChatModel`` backed by litellm.

The browser-use agentic paths need a browser-use chat model, which is a
different type from the ``LLMModel`` the registry hands out. Rather than talk to
a provider SDK directly — which is how these paths came to run on a hardcoded
Gemini model, with their own key resolution and no fallback — this adapts
litellm to that interface so every LLM call in the engine goes through one
layer, on the model the task asked for.

It stays thin because litellm speaks the OpenAI wire format, so browser-use's
own ``OpenAIMessageSerializer`` does the message conversion.
```

*   **Class**: `ChatLiteLLM`
    *   *Docstring*: A litellm model string, exposed as a browser-use chat model.
    *   **Method**: `def provider(...)`
    *   **Method**: `def name(...)`
    *   **Method**: `def _usage(...)`
    *   **Method**: `def _request(...)`

*   **Function**: `def build_agent_llm(...)`
    *   *Docstring*: The chat model for the browser-use agentic paths.

---

## File: `optexity/inference/models/human.py`

**File Type**: Python Source

*   **Class**: `Human`
    *   **Method**: `def __init__(...)`

---

## File: `optexity/inference/models/litellm_model.py`

**File Type**: Python Source

*   **Function**: `def _sanitize_schema_keys(...)`
    *   *Docstring*: Recursively replace spaces in dict keys with _._

*   **Function**: `def _restore_schema_keys(...)`
    *   *Docstring*: Recursively replace _._ in dict keys back to spaces.

*   **Function**: `def reasoning_effort_for(...)`
    *   *Docstring*: The reasoning_effort to force on a model, or None to leave it unset.

*   **Function**: `def litellm_fallbacks(...)`
    *   *Docstring*: LLM_MODEL_FALLBACK as a litellm dict so it carries its own api_key.

*   **Function**: `def _pdf_to_base64(...)`

*   **Class**: `LiteLLMModel`
    *   *Docstring*: Single provider-agnostic backend. `model_name` is any litellm model string.
    *   **Method**: `def _build_messages(...)`
    *   **Method**: `def _completion(...)`
    *   **Method**: `def _token_usage_from(...)`
    *   **Method**: `def _get_model_response(...)`
    *   **Method**: `def _get_model_response_with_structured_output(...)`

---

## File: `optexity/inference/models/llm_model.py`

**File Type**: Python Source

*   **Function**: `def extract_json_objects(...)`

*   **Function**: `def parse_json_from_completion(...)`
    *   *Docstring*: Recover a schema instance from a completion that isn't clean JSON.

*   **Class**: `LLMModel`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def _get_model_response(...)`
    *   **Method**: `def _get_model_response_with_structured_output(...)`
    *   **Method**: `def get_model_response(...)`
    *   **Method**: `def get_model_response_with_structured_output(...)`
    *   **Method**: `def extract_json_objects(...)`
    *   **Method**: `def parse_from_completion(...)`
    *   **Method**: `def get_token_usage(...)`

---

## File: `optexity/inference/infra/__init__.py`

**File Type**: Python Source

---

## File: `optexity/inference/infra/actual_browser.py`

**File Type**: Python Source

*   **Function**: `def find_chrome_binary(...)`

*   **Class**: `ActualBrowser`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def _seed_print_preferences(...)`
    *   **Method**: `def get_args(...)`
    *   **Method**: `def get_extension_paths(...)`
    *   **Method**: `def get_proxy_args_native(...)`
    *   **Method**: `def get_proxy_playwright(...)`

---

## File: `optexity/inference/infra/browser.py`

**File Type**: Python Source

*   **Class**: `Browser`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def get_xpath_from_index(...)`

---

## File: `optexity/inference/infra/browser_extension.py`

**File Type**: Python Source

*   **Class**: `BrowserExtension`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def get_extension_paths(...)`

---

## File: `optexity/inference/infra/browser_health.py`

**File Type**: Python Source
**Module Docstring**:
```
Browser session health checks and dedicated-browser restart signaling.
```

*   **Function**: `def is_driver_closed_error(...)`

*   **Function**: `def is_browser_session_poisoned_error(...)`

*   **Function**: `def get_child_process_id_from_env(...)`

*   **Function**: `def get_browser_restart_flag_path(...)`

*   **Function**: `def request_browser_restart(...)`

*   **Function**: `def consume_browser_restart_request(...)`

*   **Function**: `def update_memory_browser_state_from_summary(...)`

---

## File: `optexity/inference/infra/extension_test.py`

**File Type**: Python Source

*   **Class**: `ChromeWithExtensions`
    *   **Method**: `def __init__(...)`
    *   **Method**: `def add_extension(...)`
    *   **Method**: `def setup_forced_extensions(...)`
    *   **Method**: `def launch(...)`

---

## File: `optexity/inference/infra/utils.py`

**File Type**: Python Source

*   **Function**: `def _download_extension(...)`
    *   *Docstring*: Download extension .crx file.

*   **Function**: `def _extract_extension(...)`
    *   *Docstring*: Extract .crx file to directory.

---
