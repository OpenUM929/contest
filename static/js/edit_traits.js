// edit_traits.js
let traitListData = [];
let currentTraitId = null;

function loadTraits() {
    fetch('/api/edit/traits')
        .then(res => res.json())
        .then(data => {
            traitListData = [...data.positive, ...data.negative];
            renderTraitList(traitListData);
        });
}

function renderTraitList(traits) {
    const listDiv = document.getElementById('traitList');
    let html = '';
    
    traits.forEach(trait => {
        const isPositive = trait.trait_id.startsWith('T1') && trait.trait_id.length === 3;
        const cssClass = isPositive ? 'positive' : 'negative';
        
        html += `<div class="trait-item ${cssClass}" onclick="selectTrait('${trait.trait_id}')" id="item-${trait.trait_id}">
            <strong>${trait.trait_id}</strong> - ${trait.trait_name}
        </div>`;
    });
    
    listDiv.innerHTML = html;
}

function filterTraits(type) {
    let filtered = traitListData;
    
    if (type === 'positive') {
        filtered = traitListData.filter(t => t.trait_id.startsWith('T1') && t.trait_id.length === 3);
    } else if (type === 'negative') {
        filtered = traitListData.filter(t => !(t.trait_id.startsWith('T1') && t.trait_id.length === 3));
    }
    
    renderTraitList(filtered);
    
    // 버튼 스타일
    document.querySelectorAll('.btn-group .btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function filterTraitsByKeyword(keyword) {
    const filtered = traitListData.filter(t => 
        t.trait_id.toLowerCase().includes(keyword.toLowerCase()) ||
        t.trait_name.includes(keyword)
    );
    renderTraitList(filtered);
}

function selectTrait(traitId) {
    currentTraitId = traitId;
    
    // 활성화
    document.querySelectorAll('.trait-item').forEach(el => el.classList.remove('active'));
    document.getElementById(`item-${traitId}`).classList.add('active');
    
    fetch(`/api/edit/traits/${traitId}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('placeholder').style.display = 'none';
            document.getElementById('editor').style.display = 'block';
            
            document.getElementById('traitId').value = data.trait_id;
            document.getElementById('traitIdInput').value = data.trait_id;
            document.getElementById('traitType').value = data.trait_type || '';
            document.getElementById('traitName').value = data.trait_name || '';
            document.getElementById('traitDescription').value = data.description || '';
            document.getElementById('traitRequired').value = JSON.stringify(data.required || [], null, 2);
            document.getElementById('traitOptional').value = JSON.stringify(data.optional || [], null, 2);
            document.getElementById('traitStrengths').value = JSON.stringify(data.strengths || [], null, 2);
            document.getElementById('traitRisks').value = JSON.stringify(data.risks || [], null, 2);
            document.getElementById('traitContextWeight').value = JSON.stringify(data.context_weight || {}, null, 2);
            document.getElementById('traitTitle').innerText = `Edit: ${data.trait_id}`;
        });
}

function saveTrait() {
    const data = {
        trait_id: document.getElementById('traitId').value,
        trait_type: document.getElementById('traitType').value,
        trait_name: document.getElementById('traitName').value,
        description: document.getElementById('traitDescription').value,
        required: JSON.parse(document.getElementById('traitRequired').value || '[]'),
        optional: JSON.parse(document.getElementById('traitOptional').value || '[]'),
        strengths: JSON.parse(document.getElementById('traitStrengths').value || '[]'),
        risks: JSON.parse(document.getElementById('traitRisks').value || '[]'),
        context_weight: JSON.parse(document.getElementById('traitContextWeight').value || '{}')
    };
    
    fetch(`/api/edit/traits/${data.trait_id}`, {
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

function deleteTrait() {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    fetch(`/api/edit/traits/${currentTraitId}`, { method: 'DELETE' })
        .then(() => location.reload());
}

function integrateData() {
    if (!confirm('트레이트를 AI 검토용 통합 파일에 추가하시겠습니까?')) return;
    
    fetch('/api/edit/traits/integrate', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            alert(`통합 완료!\n파일: ${data.file}`);
        });
}

// 초기 로드
window.onload = () => loadTraits();
