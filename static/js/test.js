/**
 * Test Module - Leadership Analysis System
 * Handles quiz, situation card, hybrid, and negative detection tests
 */

class TestManager {
    constructor() {
        this.currentTest = null;
        this.currentQuestion = 0;
        this.answers = [];
        this.testData = null;
    }

    async loadTest(type) {
        try {
            const response = await fetch(`/api/test/${type}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading test:', data.error);
                return null;
            }
            
            this.testData = data;
            this.currentQuestion = 0;
            this.answers = [];
            this.currentTest = type;
            
            return data;
        } catch (error) {
            console.error('Error loading test:', error);
            return null;
        }
    }

    getCurrentQuestion() {
        if (!this.testData) return null;
        
        switch(this.currentTest) {
            case 'quiz':
                return this.testData.questions[this.currentQuestion];
            case 'situation':
                return this.testData.situations[this.currentQuestion];
            case 'hybrid':
                return this.testData.tests[this.currentQuestion];
            case 'negative':
                return this.testData.questions[this.currentQuestion];
            default:
                return null;
        }
    }

    getTotalQuestions() {
        if (!this.testData) return 0;
        
        switch(this.currentTest) {
            case 'quiz':
                return this.testData.questions.length;
            case 'situation':
                return this.testData.situations.length;
            case 'hybrid':
                return this.testData.tests.length;
            case 'negative':
                return this.testData.questions.length;
            default:
                return 0;
        }
    }

    saveAnswer(questionId, answerData) {
        this.answers.push({
            question_id: questionId,
            answer: answerData,
            timestamp: new Date().toISOString()
        });
    }

    async submitTest() {
        try {
            const response = await fetch('/api/test/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    test_type: this.currentTest,
                    answers: this.answers,
                    test_data: this.testData
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error submitting test:', error);
            return { error: error.message };
        }
    }

    nextQuestion() {
        if (this.currentQuestion < this.getTotalQuestions() - 1) {
            this.currentQuestion++;
            return true;
        }
        return false;
    }

    prevQuestion() {
        if (this.currentQuestion > 0) {
            this.currentQuestion--;
            return true;
        }
        return false;
    }

    getProgress() {
        return {
            current: this.currentQuestion + 1,
            total: this.getTotalQuestions(),
            percentage: Math.round(((this.currentQuestion + 1) / this.getTotalQuestions()) * 100)
        };
    }
}

const testManager = new TestManager();

function renderQuizQuestion(question) {
    const container = document.getElementById('testContent');
    if (!container) return;

    container.innerHTML = `
        <div class="test-question-card">
            <div class="question-header">
                <span class="question-number">Q${question.id}</span>
                <span class="question-category">${question.category}</span>
            </div>
            <div class="question-text">${question.question}</div>
            <div class="options-list">
                ${question.options.map((opt, idx) => `
                    <label class="option-item" data-option="${opt.id}">
                        <input type="radio" name="answer" value="${opt.id}" />
                        <span class="option-radio"></span>
                        <span class="option-text">${opt.text}</span>
                    </label>
                `).join('')}
            </div>
        </div>
    `;

    setupOptionListeners();
}

function renderSituationQuestion(situation) {
    const container = document.getElementById('testContent');
    if (!container) return;

    container.innerHTML = `
        <div class="test-question-card situation-card">
            <div class="question-header">
                <span class="question-number">SC${situation.id}</span>
                <span class="question-category">${situation.category}</span>
            </div>
            <div class="situation-box">
                <h4>상황</h4>
                <p>${situation.situation.replace(/\n/g, '<br>')}</p>
            </div>
            <div class="question-prompt">
                <h4>답변指引</h4>
                <p>${situation.prompt}</p>
            </div>
            <div class="textarea-answer">
                <textarea id="situationAnswer" placeholder="당신의 응답을 입력해주세요..."></textarea>
            </div>
        </div>
    `;
}

function renderHybridQuestion(test) {
    const container = document.getElementById('testContent');
    if (!container) return;

    const firstPhase = test.phases[0];
    
    container.innerHTML = `
        <div class="test-question-card hybrid-card">
            <div class="question-header">
                <span class="question-number">${test.id}</span>
                <span class="question-category">${test.title}</span>
            </div>
            <div class="scenario-box">
                <h4>시나리오</h4>
                <div class="scenario-text">${test.scenario.replace(/\n/g, '<br>')}</div>
            </div>
            <div class="phase-section">
                <h4>${firstPhase.phase_title}</h4>
                <p class="phase-question">${firstPhase.question}</p>
                <div class="options-list">
                    ${firstPhase.options.map((opt, idx) => `
                        <label class="option-item" data-option="${opt.id}">
                            <input type="radio" name="answer" value="${opt.id}" />
                            <span class="option-radio"></span>
                            <span class="option-text">${opt.text}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    setupOptionListeners();
}

function renderNegativeQuestion(question) {
    const container = document.getElementById('testContent');
    if (!container) return;

    container.innerHTML = `
        <div class="test-question-card negative-card">
            <div class="question-header">
                <span class="question-number">ND${question.id}</span>
                <span class="question-category">${question.category}</span>
            </div>
            <div class="situation-box">
                <h4>상황</h4>
                <p>${question.situation}</p>
            </div>
            <div class="question-text">${question.question}</div>
            <div class="options-list">
                ${question.options.map((opt, idx) => `
                    <label class="option-item" data-option="${opt.id}">
                        <input type="radio" name="answer" value="${opt.id}" />
                        <span class="option-radio"></span>
                        <span class="option-text">${opt.text}</span>
                        ${opt.negative_pattern ? `<span class="negative-hint">⚠️ 부정적 패턴</span>` : ''}
                    </label>
                `).join('')}
            </div>
            ${question.explanation ? `
                <div class="explanation-box" style="display: none;">
                    <h4>해설</h4>
                    <p>${question.explanation}</p>
                </div>
            ` : ''}
        </div>
    `;

    setupOptionListeners();
}

function setupOptionListeners() {
    document.querySelectorAll('.option-item').forEach(item => {
        item.addEventListener('click', function() {
            document.querySelectorAll('.option-item').forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
            this.querySelector('input').checked = true;
        });
    });
}

function renderProgressBar(progress) {
    const progressBar = document.getElementById('progressBar');
    if (!progressBar) return;

    progressBar.innerHTML = `
        <div class="progress-info">
            <span class="progress-text">${progress.current} / ${progress.total}</span>
            <span class="progress-percent">${progress.percentage}%</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width: ${progress.percentage}%"></div>
        </div>
    `;
}

function renderTestHeader(testData) {
    const header = document.getElementById('testHeader');
    if (!header) return;

    header.innerHTML = `
        <div class="test-info">
            <h2>${testData.title}</h2>
            <p>${testData.description}</p>
        </div>
    `;
}

function showTestComplete(results) {
    const container = document.getElementById('testContent');
    if (!container) return;

    container.innerHTML = `
        <div class="test-complete-card">
            <div class="complete-icon">🎉</div>
            <h2>테스트 완료!</h2>
            <p class="complete-message">모든 문항에 응답해주셨습니다.</p>
            
            <div class="result-summary">
                <div class="summary-item">
                    <span class="summary-label">총 문항 수</span>
                    <span class="summary-value">${results.total_questions}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">응답한 문항</span>
                    <span class="summary-value">${results.answered_questions}</span>
                </div>
            </div>
            
            <button id="viewResultsBtn" class="btn btn-primary">결과 보기</button>
        </div>
    `;

    document.getElementById('viewResultsBtn').addEventListener('click', () => {
        displayTestResults(results);
    });

    launchConfetti();
}

function displayTestResults(results) {
    const container = document.getElementById('testContent');
    if (!container) return;

    container.innerHTML = `
        <div class="results-container">
            <h2>테스트 결과</h2>
            
            <div class="trait-chart-section">
                <h3>리더십 Trait 분석</h3>
                <div id="traitChart" class="trait-percentage-chart"></div>
            </div>
            
            <div class="primary-result">
                <h3>주요 Trait</h3>
                <div class="primary-trait-display">
                    <span class="trait-badge">${results.primary_trait.trait_id}</span>
                    <span class="trait-name">${results.primary_trait.name}</span>
                </div>
                <p class="trait-description">${results.primary_trait.description}</p>
            </div>
            
            <div class="strengths-risks">
                <div class="strengths-box">
                    <h4>강점 (Strengths)</h4>
                    <ul>
                        ${results.strengths.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
                <div class="risks-box">
                    <h4>리스크 (Risks)</h4>
                    <ul>
                        ${results.risks.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
            </div>
            
            ${results.negative_traits && results.negative_traits.length > 0 ? `
                <div class="negative-section">
                    <h4>⚠️ 주의 필요 Trait</h4>
                    <div class="negative-traits-list">
                        ${results.negative_traits.map(nt => `
                            <div class="negative-trait-item">
                                <span class="trait-badge danger">${nt.trait_id}</span>
                                <span>${nt.name}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="action-buttons">
                <button id="restartTestBtn" class="btn btn-secondary">다시 테스트하기</button>
                <button id="saveResultBtn" class="btn btn-primary">결과 저장</button>
            </div>
        </div>
    `;

    renderTraitChart(results.trait_percentages);

    document.getElementById('restartTestBtn').addEventListener('click', () => {
        location.reload();
    });

    document.getElementById('saveResultBtn').addEventListener('click', () => {
        saveTestResult(results);
    });

    launchConfetti();
}

function renderTraitChart(traitPercentages) {
    const chartContainer = document.getElementById('traitChart');
    if (!chartContainer || !traitPercentages) return;

    const colors = [
        'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
    ];

    chartContainer.innerHTML = traitPercentages.map((trait, idx) => `
        <div class="trait-bar-item">
            <div class="trait-bar-label">${trait.trait_id}</div>
            <div class="trait-bar-container">
                <div class="trait-bar-fill" style="width: ${trait.percentage}%; background: ${colors[idx % colors.length]}">
                    <span>${trait.percentage}%</span>
                </div>
            </div>
            <div class="trait-bar-percent">${trait.percentage}%</div>
        </div>
    `).join('');
}

function launchConfetti() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js';
    script.onload = () => {
        const duration = 3000;
        const end = Date.now() + duration;

        const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'];

        (function frame() {
            confetti({
                particleCount: 3,
                angle: 60,
                spread: 55,
                origin: { x: 0 },
                colors: colors
            });
            confetti({
                particleCount: 3,
                angle: 120,
                spread: 55,
                origin: { x: 1 },
                colors: colors
            });

            if (Date.now() < end) {
                requestAnimationFrame(frame);
            }
        }());
    };
    document.head.appendChild(script);
}

async function saveTestResult(results) {
    try {
        const response = await fetch('/api/test/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(results)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('결과가 저장되었습니다.');
        } else {
            alert('저장에 실패했습니다: ' + (data.error || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('저장 중 오류가 발생했습니다: ' + error.message);
    }
}

async function startTest(type) {
    const testData = await testManager.loadTest(type);
    
    if (!testData) {
        alert('테스트를 불러오는 데 실패했습니다.');
        return;
    }

    renderTestHeader(testData);
    renderCurrentQuestion();
    updateNavigation();
}

function renderCurrentQuestion() {
    const question = testManager.getCurrentQuestion();
    const progress = testManager.getProgress();

    renderProgressBar(progress);

    if (!question) return;

    switch(testManager.currentTest) {
        case 'quiz':
            renderQuizQuestion(question);
            break;
        case 'situation':
            renderSituationQuestion(question);
            break;
        case 'hybrid':
            renderHybridQuestion(question);
            break;
        case 'negative':
            renderNegativeQuestion(question);
            break;
    }

    updateNavigation();
}

function handleAnswer() {
    let answerData;

    switch(testManager.currentTest) {
        case 'quiz':
        case 'negative':
            const selectedOption = document.querySelector('input[name="answer"]:checked');
            if (selectedOption) {
                const optionEl = selectedOption.closest('.option-item');
                answerData = {
                    option_id: selectedOption.value,
                    option_text: optionEl.querySelector('.option-text').textContent
                };
            }
            break;
        case 'situation':
            const textarea = document.getElementById('situationAnswer');
            if (textarea) {
                answerData = {
                    text: textarea.value
                };
            }
            break;
        case 'hybrid':
            const selectedHybrid = document.querySelector('input[name="answer"]:checked');
            if (selectedHybrid) {
                const optionEl = selectedHybrid.closest('.option-item');
                answerData = {
                    option_id: selectedHybrid.value,
                    option_text: optionEl.querySelector('.option-text').textContent
                };
            }
            break;
    }

    if (answerData) {
        const question = testManager.getCurrentQuestion();
        testManager.saveAnswer(question.id, answerData);
    }
}

async function submitCurrentAnswer() {
    handleAnswer();
    
    if (testManager.nextQuestion()) {
        renderCurrentQuestion();
    } else {
        const results = await testManager.submitTest();
        if (results.error) {
            alert('결과 처리 중 오류: ' + results.error);
        } else {
            showTestComplete(results);
        }
    }
}

function prevQuestion() {
    if (testManager.prevQuestion()) {
        renderCurrentQuestion();
    }
}

function updateNavigation() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progress = testManager.getProgress();

    if (prevBtn) {
        prevBtn.disabled = progress.current <= 1;
    }

    if (nextBtn && submitBtn) {
        const isLast = progress.current >= progress.total;
        nextBtn.style.display = isLast ? 'none' : 'inline-block';
        submitBtn.style.display = isLast ? 'inline-block' : 'none';
    }
}

window.testManager = testManager;
window.startTest = startTest;
window.submitCurrentAnswer = submitCurrentAnswer;
window.prevQuestion = prevQuestion;
window.renderCurrentQuestion = renderCurrentQuestion;
window.launchConfetti = launchConfetti;
