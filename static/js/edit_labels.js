// edit_labels.js
let currentType = 'positive';
let currentLabelId = null;
let labelListData = [];

function loadLabels(type) {
    currentType = type;
    
    // 버튼 스타일 변경
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    fetch(`/api/edit/labels/${type}`)
        .then(res => res.json())
        .then(data => {
            labelListData = data.labels;
            renderLabelList(labelListData);
        });
}

function renderLabelList(labels) {
    const listDiv = document.getElementById('labelList');
    let html = '';
    
    // Macro별 그룹화
    const groups = {};
    labels.forEach(label => {
        const macro = label.macro || 'OTHER';
        if (!groups[macro]) groups[macro] = [];
        groups[macro].push(label);
    });
    
    Object.keys(groups).sort().forEach(macro => {
        html += `<div class="macro-group"><strong>${macro}</strong></div>`;
        groups[macro].forEach(label => {
            html += `<div class="label-item" onclick="selectLabel('${label.label_id}')" id="item-${label.label_id}">
                ${label.label_id} - ${label.label_name}
            </div>`;
        });
    });
    
    listDiv.innerHTML = html;
}

function filterLabels(keyword) {
    const filtered = labelListData.filter(l => 
        l.label_id.toLowerCase().includes(keyword.toLowerCase()) ||
        l.label_name.includes(keyword)
    );
    renderLabelList(filtered);
}

function selectLabel(labelId) {
    currentLabelId = labelId;
    
    // 활성화 스타일
    document.querySelectorAll('.label-item').forEach(el => el.classList.remove('active'));
    document.getElementById(`item-${labelId}`).classList.add('active');
    
    fetch(`/api/edit/labels/${currentType}/${labelId}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('placeholder').style.display = 'none';
            document.getElementById('editor').style.display = 'block';
            
            document.getElementById('labelType').value = currentType;
            document.getElementById('labelId').value = data.label_id;
            document.getElementById('labelName').value = data.label_name || '';
            document.getElementById('labelMacro').value = data.macro || '';
            document.getElementById('labelWeight').value = data.weight || 0.7;
            document.getElementById('labelDefinition').value = data.definition || '';
            document.getElementById('labelWhen').value = data.when || '';
            document.getElementById('labelNotWhen').value = data.not_when || '';
            document.getElementById('labelContextWeight').value = JSON.stringify(data.context_weight || {}, null, 2);
            document.getElementById('labelTitle').innerText = `Edit: ${data.label_id}`;
        });
}

function saveLabel() {
    const data = {
        label_id: document.getElementById('labelId').value,
        label_name: document.getElementById('labelName').value,
        macro: document.getElementById('labelMacro').value,
        weight: parseFloat(document.getElementById('labelWeight').value),
        definition: document.getElementById('labelDefinition').value,
        when: document.getElementById('labelWhen').value,
        not_when: document.getElementById('labelNotWhen').value,
        context_weight: JSON.parse(document.getElementById('labelContextWeight').value)
    };
    
    const type = document.getElementById('labelType').value;
    const id = data.label_id;
    
    fetch(`/api/edit/labels/${type}/${id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        const statusDiv = document.getElementById('saveStatus');
        statusDiv.innerHTML = `<div class="alert alert-success">저장 완료!</div>`;
        setTimeout(() => statusDiv.innerHTML = '', 3000);
    })
    .catch(err => {
        document.getElementById('saveStatus').innerHTML = `<div class="alert alert-danger">오류: ${err}</div>`;
    });
}

function deleteLabel() {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    const type = document.getElementById('labelType').value;
    const id = document.getElementById('labelId').value;
    
    fetch(`/api/edit/labels/${type}/${id}`, { method: 'DELETE' })
        .then(() => {
            location.reload();
        });
}

function integrateData() {
    if (!confirm('AI 검토용 통합 파일을 생성하시겠습니까?')) return;
    
    fetch('/api/edit/integrate', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            alert(`통합 완료!\n파일: ${data.file}\n\nAI에게 "${data.file}을 읽고 검토해줘"라고 요청하세요.`);
        });
}

// 초기 로드
window.onload = () => loadLabels('positive');
