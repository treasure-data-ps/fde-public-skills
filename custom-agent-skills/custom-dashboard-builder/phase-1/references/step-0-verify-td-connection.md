# Step 0: Verify Treasure Data Connection

**Run FIRST — before anything else in Phase 1.**

**Why:** Phase 1 requires direct database access via `tdx` CLI to discover tables, validate metrics, and run test queries. If TD auth is not set up or has expired, all discovery steps will fail with 401/403 errors mid-workflow. Fail fast here.

**Estimated time:** 30 seconds

---

## Verify tdx CLI is installed and authenticated

Run this command:

```bash
tdx databases
```

**Expected output:**
```
+---------------------+
| Name                |
+---------------------+
| your_database_name  |
| another_database    |
+---------------------+
```

**If it succeeds:** ✅ Continue to Session Setup.

**If it fails:**

| Error | Likely Cause | How to Fix |
|-------|---|---|
| `command not found: tdx` | tdx CLI not installed | Install via `brew install td-client` (macOS) or [follow the guide](https://docs.treasuredata.com/display/public/PY/TD+CLI+Installation) |
| `Authentication failed` / `401` | Not authenticated to Treasure Data | Run `tdx auth setup` and follow the prompts to add your API key |
| `Invalid API key` / `403` | API key expired or revoked | Go to Treasure Data console, regenerate your API key, and run `tdx auth setup` again |
| `Cannot connect` / timeout | Network issue or wrong endpoint | Check if you're behind a firewall; if EU account, set `export TD_CLI_ENDPOINT=api.eu01.treasuredata.com` |

Once you've fixed the error, re-run `tdx databases` to confirm success.

---

## Record in Session

Once verified:

```
✅ TD connection confirmed: [record the output of tdx databases]
```

Proceed to Session Setup questions (Batch 1 in the main guide).

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
