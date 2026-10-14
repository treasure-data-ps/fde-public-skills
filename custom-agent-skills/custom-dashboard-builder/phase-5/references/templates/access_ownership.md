# [Dashboard Name] — Access & Ownership (Internal)

**Project Slug:** `<project-name>`  
**Created:** `<YYYY-MM-DD>`  
**Last Updated:** `<YYYY-MM-DD>`

---

## Ownership & Responsibility

### Primary Owner

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| Dashboard Owner | [Name] | [email] | [hours/timezone] |
| Backup Owner | [Name] | [email] | [hours/timezone] |

**Responsibilities:**
- Respond to usage questions within [24h/2 days]
- Monitor data freshness daily
- Perform monthly maintenance checks
- Escalate data issues to data platform team

### Data Owner

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| Data Platform Lead | [Name] | [email] | [hours] |
| Data Engineer On-Call | [Name] | [email] | [hours/on-call schedule] |

**Responsibilities:**
- Ensure source data is fresh and accurate
- Investigate data accuracy issues
- Monitor workflow (if Phase 2)
- Respond to escalations

---

## Access Levels

### Who Can Access

| User/Role | Access Level | Use Case | Approval Required |
|-----------|--------------|----------|-------------------|
| [Team Name] | View + Export | Day-to-day usage | Already approved |
| [Team Name] | View only | Executive reporting | YES — request from owner |
| [Team Name] | Edit (Maintainer) | Updates & fixes | YES — owner approval |
| External Partners | View (shared link) | Reporting | YES — owner + legal |

### How to Grant Access

**Option 1: Share the File**
```
Email dashboard.html to user
- Works on any device
- No login required
- No installation needed
```

**Option 2: Host on Web Server**
```
1. Copy to shared drive or web server
2. Send URL to user
3. Works in any browser
```

**Option 3: Access Control (if on secure network)**
```
1. Place in shared folder
2. Set folder permissions in OS
3. Send folder path to user
```

### How to Revoke Access

**Option 1: File Sharing**
- Don't send new versions
- Request deletion from recipients

**Option 2: Web Server**
- Move file to restricted folder
- Update access controls

**Option 3: Shared Drive**
- Remove user from folder permissions
- Notify user of revocation

---

## Data Sensitivity & Compliance

### Data Classification

- **Sensitivity Level:** [Public / Internal / Confidential / Restricted]
- **PII Included:** [Yes / No] — If yes, which fields?
- **Regulatory Requirements:** [GDPR / HIPAA / SOC2 / Other]

### Handling Requirements

**Data Retention:**
- Keep backups for: [X days / months / years]
- Delete older versions: [Yes / No]
- Archive location: [path]

**Sharing Restrictions:**
- [Can / Cannot] share outside the company
- [Can / Cannot] include in reports to external stakeholders
- [Must / Not required] encrypt when emailing
- [Must / Not required] use VPN for access

**User Agreements:**
- All users must sign: [NDA / Data Usage Agreement / Other]
- Users must complete: [Data Governance Training / Compliance Training]

### Audit Trail

- Dashboard access is logged: [Yes / No]
- Who accessed when: [Data owner team]
- Report location: [path/tool]

---

## Support Structure

### Support Channels

| Question Type | Urgency | Channel | Response Time |
|---------------|---------|---------|----------------|
| "How do I use this?" | Low | Email: `<support-email>` | 1 business day |
| "Why is metric X wrong?" | Medium | Email: `<data-team-email>` | 1-2 business days |
| "Dashboard is broken!" | High | Slack: `@<owner>` | 1 hour |
| "Data is missing!" | Critical | Phone: `<escalation>` | 30 minutes |

### Escalation Path

```
Usage Question
├─ User → Dashboard Owner (support email)
└─ Owner cannot answer → Escalate to Data Team

Data Issue
├─ User → Data Team (email)
├─ Data Team investigates
└─ If platform issue → Escalate to Infrastructure

Critical Issue (Dashboard Down)
├─ User → Dashboard Owner (Slack/Phone)
├─ Owner attempts fix
└─ If cannot resolve → Page on-call engineer
```

---

## Maintenance Schedule

### Weekly Tasks

- **Monday 9 AM:** Check data freshness
- **Wednesday:** Spot-check metrics accuracy
- **Friday:** Review user feedback/issues

### Monthly Tasks

- **1st of month:** Full maintenance check
- **2nd week:** Review and update documentation
- **Last week:** Backup & archival check

### Quarterly Tasks

- **Q1, Q2, Q3, Q4:** Strategic review with stakeholders
- **Quarterly:** Performance analysis & optimization

### Annual Tasks

- **January:** Plan for year ahead
- **Renewal date:** Update compliance certifications

---

## Change Management

### Before Making Changes

**Ask These Questions:**
- Will this break existing reports/workflows?
- Do users depend on current metric definitions?
- Is this a fix or an enhancement?
- Can it wait until maintenance window?

### Small Changes (Filters, Labels)

- Owner approval: **Not required**
- Notification: Email summary after change
- Testing: Manual (open dashboard, verify)
- Rollback: Easy (restore from backup)

### Medium Changes (Adding Metrics, Changing Formulas)

- Owner approval: **Required**
- Data owner approval: **Required**
- Notification: Email stakeholders 48h before
- Testing: Full validation against source data
- Rollback: Require backup before deploying

### Large Changes (Workflow, Data Source, Architecture)

- Owner approval: **Required**
- Data owner approval: **Required**
- Stakeholder approval: **Required**
- Notification: 1 week advance notice
- Testing: Full UAT with stakeholders
- Rollback plan: Document and test before deploying

### Change Template

```markdown
## Change Request: [Name]

**Type:** [Small / Medium / Large]
**Requested By:** [Name]
**Business Justification:** [Why make this change?]
**Impact:** [Who is affected?]
**Timeline:** [When needed?]
**Risk Level:** [Low / Medium / High]

### Specific Changes
- [Change 1]
- [Change 2]

### Testing Plan
- [Test 1]
- [Test 2]

### Rollback Plan
[How to revert if needed]

### Approvals
- Owner: [ ] Approved / [ ] Rejected
- Data Owner: [ ] Approved / [ ] Rejected
- Stakeholders: [ ] Approved / [ ] Rejected
```

---

## Disaster Recovery

### Scenarios & Responses

| Scenario | Response | Owner | Timeframe |
|----------|----------|-------|-----------|
| HTML file corrupted | Regenerate from source | Dashboard Owner | 1 hour |
| Data is wrong | Investigate + rollback | Data Owner | 2 hours |
| Source database down | Use backup SINK data | Data Owner | 4 hours |
| Workflow failed | Manual refresh + alert | Dashboard Owner | 2 hours |

### Backup Verification

- **Weekly:** Check backup files exist
- **Monthly:** Restore from backup and verify integrity
- **Quarterly:** Full disaster recovery drill

---

## License & Attribution

### Dashboard License

- **Owner:** [Company/Team]
- **Created:** `<date>`
- **License Type:** [Internal Only / CC-BY / Other]

### Data License

- **Data Source:** [System/Database]
- **License:** [As per company policy / External license]
- **Restrictions:** [List any]

### Attribution

```
[Dashboard Name]
Built by: FDE TAIS Dashboard Builder
Based on: [Source data system]
Maintained by: [Team name]
Last updated: <date>
```

---

## Contact Directory

### Primary Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| Dashboard Owner | [Name] | [email] | [phone] |
| Data Owner | [Name] | [email] | [phone] |
| On-Call Engineer | [Name] | [email] | [phone] |
| Escalation | [Name] | [email] | [phone] |

### On-Call Schedule

- **Monday-Friday 9AM-5PM:** [Name]
- **Monday-Friday 5PM-9AM:** [Name]
- **Weekends/Holidays:** [Name]

### External Contacts

- **Vendor Support:** [Name / Email / Phone]
- **Legal/Compliance:** [Name / Email / Phone]

---

## Related Documentation

- **Architecture:** `architecture.md` — Technical details
- **Usage Guide:** `usage_guide.md` (public) — How to use the dashboard
- **Runbook:** `runbook.md` — Maintenance procedures

---

**Version:** 1.0.0  
**Created:** `<date>`  
**Last Modified:** `<date>`
