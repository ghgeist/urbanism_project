# Session Management Best Practices for All Agents

**Date**: 2025-09-12  
**Status**: Active  
**Purpose**: Supplementary guidance for session management (works with `_session-management-core.md`)  
**Platform**: Universal - Works with Cursor, Claude Code, Gemini CLI, Codex, and other agents

## 📚 Core Reference

**IMPORTANT**: This document provides supplementary best practices and examples. For mandatory rules and requirements, see **`agents/_session-management-core.md`** - the canonical reference that all agents must follow.

## 🎯 Current Session Structure

```
docs/sessions/
├── active/          # Currently working sessions (1-2 max)
├── backlog/         # Planned future sessions  
└── completed/       # Finished sessions with outcomes
```

## 📋 Session File Naming Convention

Based on user preferences [[memory:8730623]] [[memory:8730527]]:

**Format**: `YYYY-MM-DD-[session-type]-[description].md`

**Examples**:

- `2025-09-12-deploy-production-model.md`
- `2025-09-12-debug-authentication-issue.md`
- `2025-09-12-refactor-database-queries.md`

## 🔧 Agent Output Guidelines

### 1. Session Artifact Creation

**All agents should** (platform-agnostic approach):

```markdown
## Session Artifacts Management

When starting work:
1. Check `docs/sessions/active/` for existing sessions
   - Cursor: Use `list_dir`
   - Claude Code: Use shell commands (`ls`, `dir`) or file navigation
   - Gemini CLI: Use file system list tools
   - Codex: Use IDE directory listing
2. If no relevant active session exists, create one
   - Cursor: Use `write`
   - Claude Code: Use text editor tool
   - Gemini CLI: Use file system write
   - Codex: Use IDE file creation
3. If relevant session exists, read to understand context
   - Cursor: Use `read_file`
   - Claude Code: Use text editor tool to read
   - Gemini CLI: Use file system read
   - Codex: Use IDE file reading
4. Update session file throughout work
   - Cursor: Use `search_replace`
   - Claude Code: Use text editor tool to modify
   - Gemini CLI: Use file system modify
   - Codex: Use IDE editing
```

### 2. Session Types & Outputs

**CRITICAL**: ALL session files MUST be stored in `docs/sessions/active/` during active work.

| Session Type | Session File Location | Secondary Outputs |
|-------------|---------------------|-------------------|
| **RESEARCH** | `docs/sessions/active/` | `docs/research/` if needed |
| **PLAN** | `docs/sessions/active/` | None |
| **EXECUTE** | `docs/sessions/active/` | Code changes in place |
| **DEBUG** | `docs/sessions/active/` | Bug fix documentation |
| **DEPLOY** | `docs/sessions/active/` | Deployment logs/scripts |
| **REFACTOR** | `docs/sessions/active/` | `docs/code_improvement_log/` |
| **TEST** | `docs/sessions/active/` | Test results in session |

### 3. Session State Management

**Active Sessions (1-2 maximum)**:

- Current work in progress
- Updated in real-time during agent interactions
- Moved to `completed/` when finished

**Session Lifecycle**:

```markdown
1. **Create**: Agent creates new session in `active/`
2. **Update**: Agent updates session throughout work
3. **Complete**: Agent moves session to `completed/` when done
4. **Archive**: Old sessions stay in `completed/` for reference
```

## 🚀 Agent Implementation Patterns

### Pattern 1: Session-Aware Agent Start

```markdown
Every agent should begin with:

1. **Check Active Sessions**:
   - Use platform-appropriate tool to check docs/sessions/active/
   - Use platform-appropriate tool to read and understand current context
   - See `_platform-detection-guide.md` for tool mappings

2. **Create or Update Session**:
   - If no relevant session: Create new session using platform-appropriate tool
   - If relevant session exists: Update using platform-appropriate tool
   - Follow naming convention: YYYY-MM-DD-[type]-[description].md

3. **Set Session Context**:
   - Document what agent is doing
   - Set expected outcomes
   - Track progress throughout work
```

### Pattern 2: Work Documentation

```markdown
Throughout agent work:

1. **Progress Updates**:
   - Update session file with current progress
   - Document decisions and rationale
   - Track blockers and solutions

2. **Artifact Links**:
   - Link to created/modified files
   - Reference related sessions
   - Document dependencies

3. **Outcome Recording**:
   - Final results and deliverables
   - Success criteria met/unmet
   - Next steps or follow-up needed
```

### Pattern 3: Session Completion

```markdown
When agent completes work:

1. **Final Update**:
   - Mark session as completed
   - Document final outcomes
   - Add success/failure status

2. **Move to Completed**:
   - Use file operations to move from active/ to completed/
   - Preserve all session history
   - Update any references

3. **Clean Up**:
   - Remove from active/ directory
   - Update any related sessions
   - Create follow-up sessions if needed
```

## 📝 Session Template Integration

### Enhanced Agent Prompts

All agents should include this session management pattern:

```markdown
## SESSION MANAGEMENT INTEGRATION

### Session Discovery
- Use platform-appropriate tools to check `docs/sessions/active/` for relevant work
- Use platform-appropriate tools to read and understand existing session context
- Use platform-appropriate search tools to find related sessions in `backlog/` and `completed/`
- See `_platform-detection-guide.md` for specific tool mappings

### Session Creation/Updates
- Use platform-appropriate tools to create new session if none exists
- Use platform-appropriate tools to update existing sessions
- Follow YYYY-MM-DD-[type]-[description].md naming convention
- Reference `_session-management-core.md` for mandatory requirements

### Session Lifecycle
- Keep sessions in `active/` during work
- Update progress throughout agent interaction
- Move to `completed/` when work is finished
- Create follow-up sessions in `backlog/` if needed
```

## 🎯 Specific Agent Behaviors

### Code Improvement Agent

- **Always** check `docs/code_improvement_log/` for previous work
- **Create session** in `docs/sessions/active/` for current improvement work
- **Link** to improvement log entries from session
- **Move** session to `completed/` when improvement is done

### Deployment Agents

- **Create detailed deployment session** with rollback plans
- **Track deployment progress** in real-time
- **Document** all deployment steps and outcomes
- **Keep** deployment sessions for audit trail

### Debug Agents  

- **Create debug session** with problem description
- **Document** debugging process and findings
- **Track** reproduction steps and solutions
- **Link** to any code fixes made

### Planning Agents

- **Create planning session** with objectives and approach
- **Break down** work into implementable tasks
- **Create follow-up sessions** in `backlog/` for execution
- **Link** planning sessions to execution sessions

## 🔍 Session Quality Checklist

### Every Session Should Have

- [ ] **Clear title** following naming convention
- [ ] **Session type** clearly identified
- [ ] **Objectives** or goals stated
- [ ] **Progress tracking** throughout work
- [ ] **Outcomes documented** when complete
- [ ] **Links** to related files/sessions
- [ ] **Next steps** or follow-up actions

### Session Metadata

```yaml
---
title: "Session Title"
date: "YYYY-MM-DD"
status: "active|completed|blocked"
session_type: "research|plan|execute|debug|deploy|refactor|test"
priority: "high|medium|low"
tags: ["relevant", "tags"]
author: "agent-name"
related: ["path/to/related/sessions"]
---
```

## 🚨 Common Pitfalls to Avoid

### DON'T

❌ Create multiple active sessions for the same type of work  
❌ Skip session creation for significant agent work  
❌ Leave sessions in `active/` after work is complete  
❌ Create sessions without clear objectives  
❌ Forget to link related work and artifacts  

### DO

✅ Keep active sessions to 1-2 maximum  
✅ Update sessions throughout agent work  
✅ Move completed sessions promptly  
✅ Use consistent naming conventions  
✅ Document decisions and rationale  

## 🎉 Expected Benefits

### For Users

- **Clear work tracking** across all agent interactions
- **Session continuity** between different agent types
- **Audit trail** of all development work
- **Context preservation** for future work

### For Agents

- **Better context awareness** of ongoing work
- **Reduced duplicate effort** through session discovery
- **Consistent output patterns** across agent types
- **Improved collaboration** between different agents

---

## 🔗 Related Documents

- **`agents/_session-management-core.md`** - Mandatory canonical rules (all agents must follow)
- **`agents/_platform-detection-guide.md`** - Tool mappings for different platforms
- **`agents/_cursor-integration-standard.md`** - Cursor-specific integration
- **`agents/_claude-code-integration-standard.md`** - Claude Code integration
- **`agents/_gemini-cli-integration-standard.md`** - Gemini CLI integration
- **`agents/_codex-integration-standard.md`** - Codex integration

---

**Implementation Status**: Ready for immediate adoption by all agents across all platforms  
**Platform Compatibility**: ✅ Cursor ✅ Claude Code ✅ Gemini CLI ✅ Codex ✅ Other agents
