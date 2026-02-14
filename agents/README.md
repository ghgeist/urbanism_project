# Agent Prompts Directory

This directory contains specialized AI agent prompts for different coding tasks. All agents follow consistent structural coherence principles and support multiple AI coding platforms.

**Repo context**: This is a subset of the agent suite, tailored for the urbanism_project (Streamlit, PostGIS, pytest). Agents detect Python/Streamlit context and adapt (e.g. pytest, Neon/PostgreSQL, `streamlit run app.py`).

## Platform Support

All agents support **multi-platform** usage:

- ✅ **Cursor IDE** - Full support with semantic code search
- ✅ **Claude Code** (claude.ai/code) - Full support with tool adaptation
- ✅ **Gemini CLI** - Full support with ReAct loop
- ✅ **Codex** (OpenAI) - Full support with IDE integration

**See**: `_platform-detection-guide.md` for platform detection and tool mapping details.

## Active Agents (Present in This Repo)

### Core Development Agents

- **`performance-agent.md`** - Optimize code to meet production performance requirements
- **`testing_agent.md`** - Validate code works correctly and ships safely (pytest, smoke tests)

### Planning & Management Agents

- **`dev_note_agent.md`** - Synthesize daily engineering activities from GitHub history into `docs/dev_notes/`

### Specialized Agents

- **`readme_agent.md`** - Review and improve README.md for completeness and accuracy
- **`security_agent.md`** - Implement essential security measures for production (input validation, auth, secrets, error handling)

## Infrastructure Files

### Integration Standards

- **`_cursor-integration-standard.md`** - Cursor IDE tool usage patterns
- **`_claude-code-integration-standard.md`** - Claude Code tool usage patterns
- **`_gemini-cli-integration-standard.md`** - Gemini CLI tool usage patterns
- **`_codex-integration-standard.md`** - Codex tool usage patterns
- **`_platform-detection-guide.md`** - Platform detection and tool mapping guide

### Session Management

- **`_session-management-core.md`** - Mandatory session management rules
- **`session-management-best-practices.md`** - Comprehensive session management guide

### Prompt Checks (Structural validation)

- **`prompt_checks/system_composition_check.md`** - Compositional sanity check for systems/prompts
- **`prompt_checks/prompt_topology_check.md`** - Structural topology read for brittleness diagnosis

## Directories Used by Agents

When using session-aware agents (or Cursor integration), the following paths are expected under the repo root:

- **`docs/sessions/active/`** - Active session files (create first session here if using session workflow)
- **`docs/sessions/backlog/`** - Planned future sessions
- **`docs/sessions/completed/`** - Completed sessions (moved here when done)
- **`docs/dev_notes/`** - Dev note output from `dev_note_agent.md`; must contain `README.md` for index updates

## Usage

### For Cursor IDE

Agents automatically detect Cursor and use full tool support including `codebase_search`.

### For Claude Code

Agents automatically adapt to Claude Code tools (bash tool, text editor tool, memory tool).

### For Gemini CLI

Agents automatically adapt to Gemini CLI tools (file system tools, `run_shell_command`).

### For Codex

Agents automatically adapt to Codex tools (IDE integration, terminal/CLI, skills system).

## Structural Coherence

All agents incorporate structural coherence principles:

- **Connectedness**: Address coherent problem spaces
- **Explicit Transformations**: Document what's preserved, transformed, and added
- **Compositional Integrity**: Ensure improvements compose correctly
- **Valid No-Op State**: System works when improvements are disabled
- **Intent Preservation**: Improvements preserve original intent

## Version History

- **v2.0** (2026-02-03): Added multi-platform support, structural coherence principles, YAML frontmatter
- **v1.0** (2025-09-12): Initial standardization with Cursor integration

---

**See individual agent files for detailed usage instructions and examples.**
