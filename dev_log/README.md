# Development Log Guidelines

This folder contains development logs documenting significant changes, migrations, and improvements to the project.

## File Naming Convention

Use the format: `YYYY_MM_DD_N.md` where:
- `YYYY_MM_DD` is the date (e.g., `2026_01_21`)
- `N` is a sequence number if multiple logs on the same day (e.g., `1`, `2`)

Example: `2026_01_21_1.md`, `2026_01_21_2.md`

## Log Structure Template

```markdown
# Development Log

## YYYY-MM-DD - [Brief Title]

### [Feature/Change Name]
- **Problem:** [What problem were you solving?]
- **Solution:** [What solution did you implement?]
- **Changes:**
  - [Specific change 1]
  - [Specific change 2]
  - [Specific change 3]

### [Additional Section]
- [Details]

### Results/Outcomes
- [Measurable results, metrics, or verification]
```

## When to Create a Dev Log

Create a dev log entry for:
- ✅ Major migrations (database, hosting platform, framework)
- ✅ Significant refactoring or architecture changes
- ✅ Data organization or cleanup efforts
- ✅ Performance optimizations with measurable results
- ✅ Infrastructure changes (deployment, CI/CD)
- ✅ Breaking changes or major feature additions

Don't create a dev log for:
- ❌ Small bug fixes
- ❌ Minor UI tweaks
- ❌ Routine maintenance
- ❌ Documentation updates (unless substantial)

## Writing Guidelines

1. **Be Specific:** Include file names, function names, and specific changes
2. **Include Context:** Explain the "why" behind decisions
3. **Show Results:** Include metrics, row counts, performance improvements
4. **Use Formatting:** Use markdown formatting for readability
5. **Link to Code:** Reference specific files/functions when relevant
6. **Keep It Concise:** Focus on what matters, not every detail

## Example Structure

```markdown
# Development Log

## 2026-01-21 - Replit Migration & Data Organization

### Migration to Replit PostgreSQL
- **Problem:** [Clear problem statement]
- **Solution:** [Clear solution]
- **Changes:**
  - Updated `services/walkability.py` to support Replit env vars
  - Modified `scripts/create_neo_postgres_db.py` for URL downloads
  - Created `scripts/enable_postgis.py` helper script

### Results
- Successfully loaded 203,645 rows
- PostGIS 3.5 enabled
- Query performance: [metrics if available]
```
