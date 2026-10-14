# [Dashboard Name] — Runbook (Internal)

**Project Slug:** `<project-name>`  
**Maintained By:** `<team/owner>`  
**Last Updated:** `<YYYY-MM-DD>`  
**Escalation Contact:** `<contact>`

---

## Quick Reference

**Location:** `./<project-name>/dashboards/dashboard.html`  
**Data Source:** `<SOURCE_DB>` / `<SINK_DB>` (if Phase 2)  
**Update Method:** [Manual / Automatic workflow]  
**Backup:** Keep copy in `<backup-location>`

---

## Weekly Maintenance Checklist

### Monday Morning (Start of Week)

- [ ] Check if dashboard loaded successfully
- [ ] Verify latest data is present (check timestamp in dashboard footer)
- [ ] Spot-check one KPI against source database
- [ ] Review error logs (if applicable)

### Every 3 Days

- [ ] Monitor data freshness (should be < 24 hours old)
- [ ] Watch for anomalies in metrics (sudden spikes/drops)
- [ ] Check if users reported any issues

### End of Month

- [ ] Archive current dashboard version
- [ ] Review and update documentation if needed
- [ ] Check storage space (file size growth)

---

## Manual Refresh (Non-Workflow Path)

Use this when data needs immediate update:

```bash
cd ./<project-name>/dashboards

# Set environment variables
export SOURCE_DB=<database_name>
export SINK_DB=<database_name>

# Run data generation
node generate-data.js

# Expected output:
# ✅ dashboard.html written — X rows across Y queries (inline data)
```

**Time Required:** ~X minutes  
**Validation:** Open `dashboard.html` and verify data looks reasonable

---

## Automated Workflow Refresh (Phase 2 Path)

Workflow runs automatically per schedule.

### Check Workflow Status

```bash
# List recent runs
td workflow run list -w <workflow-name>

# View latest run details
td workflow run show <run-id>

# View logs
td workflow run logs <run-id>
```

### Manual Trigger (If Needed)

```bash
cd ./<project-name>/workflows

# Run workflow immediately
td workflow run <workflow-name> --project <project-name>

# Monitor output
td workflow run show <run-id> --logs
```

### Common Workflow Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Workflow didn't run at scheduled time | Schedule is UTC, check timezone | Verify schedule in `config.json` |
| Query timeout error | Data volume increased | Contact data platform team |
| Table not found error | Table was renamed/deleted | Update table name in workflow SQL |

---

## Troubleshooting

### Issue 1: Dashboard Shows Old Data

**Steps:**
1. Check last update time in dashboard footer
2. If > 24 hours old, trigger manual refresh
3. If workflow exists, check workflow logs
4. Verify data source tables have recent data

```bash
# Check source data freshness
tdx query -d <database> "SELECT MAX(created_at) FROM <table>"
```

### Issue 2: Numbers Don't Match Other Systems

**Steps:**
1. Verify filters are set correctly (check Architecture doc)
2. Run spot-check query against source data
3. Check exclusion rules (nulls, test records, etc.)
4. Compare date ranges and timezones

```sql
-- Spot-check query
SELECT SUM(amount) AS total
FROM <source_table>
WHERE date >= '<date>'
  AND <exclusion_rules>;
```

### Issue 3: HTML File Is Corrupted

**Steps:**
1. Check file size (should be ~Xmb)
2. Regenerate from scratch
3. Restore from backup

```bash
# Regenerate
cd ./<project-name>/dashboards
SOURCE_DB=<db> SINK_DB=<db> node generate-data.js

# Or restore backup
cp <backup-location>/dashboard.html.bak dashboard.html
```

### Issue 4: File Size Growing Unexpectedly

**Check:** Are queries returning too many rows?

```bash
# Check query row counts in generate-data.js
# Look for SELECT without LIMIT clauses
```

**Fix:** Reduce data scope in queries (narrower date range, add LIMIT)

---

## Escalation Procedures

### Level 1: Data Accuracy Issue

**When:** Numbers look wrong  
**Who:** Data Platform Team  
**Action:**
1. Verify against source database
2. Document discrepancy with screenshots
3. Send report to data platform team

**Template:**
```
Subject: [Dashboard Name] - Data Accuracy Issue

Dashboard shows: [value]
Source query result: [value]
Discrepancy: [X%]
Filters used: [list]
Date of occurrence: [date]

Possible causes:
- [list your hypotheses]
```

### Level 2: Workflow Failure

**When:** Workflow didn't run, data is stale  
**Who:** Data Infrastructure Team  
**Action:**
1. Check workflow logs: `td workflow run logs <id>`
2. Identify error message
3. Report with logs to infrastructure team

### Level 3: Dashboard Technical Issue

**When:** File won't open, browser crashes  
**Who:** Engineering Team  
**Action:**
1. Verify HTML file is not corrupted
2. Try different browser
3. Regenerate from source
4. Escalate if issue persists

---

## Deployment Procedures

### Deploy Updated Dashboard

**Non-Workflow (Manual Build):**
```bash
cd ./<project-name>/dashboards
SOURCE_DB=<db> SINK_DB=<db> node generate-data.js
# New version saved to dashboard.html
# Backup old version first!
```

**Workflow Path:**
```bash
cd ./<project-name>/workflows
# Edit workflow SQL or config if needed
td push  # Deploy updated workflow
# Workflow will run on next scheduled time
```

### Deploy Phase 4 Skill Update

If Track A skill exists:
```bash
cd ~/.claude/skills/<skill-name>
npm run build
# Skill updated for next use
```

---

## Backup & Recovery

### Daily Backup

```bash
# Add to cron or scheduled task
cp ./<project-name>/dashboards/dashboard.html \
   ./<project-name>/dashboards/backups/dashboard.$(date +%Y%m%d).html

# Keep last 30 days of backups
find ./<project-name>/dashboards/backups -mtime +30 -delete
```

### Recovery

```bash
# List backups
ls -la ./<project-name>/dashboards/backups/

# Restore specific date
cp ./<project-name>/dashboards/backups/dashboard.20260801.html \
   ./<project-name>/dashboards/dashboard.html
```

---

## Performance Monitoring

### Metrics to Watch

| Metric | Target | Alert If |
|--------|--------|----------|
| Query Time | < 5s | > 10s |
| HTML File Size | ~Xmb | > 2x normal |
| Data Freshness | < 24h old | > 48h old |
| Uptime | 99% | < 95% |

### Performance Check

```bash
# Time the queries
time (SOURCE_DB=<db> SINK_DB=<db> node generate-data.js)

# Check file size
ls -lh ./<project-name>/dashboards/dashboard.html

# Check row counts
# Edit generate-data.js to add console.log statements
```

---

## Change Log

| Date | Change | Who |
|------|--------|-----|
| `<YYYY-MM-DD>` | Initial deployment | [Name] |
| | | |

---

## Related Documentation

- **Architecture:** `architecture.md` — Technical details, metrics, calculations
- **Usage Guide:** `usage_guide.md` (public) — How users interact with the dashboard
- **Access & Ownership:** `access_ownership.md` (internal) — Permissions, support contacts

---

## Emergency Contacts

- **Data Issues:** `<data-contact>` — phone/email
- **Platform Issues:** `<platform-contact>` — phone/email
- **Urgent Escalation:** `<escalation-contact>` — 24/7 support

---

**Version:** 1.0.0  
**Created:** `<date>`  
**Last Modified:** `<date>`
