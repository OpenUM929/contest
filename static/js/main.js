/**
 * Leadership Analysis System - Frontend JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const inputText = document.getElementById('inputText');
    const llmResponse = document.getElementById('llmResponse');
    const llmPanel = document.getElementById('llmPanel');
    const generatePromptBtn = document.getElementById('generatePromptBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const refreshExamplesBtn = document.getElementById('refreshExamplesBtn');
    const debugSection = document.getElementById('debugSection');
    const resultsSection = document.getElementById('resultsSection');
    const errorPanel = document.getElementById('errorPanel');
    const loadingIndicator = document.getElementById('loadingIndicator');

    // Sidebar Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    // Load random examples on page load
    loadRandomExamples();

    // Sidebar Toggle (Mobile)
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
        });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
    }

    // Submenu Toggle
    document.querySelectorAll('.menu-header').forEach(header => {
        header.addEventListener('click', function() {
            const menuItem = this.closest('.menu-item');
            const submenu = menuItem.querySelector('.submenu');
            const arrow = this.querySelector('.submenu-arrow');
            
            if (submenu) {
                submenu.classList.toggle('collapsed');
                arrow.classList.toggle('expanded');
            }
        });
    });

    // Menu Link Click Handler
    document.querySelectorAll('.menu-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const url = this.dataset.url;
            if (url) {
                window.location.href = url;
                return;
            }
            
            const page = this.dataset.page;
            
            // Remove active from all links
            document.querySelectorAll('.menu-link').forEach(l => l.classList.remove('active'));
            // Add active to this link
            this.classList.add('active');
            
            // Handle page navigation
            handlePageNavigation(page);
            
            // Close sidebar on mobile
            if (window.innerWidth <= 900) {
                closeSidebar();
            }
        });
    });

    function handlePageNavigation(page) {
        const mainContent = document.getElementById('mainContent');
        
        switch(page) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'bulk-analysis':
                loadBulkAnalysis();
                break;
            case 'single-analysis':
                loadSingleAnalysis();
                break;
            case 'quiz-test':
                loadQuizTest();
                break;
            case 'situation-test':
                loadSituationTest();
                break;
            case 'hybrid-test':
                loadHybridTest();
                break;
            case 'negative-test':
                loadNegativeTest();
                break;
            case 'api-settings':
                loadApiSettings();
                break;
            case 'label-management':
                loadLabelManagement();
                break;
            default:
                console.log('Unknown page:', page);
        }
    }

    function loadDashboard() {
        document.querySelector('.header h1').textContent = '대시보드';
        document.querySelector('.header .subtitle').textContent = '리더십 분석 결과 요약';
        showAnalysisSection();
    }

    function loadBulkAnalysis() {
        document.querySelector('.header h1').textContent = '대규모 분석';
        document.querySelector('.header .subtitle').textContent = '여러 텍스트 일괄 분석';
        showAnalysisSection();
    }

    function loadSingleAnalysis() {
        document.querySelector('.header h1').textContent = '개별 분석';
        document.querySelector('.header .subtitle').textContent = 'Micro Label 추출 + Trait 추론';
        showAnalysisSection();
    }

    function loadQuizTest() {
        document.querySelector('.header h1').textContent = '선택형 테스트';
        document.querySelector('.header .subtitle').textContent = '30문항 - 각 상황에 맞는 리더십 유형을 선택하세요';
        showTestSection();
        if (typeof startTest === 'function') {
            startTest('quiz');
        }
    }

    function loadSituationTest() {
        document.querySelector('.header h1').textContent = '상황 카드 테스트';
        document.querySelector('.header .subtitle').textContent = '8문항 - 주어진 상황을 읽고 서술형으로 응답하세요';
        showTestSection();
        if (typeof startTest === 'function') {
            startTest('situation');
        }
    }

    function loadHybridTest() {
        document.querySelector('.header h1').textContent = '복합 테스트';
        document.querySelector('.header .subtitle').textContent = '3문항 - 복합 시나리오를 평가합니다';
        showTestSection();
        if (typeof startTest === 'function') {
            startTest('hybrid');
        }
    }

    function loadNegativeTest() {
        document.querySelector('.header h1').textContent = '부정 Trait 탐지 테스트';
        document.querySelector('.header .subtitle').textContent = '10문항 - 부정적 리더십 패턴을 식별하세요';
        showTestSection();
        if (typeof startTest === 'function') {
            startTest('negative');
        }
    }

    function loadApiSettings() {
        document.querySelector('.header h1').textContent = 'API 설정';
        document.querySelector('.header .subtitle').textContent = 'LLM API 연결 설정을 관리합니다';
        hideTestSection();
    }

    function loadLabelManagement() {
        document.querySelector('.header h1').textContent = '라벨 관리';
        document.querySelector('.header .subtitle').textContent = 'Micro Label 정의 및 매핑을 관리합니다';
        hideTestSection();
    }

    function showTestSection() {
        const testSection = document.getElementById('testSection');
        const examplesSection = document.getElementById('examplesSection');
        const inputSection = document.querySelector('.input-section');
        
        if (testSection) testSection.style.display = 'block';
        if (examplesSection) examplesSection.style.display = 'none';
        if (inputSection) inputSection.style.display = 'none';
        
        setupTestNavigation();
    }

    function showAnalysisSection() {
        const testSection = document.getElementById('testSection');
        const examplesSection = document.getElementById('examplesSection');
        const inputSection = document.querySelector('.input-section');
        
        if (testSection) testSection.style.display = 'none';
        if (examplesSection) examplesSection.style.display = 'block';
        if (inputSection) inputSection.style.display = 'grid';
    }

    function hideTestSection() {
        const testSection = document.getElementById('testSection');
        const examplesSection = document.getElementById('examplesSection');
        const inputSection = document.querySelector('.input-section');
        
        if (testSection) testSection.style.display = 'none';
        if (examplesSection) examplesSection.style.display = 'block';
        if (inputSection) inputSection.style.display = 'grid';
    }

    function setupTestNavigation() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const submitBtn = document.getElementById('submitBtn');

        if (prevBtn) {
            prevBtn.onclick = () => {
                prevQuestion();
            };
        }

        if (nextBtn) {
            nextBtn.onclick = () => {
                submitCurrentAnswer();
            };
        }

        if (submitBtn) {
            submitBtn.onclick = () => {
                submitCurrentAnswer();
            };
        }
    }

    async function loadTestContent(testType) {
        console.log('Loading test content:', testType);
    }

    // Refresh examples button
    refreshExamplesBtn.addEventListener('click', function() {
        loadRandomExamples();
    });

    // Mode toggle
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const inputSection = document.querySelector('.input-section');
            if (this.value === 'manual') {
                llmPanel.classList.add('visible');
                if (inputSection) {
                    inputSection.classList.add('manual-mode');
                    inputSection.classList.remove('auto-mode');
                }
            } else {
                llmPanel.classList.remove('visible');
                if (inputSection) {
                    inputSection.classList.remove('manual-mode');
                    inputSection.classList.add('auto-mode');
                }
            }
        });
    });

    // Generate Prompt Button
    generatePromptBtn.addEventListener('click', async function() {
        const text = inputText.value.trim();
        
        if (!text) {
            alert('분석할 텍스트를 입력해주세요.');
            return;
        }

        try {
            showLoading(true, '프롬프트 생성 중', '텍스트 분석 및 프롬프트 작성...');
            updatePipelineStep(1);
            
            const response = await fetch('/api/generate-prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
                return;
            }

            // 프롬프트를 팝업 또는 모달로 표시
            showPromptModal(data.prompt);
            
        } catch (error) {
            showError('프롬프트 생성 중 오류가 발생했습니다: ' + error.message);
        } finally {
            showLoading(false);
        }
    });

    // Analyze Button
    analyzeBtn.addEventListener('click', async function() {
        const text = inputText.value.trim();
        const mode = document.querySelector('input[name="mode"]:checked').value;
        const llmProvider = document.getElementById('llmProvider').value;
        
        if (!text) {
            showError('분석할 텍스트를 입력해주세요.');
            return;
        }

        if (mode === 'manual' && !llmResponse.value.trim()) {
            showError('LLM 응답을 입력해주세요.');
            return;
        }

        try {
            const mode = document.querySelector('input[name="mode"]:checked').value;
            const llmProvider = document.getElementById('llmProvider').value;
            
            // HANDOVER.md 파이프라인: 1.Vector DB 검색
            updatePipelineStep(1);
            showLoading(true, 'Vector DB 검색 중', 'KoE5 + FAISS 인덱스 검색...');
            
            // LLM별 진행 상황 메시지 설정
            let statusText = '하이브리드 파이프라인 실행 중...';
            let detailText = '';
            const startTime = Date.now();
            let timeUpdateInterval;
            
            const updateTimeDisplay = () => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                const timeStr = minutes > 0 ? `${minutes}분 ${seconds}초` : `${seconds}초`;
                updateLoadingStatus(statusText, `경과 시간: ${timeStr}`);
            };
            
            if (llmProvider === 'opencode') {
                detailText = 'OpenCode (big-pickle) 호출 예정...';
            }
            
            hideError();
            hideResults();
            hideDebug();

            // 2. 임계값 판단
            updatePipelineStep(2);
            
            // 3. 하이브리드 파이프라인 (LLM 호출 포함)
            updatePipelineStep(3);
            
            showLoading(true, statusText, detailText);
            timeUpdateInterval = setInterval(updateTimeDisplay, 5000);

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    mode: mode,
                    llm_provider: llmProvider,
                    llm_response: llmResponse.value.trim()
                })
            });
            
            // 경과 시간 업데이트 중지
            clearInterval(timeUpdateInterval);
            
             const data = await response.json();
             
             // 4. 후처리
             updatePipelineStep(4);
             
             if (data.error) {
                 showError(data.error);
                 resetPipeline();
                 return;
             }

             // 5. Trait 추론
             updatePipelineStep(5);
            
            // 결과 표시
            displayResults(data);
            displayDebug(data.debug_info);
            
            updatePipelineStep(6);
            
        } catch (error) {
            if (typeof timeUpdateInterval !== 'undefined' && timeUpdateInterval) {
                clearInterval(timeUpdateInterval);
            }
            showError('분석 중 오류가 발생했습니다: ' + error.message);
            resetPipeline();
        } finally {
            if (typeof timeUpdateInterval !== 'undefined' && timeUpdateInterval) {
                clearInterval(timeUpdateInterval);
            }
            showLoading(false);
        }
    });

    // Display Results
    function displayResults(data) {
        // % 기반 Trait 차트
        const traitChart = document.getElementById('traitPercentageChart');
        traitChart.innerHTML = '';
        
        const traitPercentages = data.trait_result.trait_percentages || [];
        traitPercentages.forEach((trait, index) => {
            const barItem = document.createElement('div');
            barItem.className = 'trait-bar-item';
            
            const colors = [
                'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
            ];
            
            barItem.innerHTML = `
                <div class="trait-bar-label">${trait.trait_id}: ${trait.name}</div>
                <div class="trait-bar-container">
                    <div class="trait-bar-fill" style="width: ${trait.percentage}%; background: ${colors[index % colors.length]}">
                        <span>${trait.percentage}%</span>
                    </div>
                </div>
                <div class="trait-bar-percent">${trait.percentage}%</div>
            `;
            traitChart.appendChild(barItem);
        });
        
        // Primary Trait (첫 번째로 highest %)
        if (traitPercentages.length > 0) {
            const topTrait = traitPercentages[0];
            document.getElementById('primaryTrait').textContent = 
                `${topTrait.trait_id} (${topTrait.name})`;
            
            // Primary Trait type 표시 (positive/negative)
            const traitTypeEl = document.getElementById('primaryTraitType');
            if (traitTypeEl) {
                traitTypeEl.textContent = topTrait.type === 'negative' ? '⚠️ 부정' : '✅ 긍정';
            }
        }
        
        // Description
        document.getElementById('primaryDescription').textContent = 
            data.trait_result.primary_description || '';
        
        // Strengths - 부정 trait이면 빈 배열이므로 빈 목록 표시
        const strengthsList = document.getElementById('strengthsList');
        strengthsList.innerHTML = '';
        const strengths = data.trait_result.strengths || [];
        if (strengths.length === 0) {
            const li = document.createElement('li');
            li.textContent = data.trait_result.primary_type === 'negative' 
                ? '(부정 trait은 Strengths가 없습니다)' 
                : '정보 없음';
            li.style.color = '#999';
            li.style.fontStyle = 'italic';
            strengthsList.appendChild(li);
        } else {
            strengths.forEach(s => {
                const li = document.createElement('li');
                li.textContent = s;
                strengthsList.appendChild(li);
            });
        }
        
        // Risks
        const risksList = document.getElementById('risksList');
        risksList.innerHTML = '';
        const risks = data.trait_result.risks || [];
        if (risks.length === 0) {
            const li = document.createElement('li');
            li.textContent = '정보 없음';
            li.style.color = '#999';
            li.style.fontStyle = 'italic';
            risksList.appendChild(li);
        } else {
            risks.forEach(r => {
                const li = document.createElement('li');
                li.textContent = r.name || r;
                risksList.appendChild(li);
            });
        }
        
        // Negative Traits
        const negativeTraitsSection = document.getElementById('negativeTraitsSection');
        const negativeTraitsList = document.getElementById('negativeTraitsList');
        const negativeTraits = data.trait_result.negative_traits || [];
        
        if (negativeTraits.length > 0) {
            negativeTraitsSection.style.display = 'block';
            negativeTraitsList.innerHTML = '';
            negativeTraits.forEach(nt => {
                const item = document.createElement('div');
                item.className = 'negative-trait-item';
                item.innerHTML = `
                    <span class="trait-id">${nt.trait_id}</span>
                    <span class="trait-name">${nt.name}</span>
                    <span class="severity">${nt.severity.toFixed(2)}</span>
                `;
                negativeTraitsList.appendChild(item);
            });
        } else {
            negativeTraitsSection.style.display = 'none';
        }
        
        document.getElementById('traitConfidence').textContent = 
            data.trait_result.confidence.toFixed(3);

        // Important Labels with Details
        const importantLabelsGrid = document.getElementById('importantLabels');
        importantLabelsGrid.innerHTML = '';
        (data.important_labels || []).forEach(label => {
            const card = document.createElement('div');
            card.className = 'important-label-card';
            card.innerHTML = `
                <div class="label-header">
                    <span class="label-id">${label.label_id}</span>
                    <span class="label-conf">${label.confidence.toFixed(3)}</span>
                </div>
                <div class="label-name">${label.name}</div>
                <div class="label-category">${label.macro_category}</div>
                <div class="label-definition">${label.definition || ''}</div>
            `;
            importantLabelsGrid.appendChild(card);
        });

        // Vector DB Results
        const vectorSection = document.getElementById('vectorSection');
        const vectorMeta = document.getElementById('vectorMeta');
        const vectorTableBody = document.getElementById('vectorTableBody');
        
        if (data.vector_results && data.vector_results.length > 0) {
            vectorSection.style.display = 'block';
            vectorMeta.innerHTML = `
                <div class="meta-item"><strong>판단:</strong> ${data.vector_meta?.vector_reason || ''}</div>
                <div class="meta-item"><strong>LLM 사용:</strong> ${data.vector_meta?.used_llm ? 'Yes' : 'No'}</div>
            `;
            vectorTableBody.innerHTML = '';
            data.vector_results.forEach((r, idx) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${idx + 1}</td>
                    <td><span class="label-id">${r.label_id}</span></td>
                    <td>${r.confidence.toFixed(4)}</td>
                    <td>${r.distance.toFixed(4)}</td>
                    <td>${r.text}</td>
                `;
                vectorTableBody.appendChild(row);
            });
        } else {
            vectorSection.style.display = 'none';
        }
        
        // 전체 추출된 라벨
        const labelsGrid = document.getElementById('extractedLabels');
        labelsGrid.innerHTML = '';
        
        const sentences = data.extracted_labels.sentences;
        sentences.forEach(sentence => {
            sentence.labels.forEach(label => {
                const chip = document.createElement('div');
                chip.className = 'label-chip';
                chip.innerHTML = `
                    <div class="label-id">${label.label_id}</div>
                    <div class="label-conf">${label.confidence.toFixed(3)}</div>
                `;
                labelsGrid.appendChild(chip);
            });
        });

        // LLM 응답 원본
        document.getElementById('llmResponseDisplay').textContent = 
            JSON.stringify(JSON.parse(data.llm_response), null, 2);

        // 섹션 표시
        showResults();
    }

    // Display Debug Info
    function displayDebug(debugInfo) {
        const tbody = document.getElementById('debugTableBody');
        tbody.innerHTML = '';
        
        debugInfo.forEach(step => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><div class="step-number">${step.step}</div></td>
                <td><strong>${step.name}</strong></td>
                <td><div class="code-preview">${escapeHtml(step.input || '')}</div></td>
                <td><div class="code-preview">${escapeHtml(step.output || '')}</div></td>
                <td>${escapeHtml(step.details || '')}</td>
            `;
            tbody.appendChild(row);
        });
        
        showDebug();
    }

    // Load Random Examples (with trait filter)
    async function loadRandomExamples() {
        const examplesList = document.getElementById('examplesList');
        const traitFilter = document.getElementById('traitFilter');
        const selectedTrait = traitFilter ? traitFilter.value : '';
        
        examplesList.innerHTML = '<p class="loading-text">예제를 불러오는 중...</p>';
        
        try {
            const url = selectedTrait 
                ? `/api/trait-examples?trait=${selectedTrait}` 
                : '/api/trait-examples';
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.examples && data.examples.length > 0) {
                examplesList.innerHTML = '';
                data.examples.forEach(example => {
                    const card = document.createElement('div');
                    card.className = 'example-card';
                    
                    const isNegative = example.category === 'negative';
                    
                    card.innerHTML = `
                        <div class="case-id ${isNegative ? 'negative' : ''}">${example.case_id}</div>
                        <div class="trait-name">${example.trait_name}</div>
                        <div class="text-preview">${escapeHtml(example.raw_text)}</div>
                        <div class="expected-result">
                            ${example.expected_result?.primary ? `<span class="expected-primary">${example.expected_result.primary}</span>` : ''}
                            ${example.expected_result?.secondary?.length ? example.expected_result.secondary.map(s => `<span class="expected-secondary">${s}</span>`).join('') : ''}
                        </div>
                    `;
                    
                    card.addEventListener('click', function() {
                        document.querySelectorAll('.example-card').forEach(c => c.classList.remove('selected'));
                        card.classList.add('selected');
                        inputText.value = example.raw_text;
                    });
                    
                    examplesList.appendChild(card);
                });
            } else {
                examplesList.innerHTML = '<p class="loading-text">예제가 없습니다.</p>';
            }
        } catch (error) {
            examplesList.innerHTML = '<p class="loading-text">예제 로딩 실패</p>';
            console.error('Error loading examples:', error);
        }
    }

    // Trait filter event listeners
    document.addEventListener('DOMContentLoaded', function() {
        const traitFilter = document.getElementById('traitFilter');
        const refreshBtn = document.getElementById('refreshExamplesBtn');
        
        if (traitFilter) {
            traitFilter.addEventListener('change', loadRandomExamples);
        }
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', loadRandomExamples);
        }
        
        // Load initial examples
        loadRandomExamples();
    });

    // Show Prompt Modal
    function showPromptModal(prompt) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1001;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            padding: 24px;
            border-radius: 12px;
            max-width: 800px;
            max-height: 80vh;
            overflow: auto;
            margin: 20px;
        `;
        
        content.innerHTML = `
            <h3 style="margin-bottom: 16px;">생성된 프롬프트</h3>
            <pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; 
                        white-space: pre-wrap; font-size: 0.85rem; max-height: 60vh; overflow: auto;">
${escapeHtml(prompt)}
            </pre>
            <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: flex-end;">
                <button id="copyPromptBtn" class="btn btn-secondary">복사</button>
                <button id="closeModalBtn" class="btn btn-primary">닫기</button>
            </div>
        `;
        
        modal.appendChild(content);
        document.body.appendChild(modal);
        
        document.getElementById('closeModalBtn').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        document.getElementById('copyPromptBtn').addEventListener('click', () => {
            navigator.clipboard.writeText(prompt).then(() => {
                alert('프롬프트가 클립보드에 복사되었습니다.');
            });
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    // Helper Functions
    function showLoading(show, statusText = '분석 중...', detailText = '') {
        loadingIndicator.style.display = show ? 'flex' : 'none';
        const statusEl = document.getElementById('loadingStatus');
        const detailEl = document.getElementById('loadingDetail');
        
        if (statusEl) statusEl.textContent = statusText;
        if (detailEl) detailEl.textContent = detailText;
        
        analyzeBtn.disabled = show;
        generatePromptBtn.disabled = show;
    }

    function updateLoadingStatus(statusText, detailText = '') {
        const statusEl = document.getElementById('loadingStatus');
        const detailEl = document.getElementById('loadingDetail');
        if (statusEl) statusEl.textContent = statusText;
        if (detailEl) detailEl.textContent = detailText;
    }

    function updatePipelineStep(step, totalSteps = 6) {
        const guide = document.getElementById('pipelineGuide');
        if (!guide) return;
        
        const steps = guide.querySelectorAll('.pipeline-step');
        const lines = guide.querySelectorAll('.pipeline-line');
        
        steps.forEach((s, i) => {
            const stepNum = i + 1;
            s.classList.remove('active', 'completed');
            
            if (stepNum < step) {
                s.classList.add('completed');
            } else if (stepNum === step) {
                s.classList.add('active');
            }
        });
        
        lines.forEach((line, i) => {
            line.classList.remove('completed');
            if (i < step - 1) {
                line.classList.add('completed');
            }
        });
    }

    function resetPipeline() {
        const guide = document.getElementById('pipelineGuide');
        if (!guide) return;
        
        const steps = guide.querySelectorAll('.pipeline-step');
        const lines = guide.querySelectorAll('.pipeline-line');
        
        steps.forEach(s => s.classList.remove('active', 'completed'));
        lines.forEach(l => l.classList.remove('completed'));
    }

    function showError(message) {
        errorPanel.style.display = 'block';
        document.getElementById('errorMessage').textContent = message;
    }

    function hideError() {
        errorPanel.style.display = 'none';
    }

    function showResults() {
        resultsSection.style.display = 'grid';
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function showDebug() {
        debugSection.style.display = 'block';
    }

    function hideDebug() {
        debugSection.style.display = 'none';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
