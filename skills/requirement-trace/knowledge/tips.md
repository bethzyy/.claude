# Tips for Using Requirement Trace Skill

This document provides practical tips for effectively using the requirement-trace skill.

---

## Quick Reference

### Most Common Actions

| Task | Command |
|------|---------|
| Add requirement | `--action add --requirement "..."` |
| List all | `--action list` |
| Search | `--action search --query "..."` |
| Complete | `--action complete --id REQ-XXX` |
| Get stats | `--action stats` |

### Keyboard Shortcuts (CLI)

```bash
# Short form
-p  = --project-dir
-a  = --action
-r  = --requirement
-t  = --type
-s  = --source
-d  = --description
-o  = --owner
-m  = --milestone
-l  = --labels
-q  = --query
-n  = --note
```

---

## Workflow Tips

### 1. Start Each Session with Status Check

```bash
# Quick project status
python main.py -p ./myproject -a stats

# Check blocked items
python main.py -p ./myproject -a list --blocked
```

### 2. Use Consistent Label Naming

```
Good: frontend, backend, api, ui, security, performance
Bad: front-end/FrontEnd/FE (inconsistent casing)
```

### 3. Create Epics for Large Features

```bash
# Step 1: Create Epic
python main.py -p ./myproject -a add -r "User Authentication System" -t feature

# Step 2: Create child requirements
python main.py -p ./myproject -a add -r "User Registration" --parent REQ-001
python main.py -p ./myproject -a add -r "User Login" --parent REQ-001
python main.py -p ./myproject -a add -r "Password Reset" --parent REQ-001
```

### 4. Use Milestones for Planning

```bash
# Add to milestone
python main.py -p ./myproject -a add -r "Feature X" --milestone "v1.0.0"

# Filter by milestone
python main.py -p ./myproject -a list --milestone "v1.0.0"
```

### 5. Regular Cleanup

```bash
# Weekly: Review blocked requirements
python main.py -p ./myproject -a blocked-report

# Weekly: Complete done items
python main.py -p ./myproject -a complete --id REQ-XXX
```

---

## JSON Output Tips

### For Programmatic Access

```bash
# Get JSON output
python main.py -p ./myproject -a stats --json

# Parse with jq (if available)
python main.py -p ./myproject -a stats --json | jq '.statistics'
```

---

## Filtering Tips

### Combine Filters

```bash
# High priority bugs only
python main.py -p ./myproject -a list --type bugfix --priority high

# Blocked frontend items
python main.py -p ./myproject -a list --blocked --labels "frontend"

# Active items for v2.0.0
python main.py -p ./myproject -a list --status active --milestone "v2.0.0"
```

---

## Search Tips

### Effective Search Queries

```bash
# Search by keyword
python main.py -p ./myproject -a search -q "login"

# Search by ID pattern
python main.py -p ./myproject -a search -q "REQ-"

# Search by label
python main.py -p ./myproject -a search -q "frontend"
```

---

## Dependency Management Tips

### Check Before Blocking

```bash
# View requirement details first
python main.py -p ./myproject -a get --id REQ-001

# Then link
python main.py -p ./myproject -a link --id REQ-001 --link-to REQ-002 --link-type blocks
```

### Visualize Dependencies

Use blocked-report to see dependency chains:

```bash
python main.py -p ./myproject -a blocked-report
```

---

## Acceptance Criteria Tips

### Write SMART Criteria

- **S**pecific: "User can click logout button"
- **M**easurable: "Logout completes in < 1 second"
- **A**chievable: Within project scope
- **R**elevant: Related to the requirement
- **T**estable: Can be verified

### Use Semicolon Separator

```bash
# Multiple criteria
python main.py -p ./myproject -a add -r "Dark Mode" \
  --acceptance-criteria "User can toggle dark/light;Preference saved;Applied on next visit"
```

---

## Effort Estimation Tips

### Use Fibonacci Numbers

Good estimates: 1, 2, 3, 5, 8, 13, 21 hours

### Track Accuracy

```bash
# When completing, record actual
python main.py -p ./myproject -a complete --id REQ-001 --note "Took 10h instead of 8h"
```

---

## Integration with Other Skills

### With task-executor

```bash
# 1. Record requirement
python main.py -p ./myproject -a add -r "Feature X"

# 2. Execute task (using task-executor skill)
# ... task-executor creates implementation ...

# 3. Complete requirement
python main.py -p ./myproject -a complete --id REQ-001
```

### With quality-reviewer

```bash
# 1. Complete requirement
# 2. Review quality
# 3. If issues found, update requirement status
python main.py -p ./myproject -a update --id REQ-001 --status active --note "Reopened: QA issues found"
```

---

## Best Practices Summary

1. **Always capture source** - Original user expression matters
2. **Define acceptance criteria** - Clear "Done" definition
3. **Record dependencies** - Link related requirements
4. **Update status promptly** - Keep progress accurate
5. **Use labels consistently** - Enable filtering
6. **Review blocked items** - Identify bottlenecks
7. **Estimate effort** - Enable planning
8. **Complete done items** - Keep list clean
9. **Use milestones** - Track releases
10. **Regular cleanup** - Weekly review recommended
