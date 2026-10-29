/**
 * DefectEngine — High-Utility Developer Client Logic
 * Clean AST Metric Visualizations, TreeSHAP Attributions & Database Audit Log
 */

let currentTab = 'paste';
let selectedFile = null;

// Realistic Presets
const SAMPLES = {
    clean: `def get_user_greeting(username: str) -> str:
    """Returns a clean personalized greeting with boundary checks."""
    clean_name = username.strip().title()
    return f"Welcome back, {clean_name}!"
`,
    risky: `import os
import requests
import json
import time

def process_payment(user_id, amount, is_vip, retry_count=3):
    """Deep nested branches and high cyclomatic complexity."""
    if amount <= 0:
        return {"status": "error", "msg": "Invalid amount"}
    
    final_amount = amount
    if is_vip:
        if amount > 1000:
            final_amount = amount * 0.85
        elif amount > 500:
            final_amount = amount * 0.90
        else:
            final_amount = amount * 0.95
            
    for attempt in range(retry_count):
        try:
            res = requests.post("https://payment.gateway.com/charge", json={"user": user_id, "amt": final_amount})
            if res.status_code == 200:
                return {"status": "success", "charge": final_amount}
            elif res.status_code == 429:
                time.sleep(1)
                continue
            else:
                break
        except Exception as e:
            if attempt == retry_count - 1:
                return {"status": "failed", "error": str(e)}
                
    return {"status": "timeout"}
`
};

document.addEventListener('DOMContentLoaded', () => {
    initEditorEvents();
    initDropZone();
    checkEngineHealth();
    loadHistory();
    // Default load clean helper so editor isn't blank
    loadSample('clean');
});

// Editor Keyboard & Input Events
function initEditorEvents() {
    const editor = document.getElementById('codeEditor');

    // Live lines & chars counter
    editor.addEventListener('input', updateEditorStats);

    // Tab key indentation support & Ctrl+Enter to execute
    editor.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = editor.selectionStart;
            const end = editor.selectionEnd;
            editor.value = editor.value.substring(0, start) + "    " + editor.value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + 4;
            updateEditorStats();
        } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runAnalysis();
        }
    });
}

function updateEditorStats() {
    const code = document.getElementById('codeEditor').value;
    const lines = code ? code.split('\n').length : 0;
    const chars = code.length;
    document.getElementById('editorStats').textContent = `${lines} lines · ${chars} chars`;
}

function clearEditor() {
    document.getElementById('codeEditor').value = '';
    updateEditorStats();
}

// Health Check Probe
async function checkEngineHealth() {
    const text = document.getElementById('systemStatusText');
    
    try {
        const res = await fetch('/health');
        const data = await res.json();
        if (data.status === 'healthy' && data.model_loaded) {
            text.textContent = 'NASA KC1 Model Ready';
            text.style.color = '#3fb950';
        } else {
            text.textContent = 'Model Degraded';
            text.style.color = '#f85149';
        }
    } catch (e) {
        text.textContent = 'Server Offline';
        text.style.color = '#f85149';
    }
}

// Tab Switching
function switchTab(tab) {
    currentTab = tab;
    const uploadBtn = document.getElementById('tabUploadBtn');
    const pasteBtn = document.getElementById('tabPasteBtn');
    const uploadContent = document.getElementById('uploadTabContent');
    const pasteContent = document.getElementById('pasteTabContent');

    if (tab === 'upload') {
        uploadBtn.classList.add('active');
        pasteBtn.classList.remove('active');
        uploadContent.classList.remove('hidden');
        pasteContent.classList.add('hidden');
    } else {
        pasteBtn.classList.add('active');
        uploadBtn.classList.remove('active');
        pasteContent.classList.remove('hidden');
        uploadContent.classList.add('hidden');
    }
}

// Drop Zone Setup
function initDropZone() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    dropZone.addEventListener('click', (e) => {
        if (!e.target.closest('.btn-icon-subtle')) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    ['dragenter', 'dragover'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(file) {
    if (!file.name.endsWith('.py')) {
        alert('Unsupported file type. Please select a valid Python (.py) source file.');
        return;
    }
    selectedFile = file;
    document.getElementById('dropzoneIdle').classList.add('hidden');
    const info = document.getElementById('selectedFileInfo');
    info.classList.remove('hidden');
    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('selectedFileSize').textContent = `${(file.size / 1024).toFixed(1)} KB`;
}

function clearSelectedFile(e) {
    if (e) e.stopPropagation();
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('selectedFileInfo').classList.add('hidden');
    document.getElementById('dropzoneIdle').classList.remove('hidden');
}

function loadSample(type) {
    switchTab('paste');
    document.getElementById('codeEditor').value = SAMPLES[type];
    document.getElementById('editorFileTitle').textContent = type === 'risky' ? 'payment_routine.py' : 'string_helper.py';
    updateEditorStats();
}

// Execute Defect Analysis
async function runAnalysis() {
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const reportContent = document.getElementById('reportContent');
    const analyzeBtn = document.getElementById('analyzeBtn');

    emptyState.classList.add('hidden');
    reportContent.classList.add('hidden');
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;

    try {
        let response;
        if (currentTab === 'upload') {
            if (!selectedFile) {
                alert('Please upload a Python (.py) file first.');
                loadingState.classList.add('hidden');
                emptyState.classList.remove('hidden');
                analyzeBtn.disabled = false;
                return;
            }
            const formData = new FormData();
            formData.append('file', selectedFile);
            response = await fetch('/api/v1/analyze-file', {
                method: 'POST',
                body: formData
            });
        } else {
            const code = document.getElementById('codeEditor').value;
            if (!code.trim()) {
                alert('Code editor is empty. Enter Python code to evaluate.');
                loadingState.classList.add('hidden');
                emptyState.classList.remove('hidden');
                analyzeBtn.disabled = false;
                return;
            }
            const filename = document.getElementById('editorFileTitle').textContent || 'module.py';
            response = await fetch('/api/v1/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: filename,
                    source_code: code
                })
            });
        }

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Analysis request failed.');
        }

        const data = await response.json();
        renderReport(data);
        
        // Refresh History Audit Trail in real-time
        loadHistory();
    } catch (err) {
        alert(`Analysis Error: ${err.message}`);
        emptyState.classList.remove('hidden');
    } finally {
        loadingState.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
}

// Render Results Report
function renderReport(data) {
    const reportContent = document.getElementById('reportContent');
    reportContent.classList.remove('hidden');

    // 1. Verdict & Gauge
    document.getElementById('reportFileName').textContent = data.filename;
    document.getElementById('riskPercentText').textContent = data.risk_probability;

    const badge = document.getElementById('riskLevelBadge');
    const headline = document.getElementById('verdictHeadline');
    const summary = document.getElementById('riskSummaryText');
    const radialBar = document.getElementById('radialBar');
    
    const prob = data.probability_score;
    const tier = (data.defect_risk || 'LOW').toUpperCase();
    
    // Radial gauge calculation (Radius 42 => circumference = 263.89)
    const circumference = 263.89;
    const offset = circumference - (prob * circumference);
    radialBar.style.strokeDashoffset = offset;

    if (tier === 'HIGH') {
        badge.className = 'risk-badge high';
        badge.textContent = 'HIGH RISK';
        radialBar.style.stroke = '#f85149';
        headline.textContent = 'High Defect Susceptibility';
        summary.textContent = 'Significant non-linear complexity and high operator volume indicate elevated regression likelihood.';
    } else if (tier === 'MEDIUM') {
        badge.className = 'risk-badge medium';
        badge.textContent = 'MODERATE RISK';
        radialBar.style.stroke = '#d29922';
        headline.textContent = 'Moderate Defect Probability';
        summary.textContent = 'Moderate structural branching observed. Review complex routines prior to production release.';
    } else {
        badge.className = 'risk-badge low';
        badge.textContent = 'LOW RISK';
        radialBar.style.stroke = '#3fb950';
        headline.textContent = 'Clean Structural Profile';
        summary.textContent = 'Metric distribution is well-factored with low cyclomatic complexity and low cognitive load.';
    }

    // 2. Hotspot Callout (Only display when an actual high-complexity routine requires attention)
    const hotspotCard = document.getElementById('hotspotCard');
    const hotspotText = document.getElementById('suspiciousComponentText');
    const hotspotRationale = document.getElementById('hotspotRationale');

    const hasHotspot = data.most_suspicious_component && 
                       data.most_suspicious_component !== 'None' && 
                       data.most_suspicious_component !== 'module_level' && 
                       tier !== 'LOW';

    if (hasHotspot) {
        hotspotCard.classList.remove('hidden');
        hotspotText.textContent = data.most_suspicious_component;
        hotspotRationale.textContent = 'This routine exhibits the highest decision path density in the module. Refactoring here yields the greatest reduction in defect risk.';
    } else {
        hotspotCard.classList.add('hidden');
    }

    // 3. TreeSHAP Risk Drivers
    const riskList = document.getElementById('riskDriversList');
    riskList.innerHTML = '';
    if (!data.main_risk_factors || data.main_risk_factors.length === 0) {
        riskList.innerHTML = '<li class="shap-factor-item"><span class="shap-metric-label">No significant risk drivers detected</span></li>';
    } else {
        data.main_risk_factors.forEach(item => {
            const parsed = parseShapString(item);
            const li = document.createElement('li');
            li.className = 'shap-factor-item';
            li.innerHTML = `
                <span class="shap-metric-label">${escapeHtml(parsed.feature)}</span>
                <span class="shap-val-tag risk">${escapeHtml(parsed.impact)}</span>
            `;
            riskList.appendChild(li);
        });
    }

    // 4. TreeSHAP Mitigating Drivers
    const mitList = document.getElementById('mitigatingDriversList');
    mitList.innerHTML = '';
    if (!data.main_mitigating_factors || data.main_mitigating_factors.length === 0) {
        mitList.innerHTML = '<li class="shap-factor-item"><span class="shap-metric-label">No major mitigating factors</span></li>';
    } else {
        data.main_mitigating_factors.forEach(item => {
            const parsed = parseShapString(item);
            const li = document.createElement('li');
            li.className = 'shap-factor-item';
            li.innerHTML = `
                <span class="shap-metric-label">${escapeHtml(parsed.feature)}</span>
                <span class="shap-val-tag mitigate">${escapeHtml(parsed.impact)}</span>
            `;
            mitList.appendChild(li);
        });
    }

    // 5. Static Metric Ribbon Values
    const raw = data.raw_metrics_summary;
    document.getElementById('metricLOC').textContent = raw.lines_of_code;
    document.getElementById('metricCYCLO').textContent = raw.cyclomatic_complexity;
    document.getElementById('metricBranch').textContent = raw.branch_count;
    document.getElementById('metricDeps').textContent = raw.external_dependencies_count;
    document.getElementById('metricOperators').textContent = raw.total_operators;
    document.getElementById('metricOperands').textContent = raw.total_operands;

    // 6. Function Decomposition Table
    const tbody = document.getElementById('functionTableBody');
    tbody.innerHTML = '';
    document.getElementById('functionCount').textContent = data.function_breakdown.length;

    if (data.function_breakdown.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:16px;">No discrete routines detected (pure script / module-level scope).</td></tr>';
    } else {
        data.function_breakdown.forEach(fn => {
            const tr = document.createElement('tr');
            let pillClass = 'safe';
            let labelText = 'Normal';
            if (fn.complexity > 10) {
                pillClass = 'review';
                labelText = 'Refactor';
            } else if (fn.complexity > 4) {
                pillClass = 'moderate';
                labelText = 'Review';
            }
            tr.innerHTML = `
                <td><code style="color:var(--text-primary); font-weight:600; font-family:var(--font-mono);">def ${escapeHtml(fn.name)}()</code></td>
                <td><span style="font-family:var(--font-mono); color:var(--text-muted); font-size:11.5px;">Line ${fn.lineno}</span></td>
                <td><span style="font-family:var(--font-mono); font-weight:600; color:var(--text-primary);">${fn.complexity}</span></td>
                <td><span class="priority-pill ${pillClass}">${labelText}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
}

// Parse Raw SHAP factor string (e.g. "VOLUME (Risk Increasing, SHAP impact: +0.1811)")
function parseShapString(str) {
    if (!str) return { feature: 'Metric', impact: '0.00' };
    const parts = str.split(' (');
    const featureName = parts[0] || str;
    let impact = '';
    if (parts[1]) {
        const impactMatch = parts[1].match(/impact:\s*([+-]?[\d.]+)/);
        if (impactMatch) {
            impact = impactMatch[1];
        }
    }
    return {
        feature: cleanFeatureName(featureName),
        impact: impact || '+0.05'
    };
}

function cleanFeatureName(name) {
    const map = {
        'LOC': 'Lines of Code',
        'CYCLO': 'Cyclomatic Complexity v(g)',
        'LENGTH': 'Halstead Length',
        'VOLUME': 'Halstead Volume',
        'DIFFICULTY': 'Halstead Difficulty',
        'NUM_OPERATORS': 'Operator Volume',
        'NUM_OPERANDS': 'Operand Volume',
        'BRANCH_COUNT': 'Branch Count',
        'COMPLEXITY_DENSITY': 'Complexity Density',
        'OPERATOR_DENSITY': 'Operator Density',
        'OPERAND_DENSITY': 'Operand Density',
        'COMPLEXITY_BRANCH_RATIO': 'Branch Complexity Ratio',
        'INT_FAN_IN': 'Internal Coupling (Fan-In)',
        'INT_FAN_OUT': 'External Dependencies (Fan-Out)'
    };
    return map[name] || name;
}

// ==========================================
// Database Audit Trail Telemetry
// ==========================================

async function loadHistory() {
    const tbody = document.getElementById('historyTableBody');
    const emptyMsg = document.getElementById('historyEmpty');
    const historyCount = document.getElementById('historyCount');
    const filter = document.getElementById('riskFilterSelect').value;

    let url = '/api/v1/history?limit=50';
    if (filter) {
        url += `&risk=${filter}`;
    }

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch history');
        const data = await res.json();

        historyCount.textContent = data.total_count;
        tbody.innerHTML = '';

        if (!data.scans || data.scans.length === 0) {
            emptyMsg.classList.remove('hidden');
            return;
        }

        emptyMsg.classList.add('hidden');

        data.scans.forEach(scan => {
            const tr = document.createElement('tr');
            const tier = (scan.defect_risk || 'LOW').toUpperCase();
            let pillClass = 'low';
            if (tier === 'HIGH') pillClass = 'high';
            else if (tier === 'MEDIUM') pillClass = 'medium';

            tr.innerHTML = `
                <td class="audit-id">#${scan.id}</td>
                <td class="audit-time">${escapeHtml(scan.created_at || 'Just now')}</td>
                <td class="audit-file">${escapeHtml(scan.filename)}</td>
                <td><span class="risk-badge ${pillClass}">${tier}</span></td>
                <td class="audit-prob">${scan.risk_probability}</td>
                <td style="font-family:var(--font-mono);">${scan.lines_of_code}</td>
                <td style="font-family:var(--font-mono);">${scan.cyclomatic_complexity}</td>
                <td class="audit-hotspot" title="${escapeHtml(scan.most_suspicious_component)}">
                    ${escapeHtml(scan.most_suspicious_component)}
                </td>
                <td>
                    <button type="button" class="btn-row-del" onclick="deleteScan(${scan.id})" title="Delete audit record">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Error fetching history:', err);
    }
}

async function deleteScan(scanId) {
    try {
        const res = await fetch(`/api/v1/history/${scanId}`, { method: 'DELETE' });
        if (res.ok) {
            loadHistory();
        } else {
            alert('Failed to delete scan record.');
        }
    } catch (err) {
        console.error('Delete error:', err);
    }
}

async function clearAllHistory() {
    if (!confirm('Clear all audit telemetry logs from database?')) {
        return;
    }

    try {
        const res = await fetch('/api/v1/history', { method: 'DELETE' });
        if (res.ok) {
            loadHistory();
        } else {
            alert('Failed to clear scan history.');
        }
    } catch (err) {
        console.error('Clear history error:', err);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}
