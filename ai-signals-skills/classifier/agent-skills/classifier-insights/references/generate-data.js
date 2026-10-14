#!/usr/bin/env node
/**
 * Classification Dashboard Data Generator.
 *
 * Runs the eight dashboard queries concurrently, derives the template values,
 * and writes a standalone HTML dashboard for a customer's classifier output.
 *
 * Output (default): ./agent_outputs/<customer_slug>/classifier/dashboards/classifier_summary_dashboard.html
 *   relative to the current working directory — run it from the user's working directory.
 *
 * Usage:
 *   node generate-data.js <sink_database> [customer_slug] [customer_name]
 *   SOURCE_DB=<sink_database> node generate-data.js [customer_slug] [customer_name]
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
let customPrefix = null;
let customUserIdCol = null;
let verbose = false;
const positional = [];

function help() {
  console.log(`
Classification Dashboard Data Generator

Usage:
  node generate-data.js [sink_database] [customer_slug] [customer_name]
  SOURCE_DB=<sink_database> node generate-data.js [customer_slug] [customer_name]

Arguments:
  sink_database         Treasure Data database where classifier output tables reside (required, or env SOURCE_DB)
  customer_slug         Directory slug for customer output (default: derived from customer name or "customer")
  customer_name         Display name for customer (default: Title-cased slug)

Options:
  -p, --prefix          Classifier table prefix (default: TABLE_PREFIX or empty)
  -u, --user-id-col     Profile identifier override for metadata (auto-detected from predictions schema)
  -o, --output          Custom output HTML path
                        (default: ./agent_outputs/<customer_slug>/classifier/dashboards/classifier_summary_dashboard.html)
  -t, --template        Dashboard template path
  -v, --verbose         Show query timings and row counts
  -h, --help            Show this help
`);
  process.exit(process.exitCode || 0);
}

for (let i = 0; i < args.length; i += 1) {
  const arg = args[i];
  if (arg === '-h' || arg === '--help') help();
  else if (arg === '-p' || arg === '--prefix') customPrefix = args[++i];
  else if (arg === '-u' || arg === '--user-id-col') customUserIdCol = args[++i];
  else if (arg === '-o' || arg === '--output') customOutput = args[++i];
  else if (arg === '-t' || arg === '--template') customTemplate = args[++i];
  else if (arg === '-v' || arg === '--verbose') verbose = true;
  else if (!arg.startsWith('-')) positional.push(arg);
}

let sinkDatabase = process.env.SOURCE_DB || '';
let customerSlug = process.env.CUSTOMER_SLUG || '';
let customerName = process.env.CUSTOMER_NAME || '';
const tablePrefix = customPrefix ?? process.env.TABLE_PREFIX ?? process.env.PREFIX ?? '';

if (positional.length > 0) {
  if (!sinkDatabase) {
    sinkDatabase = positional[0];
    if (positional[1]) customerSlug = positional[1];
    if (positional[2]) customerName = positional[2];
  } else {
    customerSlug = positional[0];
    if (positional[1]) customerName = positional[1];
  }
}

function validIdentifier(value, label, allowEmpty = false) {
  if (allowEmpty && value === '') return value;
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
validIdentifier(tablePrefix, 'table prefix', true);
customerSlug = customerSlug || 'customer';
customerName = customerName || customerSlug.split(/[-_]/).map(w => w[0]?.toUpperCase() + w.slice(1)).join(' ');

const scriptDir = __dirname;
const templatePath = customTemplate
  ? path.resolve(process.cwd(), customTemplate)
  : path.join(scriptDir, 'dashboard_template.html');
const outputDir = path.resolve(workRoot, 'agent_outputs', customerSlug, 'classifier', 'dashboards');
const outputPath = customOutput
  ? path.resolve(process.cwd(), customOutput)
  : path.join(outputDir, 'classifier_summary_dashboard.html');

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
function integer(value) { return Math.round(n(value)).toLocaleString('en-US'); }
function decimal(value, places = 4) { return n(value).toFixed(places); }
function pct(value) { return `${(n(value) * 100).toFixed(1)}%`; }
function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function json(value) { return JSON.stringify(value); }
function tableName(name) { return `${sinkDatabase}.${tablePrefix}${name}`; }

async function detectUserIdCol() {
  const explicit = customUserIdCol || process.env.USER_ID_COL;
  if (explicit) return validIdentifier(explicit, 'user ID column');
  const rows = await query(`DESCRIBE ${tableName('predictions')}`, 'Detect classifier user ID column');
  const columns = rows.map(row => String(row.Column || row.column_name || row.col_name || row.Field || '').toLowerCase());
  const candidates = ['td_consumer_id', 'td_canonical_id', 'canonical_id', 'user_id', 'customer_id', 'cdp_profile_id', 'profile_id'];
  return candidates.find(candidate => columns.includes(candidate)) || null;
}

async function run() {
  const started = Date.now();
  const userIdCol = await detectUserIdCol();
  const tp = name => tableName(name);

  const [q1, q2, q3, q4, q5, q6, q7, q8] = await Promise.all([
    query(`SELECT session_id, model_type, best_threshold, precision, recall, f1_score, fbeta, auc_roc, aucpr, true_positives, true_negatives, false_positives, false_negatives, TD_TIME_FORMAT(time, 'yyyy-MM-dd HH:mm', 'UTC') AS run_time FROM ${tp('run_log')} WHERE session_id = (SELECT MAX(session_id) FROM ${tp('run_log')}) LIMIT 1`, 'Q1 latest training metrics'),
    query(`SELECT auc_roc, fbeta, precision, recall FROM ${tp('train_run_log')} WHERE session_id = (SELECT MAX(session_id) FROM ${tp('run_log')}) LIMIT 1`, 'Q2 training metrics'),
    query(`SELECT feature_name, mean_abs_shap_value FROM ${tp('feature_importance')} WHERE session_id = (SELECT MAX(session_id) FROM ${tp('run_log')}) ORDER BY mean_abs_shap_value DESC LIMIT 15`, 'Q3 feature importance'),
    query(`SELECT feature_name, direction, mean_shap, direction_confidence, pct_pushing_up, pct_pushing_down FROM ${tp('shap_directional')} WHERE session_id = (SELECT MAX(session_id) FROM ${tp('run_log')}) ORDER BY mean_abs_shap DESC LIMIT 15`, 'Q4 directional SHAP'),
    query(`SELECT pred_session_id, records_scored, score_mean, score_min, score_max, psi, threshold_applied, predicted_positive, run_timestamp FROM ${tp('prediction_run_log')} WHERE pred_session_id = (SELECT MAX(pred_session_id) FROM ${tp('prediction_run_log')}) LIMIT 1`, 'Q5 latest prediction run'),
    query(`SELECT bin_range, count, percentage FROM ${tp('prediction_bins')} WHERE pred_session_id = (SELECT MAX(pred_session_id) FROM ${tp('prediction_run_log')}) ORDER BY bin_range ASC`, 'Q6 score bins'),
    query(`SELECT session_id, TD_TIME_FORMAT(time, 'yyyy-MM-dd', 'UTC') AS run_date, auc_roc, fbeta, precision, recall FROM ${tp('run_log')} ORDER BY session_id ASC`, 'Q7 training history'),
    query(`SELECT pred_session_id, records_scored, psi, run_timestamp FROM ${tp('prediction_run_log')} ORDER BY pred_session_id ASC`, 'Q8 prediction history')
  ]);

  if (!q1.length) throw new Error(`No records found in ${tp('run_log')}. Verify the classifier workflow has completed.`);
  const train = q1[0];
  const trainCheck = q2[0] || {};
  const prediction = q5[0] || {};
  const threshold = n(train.best_threshold);
  const testTotal = n(train.true_positives) + n(train.true_negatives) + n(train.false_positives) + n(train.false_negatives);
  const predictedPositive = prediction.predicted_positive !== undefined && prediction.predicted_positive !== null
    ? n(prediction.predicted_positive)
    : 0;
  const recordsScored = n(prediction.records_scored);
  const psi = n(prediction.psi);
  const runTime = train.run_time || '—';
  const testAuc = n(train.auc_roc) / 100;
  const trainAuc = n(trainCheck.auc_roc) / 100;
  const testFbeta = n(train.fbeta);
  const trainFbeta = n(trainCheck.fbeta);
  const aucGap = trainAuc - testAuc;
  const fbetaGap = trainFbeta - testFbeta;

  const featureRows = q3.slice(0, 15);
  const directionalRows = q4.slice(0, 15);
  const featureLabels = featureRows.map(r => r.feature_name);
  const featureValues = featureRows.map(r => n(r.mean_abs_shap_value));
  const directionalLabels = directionalRows.map(r => r.feature_name);
  const directionalValues = directionalRows.map(r => n(r.mean_shap));
  const directionalTable = directionalRows.map(r => `<tr><td><strong>${escapeHtml(r.feature_name)}</strong></td><td><span class="pill ${String(r.direction || '').toLowerCase().includes('increase') ? 'ok' : String(r.direction || '').toLowerCase().includes('decrease') ? 'error' : 'warn'}">${escapeHtml(r.direction || 'unknown')}</span></td><td class="num">${decimal(r.mean_shap)}</td><td class="num">${decimal(r.direction_confidence)}</td><td class="num">${decimal(r.pct_pushing_up, 1)}%</td><td class="num">${decimal(r.pct_pushing_down, 1)}%</td></tr>`).join('\n');

  const bins = q6.map(r => ({ label: r.bin_range, count: n(r.count), percentage: n(r.percentage) }));
  const binTable = bins.map(r => `<tr><td><strong>${escapeHtml(r.label)}</strong></td><td class="num">${integer(r.count)}</td><td class="num">${decimal(r.percentage, 1)}%</td><td>Score distribution</td></tr>`).join('\n');
  const historicTrain = q7.map(r => ({ label: r.run_date || String(r.session_id), id: r.session_id, auc: n(r.auc_roc) / 100, fbeta: n(r.fbeta), precision: n(r.precision), recall: n(r.recall) }));
  const historicPred = q8.map(r => ({ label: r.run_timestamp || String(r.pred_session_id), records: n(r.records_scored), psi: n(r.psi) }));
  const status = psi < 0.10 ? `<span class="pill ok">Stable (${decimal(psi)})</span>` : psi <= 0.25 ? `<span class="pill warn">Monitor (${decimal(psi)})</span>` : `<span class="pill error">Retrain (${decimal(psi)})</span>`;
  const topFeature = featureRows[0]?.feature_name || 'No feature data';
  const topDirectional = directionalRows[0]?.direction || 'No directional data';

  const insights1 = `<li><strong>Test AUC-ROC:</strong> <strong>${decimal(testAuc)}</strong> with precision <strong>${decimal(train.precision)}</strong> and recall <strong>${decimal(train.recall)}</strong>.</li><li><strong>Generalization gap:</strong> AUC gap is <strong>${decimal(aucGap)}</strong> and F-beta gap is <strong>${decimal(fbetaGap)}</strong>.</li><li><strong>Classification threshold:</strong> Best threshold is <strong>${decimal(threshold)}</strong> across <strong>${integer(testTotal)}</strong> test records.</li><li><strong>Model:</strong> <strong>${escapeHtml(train.model_type || 'unknown')}</strong> produced the latest training run.</li>`;
  const insights2 = `<li><strong>Top global driver:</strong> <strong>${escapeHtml(topFeature)}</strong> has the largest mean absolute SHAP contribution.</li><li><strong>Directional signal:</strong> The leading directional feature is classified as <strong>${escapeHtml(topDirectional)}</strong>.</li><li><strong>Driver coverage:</strong> The dashboard shows the top <strong>${integer(featureRows.length)}</strong> global and directional features.</li><li><strong>Action:</strong> Review the strongest positive and negative SHAP contributors before changing campaign targeting.</li>`;
  const insights3 = `<li><strong>Records scored:</strong> <strong>${integer(recordsScored)}</strong> records in the latest prediction run.</li><li><strong>Positive rate:</strong> <strong>${pct(recordsScored ? predictedPositive / recordsScored : 0)}</strong> of scored records were positive.</li><li><strong>PSI status:</strong> Current PSI is <strong>${decimal(psi)}</strong>; ${psi > 0.25 ? 'retraining is recommended' : psi >= 0.10 ? 'monitor the next run' : 'the score distribution is stable'}.</li><li><strong>Score range:</strong> Scores span <strong>${decimal(prediction.score_min)}</strong> to <strong>${decimal(prediction.score_max)}</strong>.</li>`;
  const insights4 = `<li><strong>Training runs:</strong> <strong>${integer(historicTrain.length)}</strong> historical training runs are available.</li><li><strong>Prediction runs:</strong> <strong>${integer(historicPred.length)}</strong> prediction runs are available.</li><li><strong>Latest quality:</strong> AUC-ROC is <strong>${decimal(testAuc)}</strong> and latest PSI is <strong>${decimal(psi)}</strong>.</li><li><strong>Next check:</strong> Compare the next run's AUC, threshold, positive rate, and PSI for drift.</li>`;
  const callout = historicTrain.length <= 1 ? '<div class="callout"><strong>Only one run available.</strong> The Historic Tracker shows the current snapshot. Trend lines will populate after subsequent workflow runs.</div>' : '';

  const tokenMap = {
    '{{customer_name}}': escapeHtml(customerName), '{{sink_database}}': escapeHtml(sinkDatabase), '{{table_prefix}}': escapeHtml(tablePrefix), '{{user_id_col}}': escapeHtml(userIdCol || 'not exposed in aggregate dashboard queries'),
    '{{session_id}}': escapeHtml(train.session_id), '{{pred_session_id}}': escapeHtml(prediction.pred_session_id), '{{run_time_utc}}': escapeHtml(runTime), '{{model_type}}': escapeHtml(train.model_type || '—'), '{{best_threshold}}': decimal(threshold), '{{run_count}}': String(historicTrain.length), '{{pred_run_count}}': String(historicPred.length),
    '{{test_auc_roc}}': decimal(testAuc), '{{test_aucpr}}': decimal(n(train.aucpr) / 100), '{{test_precision}}': decimal(train.precision), '{{test_recall}}': decimal(train.recall), '{{test_f1}}': decimal(n(train.f1_score) / 100), '{{test_fbeta}}': decimal(testFbeta), '{{train_auc_roc}}': decimal(trainAuc), '{{train_fbeta}}': decimal(trainFbeta), '{{train_precision}}': decimal(trainCheck.precision), '{{train_recall}}': decimal(trainCheck.recall), '{{auc_gap}}': decimal(aucGap), '{{fbeta_gap}}': decimal(fbetaGap),
    '{{test_tp}}': integer(train.true_positives), '{{test_tn}}': integer(train.true_negatives), '{{test_fp}}': integer(train.false_positives), '{{test_fn}}': integer(train.false_negatives), '{{test_total}}': integer(testTotal), '{{test_tp_pct}}': pct(testTotal ? n(train.true_positives) / testTotal : 0), '{{test_tn_pct}}': pct(testTotal ? n(train.true_negatives) / testTotal : 0), '{{test_fp_pct}}': pct(testTotal ? n(train.false_positives) / testTotal : 0), '{{test_fn_pct}}': pct(testTotal ? n(train.false_negatives) / testTotal : 0),
    '{{feature_importance_labels_json}}': json(featureLabels), '{{feature_importance_values_json}}': json(featureValues), '{{shap_directional_labels_json}}': json(directionalLabels), '{{shap_directional_values_json}}': json(directionalValues), '{{shap_directional_rows}}': directionalTable, '{{tab1_insights_html_li}}': insights1, '{{tab2_insights_html_li}}': insights2,
    '{{records_scored}}': integer(recordsScored), '{{score_mean}}': decimal(prediction.score_mean), '{{score_min}}': decimal(prediction.score_min), '{{score_max}}': decimal(prediction.score_max), '{{psi}}': decimal(psi), '{{psi_status_pill}}': status, '{{predicted_positive_count}}': integer(predictedPositive), '{{predicted_positive_pct}}': pct(recordsScored ? predictedPositive / recordsScored : 0), '{{score_bins_labels_json}}': json(bins.map(r => r.label)), '{{score_bins_values_json}}': json(bins.map(r => r.count)), '{{score_bins_text_json}}': json(bins.map(r => `${integer(r.count)} (${decimal(r.percentage, 1)}%)`)), '{{score_bins_table_rows}}': binTable, '{{tab3_insights_html_li}}': insights3,
    '{{historic_run_labels_json}}': json(historicTrain.map(r => r.label)), '{{historic_session_ids_json}}': json(historicTrain.map(r => r.id)), '{{historic_auc_roc_json}}': json(historicTrain.map(r => r.auc)), '{{historic_fbeta_json}}': json(historicTrain.map(r => r.fbeta)), '{{historic_precision_json}}': json(historicTrain.map(r => r.precision)), '{{historic_recall_json}}': json(historicTrain.map(r => r.recall)), '{{historic_pred_run_labels_json}}': json(historicPred.map(r => r.label)), '{{historic_records_scored_json}}': json(historicPred.map(r => r.records)), '{{historic_psi_json}}': json(historicPred.map(r => r.psi)), '{{historic_single_run_callout}}': callout, '{{tab4_insights_html_li}}': insights4
  };

  let html = fs.readFileSync(templatePath, 'utf8');
  html = html.replace(/^<!DOCTYPE html>[\s\S]*?-->\s*<html/i, '<!DOCTYPE html>\n<html');
  for (const [token, value] of Object.entries(tokenMap)) html = html.split(token).join(value);
  const leftovers = html.match(/\{\{[^}]+\}\}/g);
  if (leftovers?.length) console.warn(`Warning: unreplaced tokens: ${leftovers.slice(0, 5).join(', ')}`);

  const raw = { customer: { name: customerName, slug: customerSlug, database: sinkDatabase, prefix: tablePrefix }, meta: { userIdCol, sessionId: train.session_id, predSessionId: prediction.pred_session_id, modelType: train.model_type, threshold, recordsScored, psi }, training: { latest: train, historic: historicTrain }, prediction: { latest: prediction, bins }, features: { importance: featureRows, directional: directionalRows } };
  html = html.replace('</head>', `<script id="classifier-data-payload">\nwindow.RAW = ${JSON.stringify(raw, null, 2)};\n</script>\n</head>`);
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

run().catch(() => {
  console.error('Fatal error encountered during dashboard generation.');
  process.exit(1);
});
