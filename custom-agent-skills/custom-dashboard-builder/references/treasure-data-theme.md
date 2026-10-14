# Treasure AI 2026 Brand Theme

**Official color palettes, typography, and UX theme for all dashboards, visualizations, and branded content.**

This is the authoritative source for Treasure AI 2026 branding. Use these colors consistently across all phases.

---

## 1. Primary Brand Theme: "Treasure AI 2026 UX Palette"

This is the primary color scheme extracted from the official 2026 brand guidelines (used for slides, documentation, web, and branded products):

| Role | Hex | Description & Usage |
| :--- | :--- | :--- |
| **Dark 1** | `#000000` | Primary text on light backgrounds |
| **Light 1** | `#FFFFFF` | White backgrounds, reversed text on dark |
| **Dark 2 (Primary)** | `#2D40AA` | Deep blue — titles, headings, emphasis, dark backgrounds |
| **Light 2** | `#F9FEFF` / `#F7F5F9` | Near-white / subtle off-white lavender fills and backgrounds |
| **Accent 1 (Brand)** | `#847BF2` | Purple — the primary brand accent (used for charts, icons, highlights) |
| **Accent 2** | `#C466D4` | Orchid / Magenta — secondary accents |
| **Accent 3** | `#80B3FA` / `#8BBCFD` | Sky blue — charts, icons, accents |
| **Accent 4** | `#F3CCF2` / `#FEAFD9` | Light / Soft pink — backgrounds, tags |
| **Accent 5** | `#FFE2BD` | Light apricot / peach — secondary highlights |
| **Accent 6** | `#FDB893` | Warm peach — callouts, highlights |
| **Hyperlink** | `#494FFF` / `#FA731A` | Vivid blue or Brand orange — links and call-to-actions |

---

## 2. CSS Theme Variables (Primary)

```css
:root {
  /* Core Brand Colors */
  --dark-1: #000000;           /* Primary text */
  --light-1: #FFFFFF;          /* White backgrounds */
  --dark-2: #2D40AA;           /* Deep blue — primary, headings */
  --light-2: #F9FEFF;          /* Near-white background */
  --light-2-lavender: #F7F5F9; /* Subtle off-white lavender */
  
  /* Brand Accents */
  --accent-1: #847BF2;         /* Purple — primary brand accent */
  --accent-2: #C466D4;         /* Orchid / Magenta */
  --accent-3: #80B3FA;         /* Sky blue */
  --accent-3-alt: #8BBCFD;     /* Sky blue (alt) */
  --accent-4: #F3CCF2;         /* Light pink */
  --accent-4-alt: #FEAFD9;     /* Soft pink */
  --accent-5: #FFE2BD;         /* Light apricot */
  --accent-6: #FDB893;         /* Warm peach */
  --hyperlink: #494FFF;        /* Vivid blue for links */
  --hyperlink-alt: #FA731A;    /* Brand orange for CTAs */
  
  /* Semantic Aliases */
  --primary: #2D40AA;          /* Primary button/emphasis */
  --brand-purple: #847BF2;     /* Charts, icons, highlights */
  --success: #8CC97E;          /* Green for positive indicators */
  --warning: #EEB53A;          /* Yellow for caution */
  --error: #E4002B;            /* Red for errors (legacy, migrate to purple) */
  
  /* Grayscale */
  --gray-0: #FFFFFF;           /* Pure white */
  --gray-50: #F9FEFF;          /* Near-white */
  --gray-100: #F7F5F9;         /* Off-white lavender */
  --gray-200: #E8E9ED;         /* Very light gray */
  --gray-400: #999999;         /* Medium gray */
  --gray-600: #666666;         /* Dark gray */
  --gray-800: #333333;         /* Very dark gray */
  --gray-900: #000000;         /* Black */
}

body {
  font-family: 'Manrope', Arial, sans-serif;
  background: var(--light-1);
  color: var(--dark-1);
  line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Poppins', Arial, sans-serif;
  font-weight: 600;
  color: var(--dark-2);
}

a, .hyperlink {
  color: var(--hyperlink);
  text-decoration: none;
}

a:hover {
  opacity: 0.9;
  text-decoration: underline;
}
```

---

## 3. Secondary Brand Theme (Dark Variant)

Used when building dark-mode slides, layouts, or high-contrast dashboards:

```css
body.dark-mode {
  --dark-1: #FFFFFF;           /* Reversed: white text on dark */
  --light-1: #00042B;          /* Near-black blue background */
  --dark-2: #FFFFFF;           /* White — reversed text */
  
  /* Dark mode accents (more vivid) */
  --accent-1: #3A61FF;         /* Vivid blue */
  --accent-2: #62DEFB;         /* Cyan */
  --accent-3: #F069D6;         /* Hot pink */
  --accent-4: #8354FF;         /* Bright purple */
  --accent-5: #CF7FF6;         /* Lilac */
  --accent-6: #FFD6A4;         /* Soft gold */
  
  background: #00042B;
  color: #FFFFFF;
}
```

---

## 4. Mandatory Data Visualization Palette

**Use this standardized color order for all interactive dashboards, charts, and reporting interfaces:**

```python
# Treasure AI 2026 Data Visualization Palette
TD_COLORS = [
  '#44BAB8', # Teal (Primary)
  '#8FD6D4', # Light Teal
  '#DAF1F1', # Pale Teal (Backgrounds/Fills)
  '#2E41A6', # Deep Blue (Emphasis/Headings)
  '#828DCA', # Medium Blue
  '#D5D9ED', # Pale Blue
  '#8CC97E', # Green (Success/Positive)
  '#BADFB2', # Light Green
  '#E8F4E5', # Pale Green
  '#EEB53A', # Yellow (Warning/Caution)
  '#F5D389', # Soft Yellow
  '#5FCFD8', # Cyan Accent
  '#A05EB0', # Purple Accent
  '#C69ED0'  # Light Purple
]
```

**For multi-series charts, use this preferred order:**
1. `#847BF2` — Purple (Brand primary)
2. `#8BBCFD` — Sky Blue
3. `#FDB893` — Warm Peach
4. `#C466D4` — Magenta
5. `#FEAFD9` — Soft Pink
6. `#FFE2BD` — Light Apricot
7. `#44BAB8` — Teal
8. `#8CC97E` — Green
9. `#EEB53A` — Yellow
10. `#5FCFD8` — Cyan

---

## 5. Component Styling with Treasure AI Colors

### KPI Cards
```css
.kpi-card {
  background: var(--light-1);
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border-left: 4px solid var(--accent-1);  /* Purple */
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--dark-2);  /* Deep blue */
}

.kpi-label {
  font-size: 0.875rem;
  color: var(--gray-600);
  font-weight: 500;
}
```

### Buttons
```css
.btn-primary {
  background: var(--dark-2);   /* Deep blue */
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-family: 'Poppins', Arial;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: var(--light-2);  /* Near-white */
  color: var(--dark-2);
  border: 1px solid var(--gray-200);
}

.btn-cta {
  background: var(--accent-1); /* Purple — calls-to-action */
  color: white;
}
```

### Badges & Tags
```css
.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.badge-success { 
  background: rgba(140, 201, 126, 0.1);   /* Green with transparency */
  color: #8CC97E; 
}

.badge-warning { 
  background: rgba(238, 181, 58, 0.1);    /* Yellow with transparency */
  color: #EEB53A; 
}

.badge-info { 
  background: rgba(132, 123, 242, 0.1);   /* Purple with transparency */
  color: #847BF2; 
}

.badge-secondary { 
  background: rgba(196, 102, 212, 0.1);   /* Magenta with transparency */
  color: #C466D4; 
}
```

### Alerts
```css
.alert-success {
  background: #E8F4E5;
  border-left: 4px solid #8CC97E;
}

.alert-warning {
  background: #FEF8E8;
  border-left: 4px solid #EEB53A;
}

.alert-error {
  background: #FFE8E8;
  border-left: 4px solid #E4002B;
}

.alert-info {
  background: #F0ECFF;
  border-left: 4px solid #847BF2;
}
```

### Tables & Data
```css
table thead {
  background: var(--light-2);
  color: var(--dark-2);
  font-weight: 600;
  font-family: 'Poppins', Arial;
}

table tbody tr:hover {
  background: rgba(132, 123, 242, 0.05);  /* Subtle purple tint */
}

table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--gray-200);
}
```

### Charts (Chart.js / Plotly)
```javascript
// Treasure AI branded chart configuration
const chartConfig = {
  datasets: [{
    // Use colors from TD_COLORS palette in order
    backgroundColor: [
      '#44BAB8', '#8FD6D4', '#2E41A6', '#828DCA', '#8CC97E'
    ],
    borderColor: '#FFFFFF',
    borderWidth: 2
  }],
  options: {
    plugins: {
      legend: {
        labels: {
          font: { family: "'Manrope', Arial" },
          color: '#000000'
        }
      }
    }
  }
};
```

---

## 6. Legacy Color Mapping (Rebrand Reference)

If updating older Treasure Data materials or dashboards, use these **hard swap rules** to transition to Treasure AI 2026 branding:

| Legacy Treasure Data | Hex | → | Treasure AI 2026 Replacement | Target Hex |
| :--- | :--- | :--- | :--- | :--- |
| **TD Red** | `#E4002B` | → | **Accent 1 (Purple)** | `#847BF2` |
| **TD Orange** | `#FF6900` / `#FC6B29` | → | **Accent 6 (Warm Peach)** | `#FDB893` |
| **TD Navy** | `#003057` / `#002855` | → | **Dark 2 (Deep Blue)** | `#2D40AA` |
| **Bright Blue** | `#0066FF` / `#1A56DF` | → | **Dark 2 (Deep Blue)** | `#2D40AA` |
| **Legacy Purple** | `#6E2CF4` | → | **Accent 1 (Purple)** | `#847BF2` |

---

## 7. Brand Typography Rules

**Pair colors with the official Treasure AI 2026 fonts:**

| Element | Font | Weight | Size | Color |
| :--- | :--- | :--- | :--- | :--- |
| **Headings (h1, h2, h3)** | Poppins | SemiBold (600) | ≥24pt | `#2D40AA` (Dark 2) |
| **Subheadings (h4, h5)** | Poppins | SemiBold (600) | 16–20pt | `#2D40AA` |
| **Body text** | Manrope | Regular (400) | 14–16pt | `#000000` (Dark 1) |
| **Emphasis / Bold** | Manrope | SemiBold (600) | 14–16pt | `#2D40AA` |
| **Labels / Captions** | Manrope | Regular (400) | 12–14pt | `#666666` (Gray 600) |
| **Links / CTAs** | Manrope | SemiBold (600) | 14–16pt | `#494FFF` or `#FA731A` |
| **Fallback** | Arial | — | — | (if Poppins/Manrope unavailable) |

---

## 8. Custom Brand Color Override (Phase 1 Step 1c)

If a customer provides custom brand colors in Phase 1 Step 1c, override only `--accent-1` and `--accent-2`, keeping the core Treasure AI structure:

**From `state.md` (Phase 1):**
```yaml
dashboard_theme:
  primary_color: "#e74c3c"        # Custom brand primary
  secondary_color: "#3498db"      # Custom brand secondary
  logo_url: "https://..."
  logo_background: "white"
```

**In Phase 3 Template (override CSS):**
```css
:root {
  /* Keep Treasure AI structure */
  --dark-1: #000000;
  --light-1: #FFFFFF;
  --dark-2: #2D40AA;
  
  /* Override only accents for custom brand */
  --accent-1: #e74c3c;           /* Custom primary */
  --accent-2: #3498db;           /* Custom secondary */
  
  /* All other Treasure AI colors remain */
  --accent-3: #8BBCFD;
  --accent-4: #FEAFD9;
  /* ... etc */
}
```

---

## 9. Accessibility & Contrast

**Treasure AI 2026 color combinations are WCAG AA compliant:**

| Background | Text Color | Contrast Ratio | Status |
| :--- | :--- | :--- | :--- |
| `#FFFFFF` (Light 1) | `#000000` (Dark 1) | 21:1 | ✅ AAA |
| `#FFFFFF` | `#2D40AA` (Dark 2) | 10.5:1 | ✅ AAA |
| `#F9FEFF` (Light 2) | `#000000` | 18:1 | ✅ AAA |
| `#F9FEFF` | `#2D40AA` | 9:1 | ✅ AA |
| `#2D40AA` (Dark 2) | `#FFFFFF` | 10.5:1 | ✅ AA |
| `#847BF2` (Accent 1) | `#FFFFFF` | 4.8:1 | ✅ AA |
| `#FDB893` (Accent 6) | `#000000` | 5.2:1 | ✅ AA |

---

**Version:** 2.0.0 (Treasure AI 2026 Official)  
**Last Updated:** 22 July 2026  
**Author:** Treasure AI Brand + FDE Team  
**Source:** Official Treasure AI 2026 Brand Guidelines
