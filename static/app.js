/* ===== STATE ===== */
let currentDatasetId = null
let currentModelId = null
let currentColumns = []
let currentDtypes = {}
let allColumnData = {}

/* ===== UTILS ===== */
function toast(msg, type = '') {
  const el = document.getElementById('toast')
  if (!el) return
  el.textContent = msg
  el.className = `toast show ${type}`
  setTimeout(() => el.classList.remove('show'), 3200)
}

function setStatus(active, label) {
  const dot = document.getElementById('statusDot')
  const lbl = document.getElementById('statusLabel')
  if (!dot || !lbl) return
  dot.className = 'status-dot' + (active ? ' active' : '')
  lbl.textContent = label
}

function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'))
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'))
  const secEl = document.getElementById('sec-' + name)
  if (secEl) secEl.classList.add('active')
  const navEl = document.querySelector(`[data-section="${name}"]`)
  if (navEl) navEl.classList.add('active')
}

function switchTab(btn, tabId) {
  const parent = btn.closest('.section') || document
  parent.querySelectorAll('.tab').forEach(t => t.classList.remove('active'))
  parent.querySelectorAll('.tab-panel').forEach(p => { p.style.display = 'none'; p.classList.remove('active') })
  btn.classList.add('active')
  const panel = document.getElementById(tabId)
  if (panel) {
    panel.style.display = 'block'
    panel.classList.add('active')
  }
}

/* ===== UPLOAD ===== */
const uploadZone = document.getElementById('uploadZone')
const fileInput = document.getElementById('fileInput')

if (uploadZone && fileInput) {
  uploadZone.addEventListener('click', () => fileInput.click())
  uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over') })
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'))
  uploadZone.addEventListener('drop', e => {
    e.preventDefault()
    uploadZone.classList.remove('drag-over')
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  })

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleUpload(fileInput.files[0])
  })
}

async function handleUpload(file) {
  if (!file.name.toLowerCase().endsWith('.csv')) {
    toast('Please select a CSV file', 'error'); return
  }

  setUploadStatus('loading', `<span class="spinner"></span> Uploading ${file.name}...`)

  const form = new FormData()
  form.append('file', file)

  try {
    const res = await fetch('/upload', { method: 'POST', body: form })
    
    if (!res.ok) {
      const errorText = await res.text()
      try {
        const errorData = JSON.parse(errorText)
        throw new Error(errorData.detail || `Server error ${res.status}`)
      } catch (parseError) {
        throw new Error(`Server error ${res.status}: ${errorText.substring(0, 100)}`)
      }
    }
    
    const data = await res.json()

    currentDatasetId = data.dataset_id
    currentColumns = data.columns
    currentDtypes = data.dtypes
    allColumnData = data

    setUploadStatus('success',
      `✓ <strong>${file.name}</strong> loaded — ${data.shape[0].toLocaleString()} rows × ${data.shape[1]} columns`
    )
    setStatus(true, `${data.shape[0]} rows`)
    toast(`Dataset loaded: ${data.shape[0]} rows, ${data.shape[1]} columns`, 'success')

    buildExploreSection(data)
    populateVisualizeSelects(data.columns, data.dtypes)
    populateTrainSelects(data.columns)

    // Auto-navigate to explore
    setTimeout(() => showSection('explore'), 500)

  } catch (e) {
    setUploadStatus('error', `✗ ${e.message}`)
    toast(e.message, 'error')
    console.error(e)
  }
}

function setUploadStatus(type, html) {
  const el = document.getElementById('uploadStatus')
  el.className = `upload-status ${type}`
  el.innerHTML = html
}

/* ===== EXPLORE ===== */
function buildExploreSection(data) {
  // Stats grid
  const totalMissing = Object.values(data.missing || {}).reduce((a, b) => a + b, 0)
  const numCols = Object.values(data.dtypes).filter(d => d.includes('int') || d.includes('float')).length
  document.getElementById('statsGrid').innerHTML = `
    <div class="stat-card"><div class="stat-label">Rows</div><div class="stat-value">${data.shape[0].toLocaleString()}</div></div>
    <div class="stat-card"><div class="stat-label">Columns</div><div class="stat-value">${data.shape[1]}</div></div>
    <div class="stat-card"><div class="stat-label">Numeric</div><div class="stat-value">${numCols}</div><div class="stat-sub">columns</div></div>
    <div class="stat-card"><div class="stat-label">Missing</div><div class="stat-value">${totalMissing.toLocaleString()}</div><div class="stat-sub">total cells</div></div>
  `

  // Schema table
  const schemaRows = data.columns.map(col => {
    const missing = (data.missing || {})[col] || 0
    const pct = ((missing / data.shape[0]) * 100).toFixed(1)
    return `<tr>
      <td>${col}</td>
      <td><span class="dtype-badge">${data.dtypes[col]}</span></td>
      <td>${missing > 0 ? `<span style="color:var(--warning)">${missing} (${pct}%)</span>` : '<span style="color:var(--success)">0</span>'}</td>
    </tr>`
  }).join('')
  document.getElementById('schemaTable').innerHTML = `
    <thead><tr><th>Column</th><th>Type</th><th>Missing</th></tr></thead>
    <tbody>${schemaRows}</tbody>
  `

  // Stats table
  const statCols = Object.keys(data.stats || {})
  if (statCols.length) {
    const statKeys = Object.keys(data.stats[statCols[0]] || {})
    const statsHtml = `<table class="data-table">
      <thead><tr><th>Column</th>${statKeys.map(k => `<th>${k}</th>`).join('')}</tr></thead>
      <tbody>${statCols.map(col => `<tr><td>${col}</td>${statKeys.map(k => {
        const v = data.stats[col][k]
        return `<td>${v === null || v === undefined ? '—' : (typeof v === 'number' ? v.toLocaleString(undefined, {maximumFractionDigits: 4}) : v)}</td>`
      }).join('')}</tr>`).join('')}</tbody>
    </table>`
    document.getElementById('statsTable').innerHTML = statsHtml
  }

  // Sample table
  if (data.sample && data.sample.length) {
    const cols = Object.keys(data.sample[0])
    const sampleHtml = `<table class="data-table">
      <thead><tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead>
      <tbody>${data.sample.map(row => `<tr>${cols.map(c => `<td>${row[c] === null || row[c] === '' ? '<span style="color:var(--text-faint)">null</span>' : row[c]}</td>`).join('')}</tr>`).join('')}</tbody>
    </table>`
    document.getElementById('sampleTable').innerHTML = `<div class="table-scroll">${sampleHtml}</div>`
  }

  // Missing bars
  const missingEntries = Object.entries(data.missing || {})
    .filter(([_, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
  const missingHtml = missingEntries.length === 0
    ? '<p style="color:var(--success);text-align:center;padding:20px">✓ No missing values found</p>'
    : missingEntries.map(([col, count]) => {
        const pct = ((count / data.shape[0]) * 100).toFixed(1)
        return `<div class="missing-row">
          <span class="missing-col" title="${col}">${col}</span>
          <div class="missing-bar-wrap"><div class="missing-bar" style="width:${pct}%"></div></div>
          <span class="missing-pct">${pct}%</span>
        </div>`
      }).join('')
  document.getElementById('missingBars').innerHTML = missingHtml
}

/* ===== VISUALIZE ===== */
function populateVisualizeSelects(cols, dtypes) {
  const numCols = cols.filter(c => dtypes[c] && (dtypes[c].includes('int') || dtypes[c].includes('float')))
  const allOpts = cols.map(c => `<option value="${c}">${c}</option>`).join('')
  const numOpts = numCols.map(c => `<option value="${c}">${c}</option>`).join('')

  document.getElementById('plotX').innerHTML = allOpts
  document.getElementById('plotY').innerHTML = numOpts
  document.getElementById('plotHue').innerHTML = '<option value="None">None</option>' + allOpts
  updatePlotControls()
}

function updatePlotControls() {
  const type = document.getElementById('plotType').value
  const showX = ['scatter', 'bar', 'box', 'histogram'].includes(type)
  const showY = ['scatter', 'bar'].includes(type)
  const showHue = ['scatter'].includes(type)

  document.getElementById('ctrl-x').style.display = showX ? 'flex' : 'none'
  document.getElementById('ctrl-y').style.display = showY ? 'flex' : 'none'
  document.getElementById('ctrl-hue').style.display = showHue ? 'flex' : 'none'
}

async function generatePlot() {
  if (!currentDatasetId) { toast('Upload a dataset first', 'error'); return }
  const container = document.getElementById('plotContainer')
  container.innerHTML = '<div class="plot-empty"><span class="spinner"></span> Generating chart...</div>'

  const type = document.getElementById('plotType').value
  const x = document.getElementById('plotX').value
  const y = document.getElementById('plotY').value
  const hue = document.getElementById('plotHue').value

  let url = `/plot?dataset_id=${currentDatasetId}&plot_type=${type}`
  if (x) url += `&x=${encodeURIComponent(x)}`
  if (y) url += `&y=${encodeURIComponent(y)}`
  if (hue) url += `&hue=${encodeURIComponent(hue)}`

  try {
    const res = await fetch(url)
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Plot generation failed')
    }
    const blob = await res.blob()
    const imgUrl = URL.createObjectURL(blob)
    container.innerHTML = `<img src="${imgUrl}" alt="plot"/>`
  } catch (e) {
    container.innerHTML = `<div class="plot-empty" style="color:var(--danger)">✗ ${e.message}</div>`
    toast(e.message, 'error')
  }
}

/* ===== TRAIN ===== */
function populateTrainSelects(cols) {
  const opts = cols.map(c => `<option value="${c}">${c}</option>`).join('')
  document.getElementById('targetSelect').innerHTML = opts
  document.getElementById('featuresSelect').innerHTML = opts
  initFeatureSelection()  // Enable toggle selection
}

function selectAllFeatures() {
  const sel = document.getElementById('featuresSelect')
  Array.from(sel.options).forEach(o => o.selected = true)
}
function clearFeatures() {
  const sel = document.getElementById('featuresSelect')
  Array.from(sel.options).forEach(o => o.selected = false)
}

// Enable toggle selection on click
function initFeatureSelection() {
  const sel = document.getElementById('featuresSelect')
  if (!sel) return
  
  sel.addEventListener('mousedown', (e) => {
    if (e.target.tagName === 'OPTION') {
      e.preventDefault()
      e.target.selected = !e.target.selected
      // Trigger change event manually
      sel.dispatchEvent(new Event('change', { bubbles: true }))
    }
  })
}

async function trainModel() {
  if (!currentDatasetId) { toast('Upload a dataset first', 'error'); return }

  const target = document.getElementById('targetSelect').value
  const features = Array.from(document.getElementById('featuresSelect').selectedOptions).map(o => o.value)

  if (!target) { toast('Select a target column', 'error'); return }
  if (features.length === 0) { toast('Select at least one feature column', 'error'); return }
  if (features.includes(target)) { toast('Target column cannot be a feature column', 'error'); return }

  const btn = document.getElementById('trainBtn')
  const btnText = document.getElementById('trainBtnText')
  btn.disabled = true
  btnText.innerHTML = '<span class="spinner"></span> Training...'

  const resultArea = document.getElementById('trainResultArea')
  resultArea.style.display = 'none'

  try {
    const body = {
      dataset_id: currentDatasetId,
      target_col: target,
      feature_cols: features,
      model_choice: document.getElementById('modelChoice').value,
      scaler_choice: document.getElementById('scalerChoice').value,
      imputer_strategy: document.getElementById('imputerStrategy').value,
      test_size: parseInt(document.getElementById('testSize').value) / 100,
      random_state: 42
    }

    const res = await fetch('/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    const data = await res.json()

    if (!res.ok) throw new Error(data.detail || 'Training failed')

    currentModelId = data.model_id

    // Build metrics display
    const taskBadge = `<div class="task-badge ${data.task_type.toLowerCase()}">${data.task_type}</div>`
    const metricsHtml = Object.entries(data.metrics).map(([k, v]) => `
      <div class="metric-item">
        <div class="metric-name">${k.toUpperCase()}</div>
        <div class="metric-value">${typeof v === 'number' ? (v < 1 ? (v * 100).toFixed(2) + '%' : v.toFixed(4)) : v}</div>
      </div>
    `).join('')

    document.getElementById('metricsDisplay').innerHTML = taskBadge + metricsHtml
    document.getElementById('modelActions').style.display = 'flex'
    document.getElementById('downloadBtn').onclick = () => downloadModel(data.model_id)
    resultArea.style.display = 'block'

    toast('Model trained successfully!', 'success')
    buildPredictForm(features, data.model_id)

  } catch (e) {
    toast(e.message, 'error')
    console.error(e)
  }

  btn.disabled = false
  btnText.innerHTML = '⚙ Train Model'
}

function downloadModel(modelId) {
  window.location.href = `/download_model/${modelId}`
}

function goToPredict() {
  showSection('predict')
}

/* ===== PREDICT ===== */
function buildPredictForm(features, modelId) {
  document.getElementById('predictNoModel').style.display = 'none'
  document.getElementById('predictForm').style.display = 'block'

  const inputs = document.getElementById('predictInputs')
  inputs.innerHTML = features.map(f => {
    const dtype = currentDtypes[f] || 'object'
    const isNum = dtype.includes('int') || dtype.includes('float')
    return `<div class="control-group">
      <label>${f}</label>
      <input type="${isNum ? 'number' : 'text'}" id="predict_${CSS.escape(f)}" data-col="${f}" placeholder="${isNum ? '0' : 'value'}"/>
    </div>`
  }).join('')

  document.getElementById('predictionResult').style.display = 'none'
}

async function runPrediction() {
  if (!currentModelId) { toast('Train a model first', 'error'); return }

  const inputs = {}
  document.querySelectorAll('#predictInputs input').forEach(el => {
    const col = el.dataset.col
    const dtype = currentDtypes[col] || 'object'
    const isNum = dtype.includes('int') || dtype.includes('float')
    const val = el.value
    inputs[col] = isNum && val !== '' ? parseFloat(val) : (val || null)
  })

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id: currentModelId, input: inputs })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Prediction failed')

    const resultEl = document.getElementById('predictionResult')
    const valueEl = document.getElementById('predictionValue')
    const pred = data.prediction
    valueEl.textContent = typeof pred === 'number' ? pred.toLocaleString(undefined, { maximumFractionDigits: 4 }) : pred
    resultEl.style.display = 'block'
    toast('Prediction complete!', 'success')
  } catch (e) {
    toast(e.message, 'error')
  }
}