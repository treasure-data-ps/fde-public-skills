# HTML Dashboard Deployment Guide

**How to deploy and share HTML dashboards in different environments.**

---

> **⚠️ Read this first: the DEFAULT and RECOMMENDED path needs none of this.**
>
> `dashboard.html` is a single, fully self-contained file (Chart.js and all data inlined) — the default delivery method is simply **emailing the file or sharing it via Confluence/Drive**, and the recipient double-clicks to open it in any browser. **No server, no hosting, and no internet connection are required** for that default path.
>
> Everything below this note (Ngrok, cloud platforms, internal/Nginx servers, Confluence server-hosting) is an **optional fallback** for edge cases only — e.g., a dataset that genuinely cannot stay under the payload budget and must switch to a server-hosted `data.json` pattern (Pattern B), or a team that specifically wants a persistent shared URL instead of a file attachment. Don't reach for these options by default; only use them if the single-file approach truly doesn't fit the situation.

---

## Deployment Options Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ ENVIRONMENT DECISION TREE                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Are you developing locally?                                     │
│  ├─ YES → Localhost (Option 1)                                  │
│  │        (No setup needed, runs on your machine)               │
│  │                                                               │
│  └─ NO → Need to share/deploy?                                  │
│         ├─ Temporary sharing (days/weeks)?                      │
│         │  └─ Ngrok tunneling (Option 2)                        │
│         │     (Quick, no infrastructure)                        │
│         │                                                        │
│         ├─ Email/download sharing?                              │
│         │  └─ Self-contained HTML file (Option 3)               │
│         │     (Embed all data, no dependencies)                 │
│         │                                                        │
│         ├─ Internal team use?                                   │
│         │  └─ Internal server (Option 4)                        │
│         │     (Corporate network/VPN)                           │
│         │                                                        │
│         ├─ Public sharing / production?                         │
│         │  └─ Cloud deployment (Option 5)                       │
│         │     (Heroku, Vercel, Railway, AWS, etc.)              │
│         │                                                        │
│         └─ Documentation site?                                  │
│            └─ Embed in Confluence (Option 6)                    │
│               (Direct embed or link)                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Option 1: Localhost (Development)

**Use for:** Local testing, development, personal use

### Setup (5 minutes)

```bash
# Terminal 1: Start backend API (if using server-side filtering)
cd /tmp  # or your project directory
node api-server.js

# Terminal 2: Start HTTP server for frontend
python3 -m http.server 8000

# Terminal 3: Open in browser
open http://localhost:8000/dashboard.html
```

### Pros & Cons

✅ **Pros:**
- Instant setup (no configuration)
- Fastest (local network)
- Full control
- Perfect for development

❌ **Cons:**
- Only accessible from your machine
- API server must be running
- Can't share with others easily

---

## Option 2: Ngrok Tunneling (Temporary Sharing)

**Use for:** Quick sharing (days/weeks), demos, testing with stakeholders

### Setup (10 minutes)

1. **Install Ngrok**
   ```bash
# macOS
   brew install ngrok
   
# or download from https://ngrok.com/download
   ```

2. **Create free Ngrok account** → https://ngrok.com (optional but recommended)

3. **Start your dashboard locally**
   ```bash
# Terminal 1: Backend API
   node api-server.js
   
# Terminal 2: Frontend server
   python3 -m http.server 8000
   ```

4. **Expose to internet via Ngrok**
   ```bash
# Terminal 3: Tunnel the HTTP server
   ngrok http 8000
   
# Output:
# Forwarding https://abc123.ngrok.io -> http://localhost:8000
   ```

5. **Share the URL**
   ```
   Share: https://abc123.ngrok.io/dashboard.html
   Valid for: 8 hours (free tier) or indefinitely (paid)
   ```

### Pros & Cons

✅ **Pros:**
- No infrastructure setup
- Instant public URL
- Works anywhere
- Great for demos/stakeholder feedback

❌ **Cons:**
- URL changes each time (free tier)
- Limited session (8 hours free)
- API must be running
- Not suitable for production

### Ngrok Tunnel Example

```bash
# Terminal 1: Backend
$ node api-server.js
🚀 Travel Dashboard API running on http://localhost:3001

# Terminal 2: Frontend
$ python3 -m http.server 8000
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...

# Terminal 3: Expose
$ ngrok http 8000

ngrok by @inconshreveable                                    (Ctrl+C to quit)

Build better APIs with ngrok. Early access to ngrok 3 is now available!
Try new ngrok 3 at https://ngrok.com/ngrok3 (requires a login)

Session Status    online
Account           user@example.com (Plan: Free)
Version           2.3.40
Region            us-west
Web Interface     http://127.0.0.1:4040
Forwarding        https://abc123.ngrok.io -> http://localhost:8000

Connections       ttl     opn     rt1     rt5     p50     p95
                  0       0       0.00    0.00    0.00    0.00

# Share: https://abc123.ngrok.io/dashboard.html
```

---

## Option 3: Self-Contained HTML File (Email/Download)

**Use for:** Email sharing, download links, portable dashboards

### Requirements

- Small dataset (< 10K rows typically)
- Client-side filtering OR pre-computed data
- No backend API needed

### Implementation

```html
<!DOCTYPE html>
<html>
<head>
  <title>Sales Dashboard</title>
  <!-- Chart.js is inlined directly (no CDN) so the file works fully offline — see templates/*.html for the actual inlined <script> block -->
  <style>/* CSS */</style>
</head>
<body>
  <!-- Filters -->
  <div class="filters">
    <select id="regionFilter" onchange="filterData()">
      <option value="all">All Regions</option>
      <option value="North">North</option>
      <option value="South">South</option>
    </select>
  </div>
  
  <!-- Dashboard content -->
  <div id="charts"></div>
  
  <script>
    // Embed data directly (no API calls)
    const DATA = [
      { region: 'North', revenue: 100000, customers: 50 },
      { region: 'South', revenue: 150000, customers: 75 }
    ];
    
    function filterData() {
      const region = document.getElementById('regionFilter').value;
      const filtered = region === 'all' 
        ? DATA 
        : DATA.filter(d => d.region === region);
      renderCharts(filtered);
    }
    
    // Filter logic on client-side only
    function renderCharts(data) {
      // Update charts with filtered data
    }
    
    // Initialize
    filterData();
  </script>
</body>
</html>
```

### Sharing

```bash
# Option A: Email as attachment
zip dashboard.html
# Send: dashboard.html.zip to user@example.com
# User: Download, unzip, open in browser

# Option B: Host on file sharing service
# Upload: dashboard.html to Dropbox, Google Drive, etc.
# Share: Public link to users

# Option C: Save to internal file server
cp dashboard.html /shared/dashboards/sales-dashboard.html
# Users: Open from network share
```

### Pros & Cons

✅ **Pros:**
- Single file (easy to share)
- No server needed
- Fast (no API calls)
- Works offline
- Email-friendly

❌ **Cons:**
- Limited to small datasets
- Can't query live database
- Hard to update data
- No real-time updates

---

## Option 4: Internal Server (Corporate Network)

**Use for:** Team access, internal tools, private dashboards

### Setup (30 minutes)

#### A. Simple HTTP Server (Development)

```bash
# Copy dashboard to shared location
cp dashboard.html /path/to/internal/webserver/

# Access: http://internal-server.company.com/dashboards/dashboard.html
```

#### B. Node.js Server (Production-like)

```bash
# Production-ready setup

# 1. Copy to server
scp -r dashboard-api/ server@internal.company.com:/opt/dashboards/

# 2. SSH to server
ssh server@internal.company.com

# 3. Install dependencies
cd /opt/dashboards
npm install

# 4. Start with systemd (auto-restart on reboot)
sudo systemctl start dashboard-api
sudo systemctl enable dashboard-api

# 5. Configure Nginx reverse proxy (optional, for HTTPS)
# (See Nginx config below)

# 6. Access: https://dashboards.company.com/dashboard.html
```

#### Nginx Configuration (HTTPS)

```nginx
# /etc/nginx/sites-available/dashboards

upstream dashboard_api {
  server localhost:3001;
}

server {
  listen 443 ssl http2;
  server_name dashboards.company.com;
  
  ssl_certificate /etc/ssl/certs/dashboard.crt;
  ssl_certificate_key /etc/ssl/private/dashboard.key;
  
  location / {
    root /opt/dashboards/public;
    try_files $uri $uri/ =404;
  }
  
  location /api/ {
    proxy_pass http://dashboard_api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}

# Enable
sudo ln -s /etc/nginx/sites-available/dashboards /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Systemd Service File

```ini
# /etc/systemd/system/dashboard-api.service

[Unit]
Description=Dashboard API Server
After=network.target

[Service]
Type=simple
User=dashboards
WorkingDirectory=/opt/dashboards
ExecStart=/usr/bin/node /opt/dashboards/api-server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Access Control (VPN/Firewall)

```bash
# Option A: VPN-only access
# - Deploy on internal network
# - Require VPN connection to access
# - No firewall rules needed

# Option B: IP whitelist
# - Allow only specific IP ranges
# - Configure in firewall/security group

# Option C: Authentication
# - Add login (see Auth section below)
# - Prevent unauthorized access
```

### Adding Authentication (Optional)

```javascript
// api-server.js with basic auth

const basicAuth = (req, res, next) => {
  const auth = req.headers.authorization;
  
  if (!auth) {
    res.status(401).set('WWW-Authenticate', 'Basic realm="Dashboard"').json({ error: 'Unauthorized' });
    return;
  }
  
  const [scheme, credentials] = auth.split(' ');
  if (scheme !== 'Basic') {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }
  
  const [username, password] = Buffer.from(credentials, 'base64').toString().split(':');
  
  if (username === 'admin' && password === 'secret123') {
    next();
  } else {
    res.status(401).json({ error: 'Unauthorized' });
  }
};

// Apply to all API routes
app.use('/api/', basicAuth);
```

### Pros & Cons

✅ **Pros:**
- Full control
- Persistent (always available)
- Scalable
- Can handle large datasets
- Authentication/access control

❌ **Cons:**
- Requires infrastructure
- Setup complexity
- Maintenance burden
- Cost (hosting)

---

## Option 5: Cloud Deployment (Production)

**Use for:** Production dashboards, public sharing, scalability

### A. Heroku (Easiest)

```bash
# 1. Install Heroku CLI
brew install heroku

# 2. Login
heroku login

# 3. Create app
heroku create dashboard-sales

# 4. Add Procfile
cat > Procfile << 'EOF'
web: node api-server.js
EOF

# 5. Commit to git
git add Procfile
git commit -m "Add Heroku Procfile"

# 6. Deploy
git push heroku main

# 7. Access
# https://dashboard-sales.herokuapp.com
```

### B. Vercel (React/Node-friendly)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
vercel

# 3. Follow prompts
# → Select project directory
# → Select framework (Node.js)
# → Confirm settings

# 4. Access
# https://dashboard-sales.vercel.app
```

### C. Railway (Modern alternative)

```bash
# 1. Connect GitHub
# → Go to railway.app
# → Connect GitHub account
# → Select repository

# 2. Add environment variables
# → Set any needed env vars (API keys, etc.)

# 3. Deploy
# → Railway auto-deploys on git push

# 4. Access
# → https://dashboard-sales.up.railway.app
```

### D. AWS/Azure/GCP (Enterprise)

```bash
# AWS example (simplified)

# 1. Create EC2 instance
aws ec2 run-instances --image-id ami-0c55b159cbfafe1f0 --instance-type t2.micro

# 2. SSH to instance
ssh -i key.pem ec2-user@instance-ip

# 3. Install Node.js
sudo yum install nodejs

# 4. Clone & setup
git clone https://github.com/yourrepo/dashboards.git
cd dashboards && npm install

# 5. Start with PM2 (process manager)
npm install -g pm2
pm2 start api-server.js
pm2 startup
pm2 save

# 6. Setup Nginx (reverse proxy)
# (See Nginx config in Option 4)

# 7. Get SSL certificate (Let's Encrypt)
sudo certbot certonly --standalone -d dashboards.yourdomain.com

# 8. Access
# https://dashboards.yourdomain.com
```

### Pros & Cons

✅ **Pros:**
- Always available
- Scales automatically
- HTTPS/SSL included
- Monitoring/logging
- Professional

❌ **Cons:**
- Monthly cost ($5-500+)
- More complex setup
- Potential vendor lock-in

---

## Option 6: Embed in Confluence

**Use for:** Documentation sites, internal knowledge bases

### A. Direct HTML Embed (Confluence Cloud)

```
1. Dashboard menu → [⋯ More] → HTML macro
2. Paste dashboard HTML into macro
3. Save page

Result: Dashboard renders in Confluence page
```

### B. IFrame Embed

```html
<!-- Confluence page HTML (via editor) -->

<ac:structured-macro ac:name="html">
  <ac:plain-text-body>
    <![CDATA[
    <iframe 
      src="https://dashboards.company.com/dashboard.html"
      width="100%" 
      height="800"
      style="border: none;">
    </iframe>
    ]]>
  </ac:plain-text-body>
</ac:structured-macro>
```

### C. Link to External Dashboard

```markdown
## Dashboard

[Open Sales Dashboard →](https://dashboards.company.com)

Or embed in Confluence page (see above)
```

### Pros & Cons

✅ **Pros:**
- Easy documentation
- Centralized (with other docs)
- No separate tool

❌ **Cons:**
- Limited customization
- Confluence-dependent
- May need special permissions

---

## Comparison: All Options

| Option | Setup Time | Cost | Access | Scalability | Best For |
|--------|-----------|------|--------|-------------|----------|
| **Localhost** | 2 min | Free | Local only | Single user | Development |
| **Ngrok** | 5 min | Free | Temporary | Limited | Demos, testing |
| **Self-contained HTML** | 10 min | Free | Email/download | Limited | Simple sharing |
| **Internal Server** | 30 min | Low | Team (VPN) | High | Internal tools |
| **Cloud** | 20 min | $5-500/mo | Public | Very high | Production |
| **Confluence** | 5 min | Included | Docs site | N/A | Documentation |

---

## Decision Matrix

```
Quick demo for stakeholder?           → Ngrok
Send via email?                        → Self-contained HTML
Internal team (1-100 people)?          → Internal Server
Production (many users)?               → Cloud
Share in documentation?                → Confluence
Just testing locally?                  → Localhost
```

---

## Deployment Checklist

Before deploying, verify:

- [ ] Dashboard passes all 95 tests (see ../../testing-troubleshooting.md)
- [ ] All data is accurate (spot-checked 5+ metrics)
- [ ] All filters work (alone, pairs, all together)
- [ ] Performance acceptable (< 1s filter updates)
- [ ] HTTPS enabled (if public)
- [ ] Authentication configured (if needed)
- [ ] Monitoring/logging enabled (if production)
- [ ] Backup strategy (if persistent data)
- [ ] Documentation for users

---

## Security Considerations

### If Public (Cloud Deployment)

- [ ] Use HTTPS (SSL certificate)
- [ ] Add authentication (username/password or OAuth)
- [ ] Rate limit API endpoints
- [ ] Validate all user input
- [ ] Use secrets for API keys (environment variables)
- [ ] Enable CORS carefully (don't allow `*` from unknown origins)
- [ ] Monitor for attacks

### If Internal (Corporate)

- [ ] Use VPN for access
- [ ] IP whitelist if possible
- [ ] Basic authentication (username/password)
- [ ] HTTPS encouraged
- [ ] Logging for audit trail

### Code

```javascript
// api-server.js security hardening

const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

app.use(helmet()); // Security headers
app.use(cors({
  origin: 'https://dashboards.company.com',
  credentials: true
})); // Restrict CORS

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // Limit each IP to 100 requests per window
});

app.use('/api/', limiter); // Rate limiting
```

---

## Troubleshooting

### Dashboard loads but no data shows

**Possible causes:**
1. Backend API not running
2. Database connection error
3. CORS misconfigured
4. Query error

**Fix:**
```bash
# Check backend logs
tail -f /var/log/dashboard-api.log

# Check network tab in browser DevTools
# Look for failed API calls (red)

# Test API directly
curl http://localhost:3001/api/kpis
```

### API returns 404 on filter change

**Possible causes:**
1. Endpoint not defined
2. Wrong URL in frontend
3. API server restarted

**Fix:**
```javascript
// frontend check
console.log('API URL:', API_BASE);
console.log('Making request to:', `${API_BASE}/kpis?status=all`);

// backend check
app.get('/api/kpis', (req, res) => {
  console.log('KPIs endpoint called');
  res.json({...});
});
```

### Performance is slow

**Possible causes:**
1. Large dataset
2. Complex query
3. Network latency
4. No caching

**Fix:**
- Optimize database queries
- Use pagination for large tables
- Monitor API response times

---

## Next Steps

1. **Choose deployment option** (use decision matrix above)
2. **Follow setup instructions** for your option
3. **Test dashboard** in new environment
4. **Verify all filters work** (run testing checklist)
5. **Share URL/access** with users
6. **Monitor** usage and performance

---

## Related Documentation

- `html-dashboard-patterns.md` - UI/UX patterns
- `../../testing-troubleshooting.md` - Quality validation

---

## Performance Optimization: Enable Gzip Compression

**Impact:** Dashboard HTML typically compresses to **60–70 KB** (87% reduction) due to highly repetitive JSON data and CSS/JS.

### With `npx serve`:

```bash
# Enable compression with --compress flag
npx serve --compress ./<project-name>/dashboards/

# Result: dashboard.html transferred as gzip (87% smaller)
# Browser automatically decompresses on load
```

### With nginx:

```nginx
server {
    gzip on;
    gzip_types text/html application/json text/javascript text/css;
    gzip_min_length 1024;  # Only compress > 1 KB
    
    location / {
        root /path/to/dashboards;
    }
}
```

### Local testing (no compression needed):

```bash
# Single file — no server
open file:///path/to/dashboard.html

# Or simple http-server
python3 -m http.server 8000
# Then visit http://localhost:8000/dashboard.html
```

**When it matters:**
- Dashboard served over network (production, shared servers)
- Dashboard HTML > 100 KB before compression
- Network latency is a bottleneck (mobile, remote users)

**When it doesn't matter:**
- Local file (file:// protocol)
- Small dashboards (< 100 KB)
- Fast local network




---

## Offline Capability (Built-In)

✅ **All dashboard templates include Chart.js inline** — they work completely offline with zero external dependencies.

No CDN calls. No internet required. Single self-contained `.html` file.

---

---

**Version:** 1.0.0
**Last Updated:** 15 July 2026
**Author:** FDE Team
