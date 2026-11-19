#!/usr/bin/env node
/**
 * NBA AI Signal (Next Best Action) Dashboard Data Generator.
 *
 * Runs the dashboard queries concurrently against the NBA AI Signal outputs (fixed-name
 * nba_ais_* tables + the recommendations table), derives the template values, and writes
 * a standalone HTML dashboard.
 *
 * Usage:
 *   node generate-data.js <sink_database> [project_slug] [project_name] [-P <pred_output_table>]
 *   SOURCE_DB=<sink_database> node generate-data.js [project_slug] [project_name]
 *
 * Output (default): ./agent_outputs/<project_slug>/dashboards/nba_ai_signal_dashboard.html
 *   relative to the current working directory — run it from the user's working directory.
 */

const fs = require('fs');
const path = require('path');

// Resolve the user's working directory: if run from inside agent_outputs/ (e.g. a workflow copy),
// step back out so dashboards never land in a nested agent_outputs/.
const workRoot = (() => {
  const parts = process.cwd().split(path.sep);
  const i = parts.lastIndexOf('agent_outputs');
  return i > 0 ? (parts.slice(0, i).join(path.sep) || path.sep) : process.cwd();
})();

const { exec } = require('child_process');

const args = process.argv.slice(2);
let customOutput = null;
let customTemplate = null;
let customPredTable = null;
let verbose = false;
const positional = [];

function help() {
  console.log(`
NBA AI Signal Dashboard Data Generator

Usage:
  node generate-data.js <sink_database> [project_slug] [project_name] [-P <pred_output_table>]
  SOURCE_DB=<sink_database> node generate-data.js [project_slug] [project_name]

Arguments:
  sink_database         Treasure Data database with the nba_ais_* tables and the recommendations (required, or env SOURCE_DB)
  project_slug          Project slug, names the output folder (default: "nba-ai-signal")
  project_name          Project display name in the dashboard header (default: Title-cased slug)

Options:
  -P, --pred-table      Recommendations table, the workflow's pred_output_table (default: nba_ais_actions or env PRED_TABLE)
  -o, --output          Custom output HTML path
                        (default: ./agent_outputs/<project_slug>/dashboards/nba_ai_signal_dashboard.html)
  -t, --template        Dashboard template path
  -v, --verbose         Show query timings and row counts
  -h, --help            Show this help
`);
  process.exit(process.exitCode || 0);
}

for (let i = 0; i < args.length; i += 1) {
  const arg = args[i];
  if (arg === '-h' || arg === '--help') help();
  else if (arg === '-P' || arg === '--pred-table') customPredTable = args[++i];
  else if (arg === '-o' || arg === '--output') customOutput = args[++i];
  else if (arg === '-t' || arg === '--template') customTemplate = args[++i];
  else if (arg === '-v' || arg === '--verbose') verbose = true;
  else if (!arg.startsWith('-')) positional.push(arg);
}

let sinkDatabase = process.env.SOURCE_DB || '';
let projectSlug = process.env.PROJECT_SLUG || '';
let projectName = process.env.PROJECT_NAME || '';
const predTable = customPredTable || process.env.PRED_TABLE || 'nba_ais_actions';

if (positional.length > 0) {
  if (!sinkDatabase) {
    sinkDatabase = positional[0];
    if (positional[1]) projectSlug = positional[1];
    if (positional[2]) projectName = positional[2];
  } else {
    projectSlug = positional[0];
    if (positional[1]) projectName = positional[1];
  }
}

function validIdentifier(value, label) {
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(value)) {
    throw new Error(`Invalid ${label}: "${value}"`);
  }
  return value;
}

if (!sinkDatabase) {
  console.error('Error: sink_database is required (first argument or SOURCE_DB env var).');
  process.exitCode = 1;
  help();
}
validIdentifier(sinkDatabase, 'sink database');
validIdentifier(predTable, 'recommendations table');
projectSlug = projectSlug || 'nba-ai-signal';
projectName = projectName || projectSlug.split(/[-_]/).filter(Boolean).map(w => w[0].toUpperCase() + w.slice(1)).join(' ');

const scriptDir = __dirname;
const templatePath = customTemplate
  ? path.resolve(process.cwd(), customTemplate)
  : path.join(scriptDir, 'dashboard_template.html');
const outputDir = path.resolve(workRoot, 'agent_outputs', projectSlug, 'dashboards');
const outputPath = customOutput
  ? path.resolve(process.cwd(), customOutput)
  : path.join(outputDir, 'nba_ai_signal_dashboard.html');

if (!fs.existsSync(templatePath)) throw new Error(`Template not found: ${templatePath}`);

function query(sql, description) {
  return new Promise(resolve => {
    const clean = sql.replace(/\s+/g, ' ').trim();
    const escaped = clean.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    const command = `tdx query -d ${sinkDatabase} --format json "${escaped}"`;
    const started = Date.now();
    exec(command, { maxBuffer: 50 * 1024 * 1024 }, (error, stdout) => {
      const elapsed = Date.now() - started;
      if (error) {
        if (verbose) console.warn(`  [Notice] ${description} failed (${elapsed}ms): ${error.message}`);
        return resolve([]);
      }
      try {
        const start = stdout.indexOf('[');
        const end = stdout.lastIndexOf(']');
        const rows = start >= 0 && end > start ? JSON.parse(stdout.slice(start, end + 1)) : [];
        if (verbose) console.log(`  ✔ ${description}: ${rows.length} rows (${elapsed}ms)`);
        resolve(rows);
      } catch (err) {
        if (verbose) console.warn(`  [Notice] ${description} returned invalid JSON (${elapsed}ms)`);
        resolve([]);
      }
    });
  });
}

function n(value) {
  if (value === null || value === undefined || value === '') return 0;
  const result = Number(value);
  return Number.isFinite(result) ? result : 0;
}
function has(value) { return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value)); }
function integer(value) { return Math.round(n(value)).toLocaleString('en-US'); }
function decimal(value, places = 4) { return has(value) ? n(value).toFixed(places) : '—'; }
function pct(value) { return `${(n(value) * 100).toFixed(1)}%`; }
function signedPct(value) { return has(value) ? `${n(value) >= 0 ? '+' : ''}${n(value).toFixed(1)}%` : '—'; }
function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function json(value) { return JSON.stringify(value).replace(/</g, '\\u003c'); }
function pill(kind, text) { return `<span class="pill ${kind}">${escapeHtml(text)}</span>`; }

async function run() {
  const started = Date.now();
  const db = sinkDatabase;
  const pred = `${db}.${predTable}`;
  const history = `${db}.${predTable}_history`;
  // Every nba_ais_* log is appended on each run: the latest run is the latest session_id by time.
  const latestStats = `(SELECT max_by(session_id, time) FROM ${db}.nba_ais_action_stats)`;
  const latestTuning = `(SELECT max_by(run_id, time) FROM ${db}.nba_ais_tuning_results)`;

  const [q1, q2, q3, q4, q5, q6] = await Promise.all([
    query(`SELECT session_id, run_date, nba_type, time_grain, model_name, model_type, enable_tuning, train_rows, train_users, n_actions, logged_avg_reward, estimated_policy_value, ci_lower, ci_upper, estimated_lift_pct, reward_window_days, train_window_days, feature_lookback_days FROM ${db}.nba_ais_run_log ORDER BY time DESC LIMIT 1`, 'Q1 latest training run'),
    query(`SELECT session_id, run_date, logged_avg_reward, estimated_policy_value, ci_lower, ci_upper FROM ${db}.nba_ais_run_log ORDER BY time ASC`, 'Q2 training history'),
    query(`SELECT action, logged_rows, logged_share, logged_avg_reward, recommended_users, recommended_share FROM ${db}.nba_ais_action_stats WHERE session_id = ${latestStats} ORDER BY recommended_users DESC, logged_rows DESC`, 'Q3 action mix'),
    query(`SELECT COUNT(*) AS customers, COUNT(DISTINCT next_best_action) AS actions_recommended, MAX(scored_date) AS scored_date, arbitrary(session_id) AS pred_session_id FROM ${pred}`, 'Q4 latest recommendations'),
    query(`SELECT * FROM ${db}.nba_ais_tuning_results WHERE run_id = ${latestTuning} AND LOWER(CAST(is_best AS VARCHAR)) = 'true'`, 'Q5 tuning best trials'),
    query(`SELECT session_id, MIN(scored_date) AS scored_date, MIN(time) AS t, next_best_action, COUNT(*) AS customers FROM ${history} GROUP BY session_id, next_best_action ORDER BY 3`, 'Q6 scoring history')
  ]);

  if (!q1.length) throw new Error(`No records found in ${db}.nba_ais_run_log. Verify the NBA AI Signal workflow has completed.`);
  const runRow = q1[0];
  const recs = q4[0] || {};
  const logged = n(runRow.logged_avg_reward);
  const value = n(runRow.estimated_policy_value);
  const lower = n(runRow.ci_lower);
  const upper = n(runRow.ci_upper);
  const tuned = String(runRow.enable_tuning || '').toLowerCase() === 'true';

  const evidencePill = !has(runRow.estimated_policy_value) ? pill('warn', 'No estimate')
    : lower > logged ? pill('ok', 'Confident improvement')
    : value >= logged ? pill('warn', 'Likely, not proven')
    : pill('error', 'No improvement');

  // Tuning: one best row per phase; chosen settings are whichever phase*_ columns exist
  const phaseOrder = ['baseline_random', 'phase0_preprocessing', 'phase1_ope', 'phase2_policy'];
  const tuningRows = q5.slice().sort((a, b) => phaseOrder.indexOf(a.phase) - phaseOrder.indexOf(b.phase));
  const settingKeys = row => Object.keys(row).filter(k => /^phase[0-2]_/.test(k) && !/_std_score$|_ESS(_threshold)?$/i.test(k) && row[k] !== null && row[k] !== '');
  const tuningHtml = tuningRows.map(r => `<tr><td><strong>${escapeHtml(r.phase)}</strong></td><td>${settingKeys(r).map(k => `<code>${escapeHtml(k.replace(/^phase[0-2]_/, ''))}=${escapeHtml(r[k])}</code>`).join(' ') || '—'}</td><td class="num">${decimal(r.overall_score)}</td><td class="num">${decimal(r.estimated_policy_value)}</td><td class="num">${signedPct(r.lift_vs_random_pct)}</td></tr>`).join('\n');
  const bestPolicy = tuningRows.find(r => r.phase === 'phase2_policy') || {};
  const tuningCallout = tuningRows.length ? '' : `<div class="callout"><strong>${tuned ? 'Tuning results not found.' : 'Tuning has not run.'}</strong> ${tuned ? 'The latest run was tuned, but nba_ais_tuning_results returned no best trials.' : 'The model was trained with the configured settings; set enable_tuning to true in the workflow config to search them.'}</div>`;

  // Action mix
  const actions = q3.map(r => ({ action: String(r.action), loggedRows: n(r.logged_rows), loggedShare: n(r.logged_share), loggedReward: n(r.logged_avg_reward), hasReward: has(r.logged_avg_reward), recommended: n(r.recommended_users), recommendedShare: n(r.recommended_share) }));
  actions.forEach(a => { a.shift = a.recommendedShare - a.loggedShare; });
  const top = actions.slice().sort((a, b) => b.recommended - a.recommended)[0];
  const shiftTop = actions.slice().sort((a, b) => Math.abs(b.shift) - Math.abs(a.shift))[0];
  const neverRecommended = actions.filter(a => a.loggedRows > 0 && a.recommended === 0).map(a => a.action);
  const thinActions = actions.filter(a => a.loggedRows > 0 && a.loggedRows < 200).map(a => a.action);
  const actionRows = actions.map(a => `<tr><td><strong>${escapeHtml(a.action)}</strong></td><td class="num">${integer(a.loggedRows)}</td><td class="num">${pct(a.loggedShare)}</td><td class="num">${a.hasReward ? decimal(a.loggedReward) : '—'}</td><td class="num">${integer(a.recommended)}</td><td class="num">${pct(a.recommendedShare)}</td><td class="num">${a.shift >= 0 ? '+' : ''}${(a.shift * 100).toFixed(1)} pts</td></tr>`).join('\n');

  // History
  // Unique category per run: two training runs on the same run date get a (2), (3) suffix
  const seenLabels = {};
  const runLabel = base => { seenLabels[base] = (seenLabels[base] || 0) + 1; return seenLabels[base] > 1 ? `${base} (${seenLabels[base]})` : base; };
  const historicTrain = q2.map(r => ({ label: runLabel(r.run_date || String(r.session_id)), value: n(r.estimated_policy_value), lower: n(r.ci_lower), upper: n(r.ci_upper), logged: n(r.logged_avg_reward) }));
  const predSessions = [];
  const bySession = {};
  q6.forEach(r => {
    const key = String(r.session_id);
    if (!bySession[key]) { bySession[key] = { label: r.scored_date || key, counts: {} }; predSessions.push(key); }
    bySession[key].counts[String(r.next_best_action)] = n(r.customers);
  });
  const allActions = [...new Set(q6.map(r => String(r.next_best_action)))];
  const predSeries = allActions.map(action => ({ action, customers: predSessions.map(s => bySession[s].counts[action] || 0) }));
  const predLabels = predSessions.map(s => bySession[s].label);
  const callout = historicTrain.length <= 1 ? '<div class="callout"><strong>Only one run available.</strong> The Historic Tracker shows the current snapshot. Trend lines will populate after subsequent workflow runs.</div>' : '';

  const insights1 = `<li><strong>Past decisions vs model:</strong> logged average reward <strong>${decimal(logged)}</strong>, estimated policy value <strong>${decimal(runRow.estimated_policy_value)}</strong> (95% interval <strong>${decimal(runRow.ci_lower)}</strong>–<strong>${decimal(runRow.ci_upper)}</strong>), estimated lift <strong>${signedPct(runRow.estimated_lift_pct)}</strong>.</li><li><strong>Evidence:</strong> ${lower > logged ? 'the whole interval is above the logged reward — a confident improvement on past data' : value >= logged ? 'the estimate is above the logged reward but the interval includes it — likely better, not proven' : 'the estimate is not above the logged reward — no improvement shown'}.</li><li><strong>Data:</strong> <strong>${integer(runRow.train_rows)}</strong> logged actions over <strong>${integer(runRow.n_actions)}</strong> actions and <strong>${integer(runRow.train_users)}</strong> customers.</li><li><strong>Caveat:</strong> the policy value is an off-policy estimate on the training log (in-sample)${bestPolicy.lift_vs_random_pct !== undefined && has(bestPolicy.lift_vs_random_pct) ? `; tuning's hold-out shows <strong>${signedPct(bestPolicy.lift_vs_random_pct)}</strong> vs random choices` : ''}. A holdout group after go-live measures the real effect.</li>`;
  const insights2 = actions.length ? `<li><strong>Top recommendation:</strong> <strong>${escapeHtml(top.action)}</strong> for <strong>${pct(top.recommendedShare)}</strong> of customers (it was <strong>${pct(top.loggedShare)}</strong> of past decisions).</li><li><strong>Biggest shift:</strong> <strong>${escapeHtml(shiftTop.action)}</strong> ${shiftTop.shift >= 0 ? 'gains' : 'loses'} <strong>${Math.abs(shiftTop.shift * 100).toFixed(1)} pts</strong> of share.</li>${neverRecommended.length ? `<li><strong>Never recommended:</strong> ${neverRecommended.map(a => `<strong>${escapeHtml(a)}</strong>`).join(', ')} — the policy expects another action to do better for every scored customer.</li>` : ''}${thinActions.length ? `<li><strong>Thin data:</strong> ${thinActions.map(a => `<strong>${escapeHtml(a)}</strong>`).join(', ')} ${thinActions.length === 1 ? 'has' : 'have'} fewer than 200 logged rows — estimates for ${thinActions.length === 1 ? 'it are' : 'them are'} weak.</li>` : ''}<li><strong>Reading the reward chart:</strong> the average logged reward per action is raw — it reflects who received the action, not the action's effect.</li>` : '<li><strong>No action statistics found</strong> in <code>nba_ais_action_stats</code> — run the scoring workflow.</li>';
  const insights3 = `<li><strong>Training runs:</strong> <strong>${integer(historicTrain.length)}</strong> in <code>nba_ais_run_log</code>.</li><li><strong>Scoring runs:</strong> <strong>${integer(predSessions.length)}</strong> in <code>${escapeHtml(predTable)}_history</code>.</li><li><strong>Next check:</strong> compare the next run's policy value, interval and mix; a change after a config or SQL edit is expected, a change without one is drift in the customers or the actions.</li>`;

  const tokenMap = {
    '{{project_name}}': escapeHtml(projectName), '{{sink_database}}': escapeHtml(sinkDatabase), '{{pred_table}}': escapeHtml(predTable),
    '{{session_id}}': escapeHtml(runRow.session_id), '{{run_date}}': escapeHtml(runRow.run_date || '—'), '{{model_name}}': escapeHtml(runRow.model_name || '—'), '{{model_type}}': escapeHtml(runRow.model_type || '—'), '{{enable_tuning}}': escapeHtml(runRow.enable_tuning || 'false'), '{{decision_type}}': escapeHtml(runRow.nba_type ? `${runRow.nba_type}${runRow.time_grain ? ` (${runRow.time_grain})` : ''}` : '—'),
    '{{n_actions}}': integer(runRow.n_actions), '{{customers_scored}}': integer(recs.customers), '{{run_count}}': String(historicTrain.length),
    '{{train_rows}}': integer(runRow.train_rows), '{{train_users}}': integer(runRow.train_users), '{{reward_window_days}}': integer(runRow.reward_window_days), '{{train_window_days}}': integer(runRow.train_window_days), '{{feature_lookback_days}}': integer(runRow.feature_lookback_days),
    '{{logged_avg_reward}}': decimal(runRow.logged_avg_reward), '{{estimated_policy_value}}': decimal(runRow.estimated_policy_value), '{{ci_lower}}': decimal(runRow.ci_lower), '{{ci_upper}}': decimal(runRow.ci_upper), '{{estimated_lift_pct}}': signedPct(runRow.estimated_lift_pct), '{{evidence_pill}}': evidencePill,
    '{{tuning_callout}}': tuningCallout, '{{tuning_rows}}': tuningHtml || '<tr><td colspan="5">—</td></tr>', '{{tab1_insights_html_li}}': insights1,
    '{{scored_date}}': escapeHtml(recs.scored_date || '—'), '{{actions_recommended}}': integer(recs.actions_recommended), '{{top_action}}': escapeHtml(top ? top.action : '—'), '{{top_action_share}}': top ? pct(top.recommendedShare) : '—', '{{biggest_shift_action}}': escapeHtml(shiftTop ? shiftTop.action : '—'), '{{biggest_shift}}': shiftTop ? `${shiftTop.shift >= 0 ? '+' : ''}${(shiftTop.shift * 100).toFixed(1)} pts` : '—', '{{action_rows}}': actionRows || '<tr><td colspan="7">—</td></tr>', '{{tab2_insights_html_li}}': insights2,
    '{{historic_single_run_callout}}': callout, '{{tab3_insights_html_li}}': insights3,
    '{{logged_avg_reward_num}}': json(logged), '{{estimated_policy_value_num}}': json(value), '{{ci_lower_num}}': json(lower), '{{ci_upper_num}}': json(upper),
    '{{mix_actions_json}}': json(actions.map(a => a.action)), '{{mix_logged_share_json}}': json(actions.map(a => a.loggedShare)), '{{mix_recommended_share_json}}': json(actions.map(a => a.recommendedShare)), '{{mix_logged_reward_json}}': json(actions.map(a => a.loggedReward)),
    '{{historic_run_labels_json}}': json(historicTrain.map(r => r.label)), '{{historic_value_json}}': json(historicTrain.map(r => r.value)), '{{historic_lower_json}}': json(historicTrain.map(r => r.lower)), '{{historic_upper_json}}': json(historicTrain.map(r => r.upper)), '{{historic_logged_json}}': json(historicTrain.map(r => r.logged)),
    '{{historic_pred_run_labels_json}}': json(predLabels), '{{historic_pred_series_json}}': json(predSeries)
  };

  let html = fs.readFileSync(templatePath, 'utf8');
  html = html.replace(/^<!DOCTYPE html>[\s\S]*?-->\s*<html/i, '<!DOCTYPE html>\n<html');
  for (const [token, replacement] of Object.entries(tokenMap)) html = html.split(token).join(replacement);
  const leftovers = html.match(/\{\{[^}]+\}\}/g);
  if (leftovers?.length) console.warn(`Warning: unreplaced tokens: ${leftovers.slice(0, 5).join(', ')}`);

  const raw = { project: { name: projectName, slug: projectSlug, database: sinkDatabase, predTable }, meta: { sessionId: runRow.session_id, predSessionId: recs.pred_session_id, modelName: runRow.model_name, modelType: runRow.model_type, tuned, customersScored: n(recs.customers) }, training: { latest: runRow, historic: historicTrain }, tuning: tuningRows, actions, scoring: { latest: recs, sessions: predLabels, series: predSeries } };
  html = html.replace('</head>', `<script id="nba-ai-signal-data-payload">\nwindow.RAW = ${json(raw)};\n</script>\n</head>`);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  // Make sure agent_outputs/ ignores itself so customer data is never committed
  const outputsIgnore = path.resolve(workRoot, 'agent_outputs', '.gitignore');
  if (outputPath.startsWith(path.dirname(outputsIgnore) + path.sep) && !fs.existsSync(outputsIgnore)) {
    fs.mkdirSync(path.dirname(outputsIgnore), { recursive: true });
    fs.writeFileSync(outputsIgnore, '*\n', 'utf-8');
  }
  fs.writeFileSync(outputPath, html, 'utf8');
  console.log(`Dashboard generated: ${outputPath}`);
  console.log(`Queries completed in ${Date.now() - started}ms`);
}

run().catch(err => {
  console.error(`Fatal error encountered during dashboard generation: ${err.message}`);
  process.exit(1);
});
