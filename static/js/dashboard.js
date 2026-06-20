/**
 * Dashboard JavaScript - Enhanced with Period & Metadata Filters
 */

let traitRadarChart = null;
let traitPercentageChart = null;
let posNegChart = null;
let negTraitChart = null;
let trendChart = null;
let currentPeriod = 'all';
let currentFilters = {
    department: '',
    position: '',
    job_level: ''
};

document.addEventListener('DOMContentLoaded', async function() {
    initPeriodTabs();
    initFilterTabs();
    await loadDashboardData();
    await loadFilterOptions();
});

function initPeriodTabs() {
    document.querySelectorAll('.period-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.period-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentPeriod = this.dataset.period;
            loadDashboardData();
        });
    });
}

function initFilterTabs() {
    document.getElementById('applyFilterBtn').addEventListener('click', applyFilters);
    document.getElementById('clearFilterBtn').addEventListener('click', clearFilters);
}

async function loadFilterOptions() {
    try {
        const response = await fetch('/api/metadata/users');
        const data = await response.json();
        
        const departments = new Set();
        const positions = new Set();
        const jobLevels = new Set();
        
        data.users.forEach(u => {
            if (u.department) departments.add(u.department);
            if (u.position) positions.add(u.position);
            if (u.job_level) jobLevels.add(u.job_level);
        });
        
        const deptSelect = document.getElementById('departmentFilter');
        departments.forEach(d => {
            deptSelect.innerHTML += `<option value="${d}">${d}</option>`;
        });
        
        const posSelect = document.getElementById('positionFilter');
        positions.forEach(p => {
            posSelect.innerHTML += `<option value="${p}">${p}</option>`;
        });
        
        const levelSelect = document.getElementById('jobLevelFilter');
        jobLevels.forEach(l => {
            levelSelect.innerHTML += `<option value="${l}">${l}</option>`;
        });
        
    } catch (error) {
        console.error('필터 옵션 로드 실패:', error);
    }
}

function applyFilters() {
    currentFilters.department = document.getElementById('departmentFilter').value;
    currentFilters.position = document.getElementById('positionFilter').value;
    currentFilters.job_level = document.getElementById('jobLevelFilter').value;
    loadDashboardData();
}

function clearFilters() {
    document.getElementById('departmentFilter').value = '';
    document.getElementById('positionFilter').value = '';
    document.getElementById('jobLevelFilter').value = '';
    currentFilters = { department: '', position: '', job_level: '' };
    loadDashboardData();
}

async function loadDashboardData() {
    try {
        let url = `/api/dashboard/stats?period=${currentPeriod}`;
        
        // 필터 파라미터 추가
        if (currentFilters.department) {
            url += `&department=${encodeURIComponent(currentFilters.department)}`;
        }
        if (currentFilters.position) {
            url += `&position=${encodeURIComponent(currentFilters.position)}`;
        }
        if (currentFilters.job_level) {
            url += `&job_level=${encodeURIComponent(currentFilters.job_level)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        renderSummary(data.summary);
        renderCharts(data.data);
        renderRecentTable(data.recent_analyses);
        
    } catch (error) {
        console.error('대시보드 데이터 로드 실패:', error);
    }
}

function renderSummary(summary) {
    document.getElementById('sumTotal').textContent = summary.total_analyses || 0;
    document.getElementById('sumAvg').textContent = summary.avg_per_day || 0;
    document.getElementById('sumYesterday').textContent = summary.yesterday_analyses || 0;
    
    const topTraitEl = document.getElementById('sumTopTrait');
    if (summary.top_trait) {
        topTraitEl.textContent = `${summary.top_trait.trait_id} (${summary.top_trait.percentage}%)`;
    } else {
        topTraitEl.textContent = '-';
    }
    
    document.getElementById('sumPositive').textContent = summary.positive_rate || 0;
    document.getElementById('sumNegative').textContent = summary.negative_trait_count || 0;
    document.getElementById('sumLast').textContent = summary.last_analysis || '-';
}

function renderCharts(data) {
    renderTraitRadarChart(data.trait_percentages);
    renderTraitPercentageChart(data.trait_percentages);
    renderPosNegChart(data.positive_negative);
    renderNegTraitChart(data.negative_trait_count);
    renderTrendChart(data.trait_trend, data.daily_trend);
}

function renderTraitRadarChart(traitData) {
    const ctx = document.getElementById('traitRadarChart').getContext('2d');
    
    // Trait 이름 매핑
    const traitNames = {
        'T01': '비전 제시', 'T02': '関係構築', 'T03': '변화牵引',
        'T04': '의사결정', 'T05': '데이터 기반', 'T06': '프로세스',
        'T07': '인재 개발', 'T08': '감성 지능', 'T09': '영감을주는',
        'T10': '목표 달성', 'T11': '沟通', 'T12': '적응력'
    };
    
    // 모든 Trait에 대해 데이터准备 (8개为中心)
    const allTraits = ['T01', 'T02', 'T03', 'T04', 'T05', 'T06', 'T07', 'T08', 'T09', 'T10', 'T11', 'T12'];
    
    const labels = [];
    const dataValues = [];
    
    allTraits.forEach(trait => {
        const traitInfo = traitData.find(t => t.trait_id === trait);
        labels.push(traitNames[trait] || trait);
        dataValues.push(traitInfo ? traitInfo.percentage : 0);
    });
    
    if (traitRadarChart) traitRadarChart.destroy();
    
    traitRadarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Trait 비율 (%)',
                data: dataValues,
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                borderColor: '#667eea',
                borderWidth: 2,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    pointLabels: {
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

function renderTraitPercentageChart(traitData) {
    const ctx = document.getElementById('traitPercentageChart').getContext('2d');
    
    const labels = traitData.map(t => `${t.trait_id}: ${t.name || t.trait_id}`);
    const percentages = traitData.map(t => t.percentage);
    
    const colors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c',
        '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
        '#fa709a', '#fee140'
    ];
    
    if (traitPercentageChart) traitPercentageChart.destroy();
    
    traitPercentageChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '%',
                data: percentages,
                backgroundColor: colors.slice(0, labels.length),
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function renderPosNegChart(posNegData) {
    const ctx = document.getElementById('posNegChart').getContext('2d');
    
    if (posNegChart) posNegChart.destroy();
    
    posNegChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative'],
            datasets: [{
                data: [posNegData.positive, posNegData.negative],
                backgroundColor: ['#43e97b', '#f5576c'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
}

function renderNegTraitChart(count) {
    const ctx = document.getElementById('negTraitChart').getContext('2d');
    
    if (negTraitChart) negTraitChart.destroy();
    
    negTraitChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['부정 Trait 감지 수'],
            datasets: [{
                data: [count],
                backgroundColor: count > 0 ? '#f5576c' : '#ccc',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderTrendChart(traitTrend, dailyTrend) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) trendChart.destroy();
    
    if (traitTrend && traitTrend.length > 0) {
        // Trait별 추이 (Group by period)
        const periods = [...new Set(traitTrend.map(t => t.period))].sort();
        const traits = [...new Set(traitTrend.map(t => t.trait_id))];
        
        const datasets = traits.map((trait, idx) => {
            const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140'];
            return {
                label: trait,
                data: periods.map(p => {
                    const item = traitTrend.find(t => t.period === p && t.trait_id === trait);
                    return item ? item.percentage : 0;
                }),
                borderColor: colors[idx % colors.length],
                backgroundColor: 'transparent',
                tension: 0.3
            };
        });
        
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: periods,
                datasets: datasets
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    } else if (dailyTrend && dailyTrend.length > 0) {
        // 일별 추이만 표시
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dailyTrend.map(d => d.date.slice(5)),
                datasets: [{
                    label: '일별 분석 수',
                    data: dailyTrend.map(d => d.count),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } else {
        // 데이터 없음
        ctx.font = '14px Noto Sans KR';
        ctx.fillStyle = '#999';
        ctx.textAlign = 'center';
        ctx.fillText('데이터가 없습니다', ctx.canvas.width / 2, ctx.canvas.height / 2);
    }
}

function renderRecentTable(recentData) {
    const tbody = document.getElementById('recentBody');
    
    if (!recentData || recentData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">분석 결과가 없습니다</td></tr>';
        return;
    }
    
    tbody.innerHTML = recentData.map((item, idx) => {
        const date = item.created_at ? item.created_at.slice(0, 10) : '-';
        const text = item.text || '-';
        const traitBadge = item.primary_trait && item.primary_trait.startsWith('N') 
            ? 'trait-badge warning' 
            : 'trait-badge';
        
        return `
            <tr>
                <td>${idx + 1}</td>
                <td>${item.username || '-'}</td>
                <td><span class="text-preview" title="${escapeHtml(text)}">${escapeHtml(text)}</span></td>
                <td><span class="${traitBadge}">${item.primary_trait} - ${item.primary_name || '-'}</span></td>
                <td>${date}</td>
            </tr>
        `;
    }).join('');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}