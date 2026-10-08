/**
 * DefectRiskEngine Frontend Application Logic
 */

let currentTab = 'upload';
let selectedFile = null;

// Sample Snippets for Instant Testing
const SAMPLES = {
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
`,
    clean: `def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculates clean discounted price."""
    if price < 0 or discount_percent < 0:
        raise ValueError("Price and discount must be positive")
    return price * (1 - discount_percent / 100)
`
};

document.addEventListener('DOMContentLoaded', () => {
    initDropZone();
    checkEngineHealth();
});

// Health Check Probe
async function checkEngineHealth() {
    const badge = document.getElementById('systemStatusBadge');
    const text = document.getElementById('systemStatusText');
    
    try {
        const res = await fetch('/health');
        const data = await res.json();
        if (data.status === 'healthy' && data.model_loaded) {
            text.textContent = `Live: ${data.engine}`;
            badge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        } else {
            text.textContent = 'Engine Degraded';
            badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        }
    } catch (e) {
        text.textContent = 'Server Offline';
        badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
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
        if (!e.target.closest('#removeFileBtn')) {
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
        alert('Please select a valid Python (.py) file.');
        return;
    }
    selectedFile = file;
    document.querySelector('.drop-zone-content').classList.add('hidden');
    const info = document.getElementById('selectedFileInfo');
    info.classList.remove('hidden');
    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('selectedFileSize').textContent = `(${(file.size / 1024).toFixed(1)} KB)`;
}

function clearSelectedFile(e) {
    if (e) e.stopPropagation();
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('selectedFileInfo').classList.add('hidden');
    document.querySelector('.drop-zone-content').classList.remove('hidden');
}

function loadSample(type) {
    document.getElementById('codeEditor').value = SAMPLES[type];
}

// Run Defect Analysis
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
                alert('Please paste Python code to analyze.');
                loadingState.classList.add('hidden');
                emptyState.classList.remove('hidden');
                analyzeBtn.disabled = false;
                return;
            }
            response = await fetch('/api/v1/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: 'editor_snippet.py',
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
    } catch (err) {
        alert(`Error: ${err.message}`);
        emptyState.classList.remove('hidden');
    } finally {
        loadingState.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
}

// Render Results
function renderReport(data) {
    const reportContent = document.getElementById('reportContent');
    reportContent.classList.remove('hidden');

    // 1. Risk Level & Percent
    document.getElementById('reportFileName').textContent = data.filename;
    document.getElementById('riskPercentText').textContent = data.risk_probability;

    const badge = document.getElementById('riskLevelBadge');
    badge.textContent = `${data.defect_risk} RISK`;
    badge.className = `risk-level-badge ${data.defect_risk.toLowerCase()}`;

    // Color progress circle
    const circle = document.getElementById('circularProgress');
    const prob = data.probability_score;
    let color = '#10b981';
    if (data.defect_risk === 'HIGH') color = '#ef4444';
    else if (data.defect_risk === 'MEDIUM') color = '#f59e0b';
    
    circle.style.background = `conic-gradient(${color} ${prob * 360}deg, rgba(255, 255, 255, 0.05) 0deg)`;

    // 2. Suspicious Component
    document.getElementById('suspiciousComponentText').textContent = data.most_suspicious_component;

    // 3. SHAP Risk Drivers
    const riskList = document.getElementById('riskDriversList');
    riskList.innerHTML = '';
    if (data.main_risk_factors.length === 0) {
        riskList.innerHTML = '<li class="shap-item">No major risk drivers detected.</li>';
    } else {
        data.main_risk_factors.forEach(item => {
            const li = document.createElement('li');
            li.className = 'shap-item';
            li.innerHTML = `<span>${item}</span>`;
            riskList.appendChild(li);
        });
    }

    // 4. SHAP Mitigating Drivers
    const mitList = document.getElementById('mitigatingDriversList');
    mitList.innerHTML = '';
    if (data.main_mitigating_factors.length === 0) {
        mitList.innerHTML = '<li class="shap-item">No significant mitigating factors.</li>';
    } else {
        data.main_mitigating_factors.forEach(item => {
            const li = document.createElement('li');
            li.className = 'shap-item';
            li.innerHTML = `<span>${item}</span>`;
            mitList.appendChild(li);
        });
    }

    // 5. Raw Static Metrics
    const raw = data.raw_metrics_summary;
    document.getElementById('metricLOC').textContent = raw.lines_of_code;
    document.getElementById('metricCYCLO').textContent = raw.cyclomatic_complexity;
    document.getElementById('metricBranch').textContent = raw.branch_count;
    document.getElementById('metricDeps').textContent = raw.external_dependencies_count;
    document.getElementById('metricOperators').textContent = raw.total_operators;
    document.getElementById('metricOperands').textContent = raw.total_operands;

    // 6. Function Breakdown Table
    const tbody = document.getElementById('functionTableBody');
    tbody.innerHTML = '';
    document.getElementById('functionCount').textContent = data.function_breakdown.length;

    if (data.function_breakdown.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#9ca3af;">No discrete function definitions detected (module-level script).</td></tr>';
    } else {
        data.function_breakdown.forEach(fn => {
            const tr = document.createElement('tr');
            let pillClass = 'low';
            let statusText = 'Clean';
            if (fn.complexity > 7) {
                pillClass = 'high';
                statusText = 'High Risk';
            } else if (fn.complexity > 3) {
                pillClass = 'medium';
                statusText = 'Moderate';
            }
            tr.innerHTML = `
                <td><strong>${fn.name}()</strong></td>
                <td>Line ${fn.lineno}</td>
                <td><span class="complexity-pill ${pillClass}">${fn.complexity}</span></td>
                <td><span style="color: ${pillClass === 'high' ? '#ef4444' : (pillClass === 'medium' ? '#f59e0b' : '#10b981')}">${statusText}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
}
