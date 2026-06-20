/**
 * Bulk Analysis JavaScript
 */

let bulkResults = [];
let currentMode = 'text';

document.addEventListener('DOMContentLoaded', function() {
    initMethodButtons();
    initFileUpload();
    initActionButtons();
});

function initMethodButtons() {
    document.querySelectorAll('.method-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.method-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            currentMode = this.dataset.method;
            
            if (currentMode === 'text') {
                document.getElementById('textInputArea').style.display = 'block';
                document.getElementById('fileInputArea').style.display = 'none';
            } else {
                document.getElementById('textInputArea').style.display = 'none';
                document.getElementById('fileInputArea').style.display = 'block';
            }
        });
    });
}

function initFileUpload() {
    const dropZone = document.getElementById('fileDropZone');
    const fileInput = document.getElementById('fileInput');
    
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    Array.from(files).forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.style.cssText = 'padding:12px;background:#f8f9ff;border-radius:8px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;';
        fileItem.innerHTML = `
            <span>📄 ${file.name}</span>
            <button class="btn-remove" style="background:none;border:none;color:#dc3545;cursor:pointer;">✕</button>
        `;
        fileList.appendChild(fileItem);
        
        const reader = new FileReader();
        reader.onload = (e) => {
            fileItem.dataset.content = e.target.result;
        };
        reader.readAsText(file);
    });
}

function initActionButtons() {
    document.getElementById('analyzeBulkBtn').addEventListener('click', startBulkAnalysis);
    document.getElementById('exportCsvBtn').addEventListener('click', exportToCSV);
    document.getElementById('clearBtn').addEventListener('click', clearAll);
}

async function startBulkAnalysis() {
    let texts = [];
    
    if (currentMode === 'text') {
        const textarea = document.getElementById('bulkTextInput').value;
        texts = textarea.split('\n').filter(t => t.trim());
    } else {
        const fileItems = document.querySelectorAll('#fileList > div');
        fileItems.forEach(item => {
            if (item.dataset.content) {
                const content = item.dataset.content;
                const lines = content.split('\n').filter(t => t.trim());
                texts.push(...lines);
            }
        });
    }
    
    if (texts.length === 0) {
        alert('분석할 텍스트를 입력하거나 파일을 업로드해주세요.');
        return;
    }
    
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.classList.add('active');
    
    bulkResults = [];
    
    for (let i = 0; i < texts.length; i++) {
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: texts[i],
                    mode: 'auto',
                    llm_provider: 'gemini'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                bulkResults.push({
                    index: i + 1,
                    text: texts[i],
                    primary: data.trait_result.primary,
                    primary_name: data.trait_result.primary_name,
                    secondary: data.trait_result.secondary.join(', '),
                    confidence: data.trait_result.confidence
                });
            }
        } catch (error) {
            console.error(`텍스트 ${i + 1} 분석 실패:`, error);
        }
    }
    
    loadingOverlay.classList.remove('active');
    displayResults();
}

function displayResults() {
    const resultsArea = document.getElementById('resultsArea');
    const resultsBody = document.getElementById('resultsBody');
    const exportBtn = document.getElementById('exportCsvBtn');
    
    resultsBody.innerHTML = '';
    
    bulkResults.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.index}</td>
            <td><div class="result-text-preview" title="${escapeHtml(result.text)}">${escapeHtml(result.text)}</div></td>
            <td><span class="trait-badge primary">${result.primary} - ${result.primary_name}</span></td>
            <td>${result.secondary || '-'}</td>
            <td>${result.confidence.toFixed(3)}</td>
        `;
        resultsBody.appendChild(row);
    });
    
    resultsArea.style.display = 'block';
    exportBtn.disabled = bulkResults.length === 0;
}

function exportToCSV() {
    if (bulkResults.length === 0) return;
    
    let csv = 'Index,Input Text,Primary Trait,Primary Name,Secondary Traits,Confidence\n';
    
    bulkResults.forEach(result => {
        const text = result.text.replace(/"/g, '""');
        csv += `${result.index},"${text}","${result.primary}","${result.primary_name}","${result.secondary}",${result.confidence.toFixed(3)}\n`;
    });
    
    const blob = new Blob(['\ufeff' + csv], {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bulk_analysis_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

function clearAll() {
    document.getElementById('bulkTextInput').value = '';
    document.getElementById('fileList').innerHTML = '';
    document.getElementById('resultsArea').style.display = 'none';
    document.getElementById('exportCsvBtn').disabled = true;
    bulkResults = [];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}