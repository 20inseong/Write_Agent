// 탭 전환 제어
function switchTab(tabName) {
    const archiveTab = document.getElementById('tab-archive');
    const settingsTab = document.getElementById('tab-settings');
    const archiveContent = document.getElementById('content-archive');
    const settingsContent = document.getElementById('content-settings');

    const activeClass = "py-2 px-6 text-lg font-semibold text-purple-600 border-b-2 border-purple-600 focus:outline-none";
    const inactiveClass = "py-2 px-6 text-lg font-semibold text-gray-500 hover:text-purple-600 focus:outline-none";

    if (tabName === 'archive') {
        archiveTab.className = activeClass;
        settingsTab.className = inactiveClass;
        archiveContent.classList.remove('hidden');
        settingsContent.classList.add('hidden');
    } else {
        settingsTab.className = activeClass;
        archiveTab.className = inactiveClass;
        settingsContent.classList.remove('hidden');
        archiveContent.classList.add('hidden');
    }
}

// 비동기 설정 업데이트 (Temperature 등)
function saveSettings(data) {
    fetch(window.SettingsConfig.updateApiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCookie('csrftoken') 
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('설정 저장 완료:', data.message);
        } else {
            console.error('저장 실패:', data.message);
        }
    })
    .catch(error => console.error('통신 에러:', error));
}

// AI 창의성 슬라이더 이벤트 바인딩
document.addEventListener('DOMContentLoaded', function() {
    const temperatureSlider = document.getElementById('temp-slider');
    const tempDisplay = document.getElementById('temp-display');

    if (temperatureSlider && tempDisplay) {
        // 드래그하는 동안 실시간으로 숫자 텍스트 변경
        temperatureSlider.addEventListener('input', function(e) {
            tempDisplay.textContent = e.target.value;
        });

        // 마우스를 뗐을 때(최종 값 확정) 백엔드에 저장
        temperatureSlider.addEventListener('change', function(e) {
            const tempValue = parseFloat(e.target.value);
            saveSettings({ ai_temperature: tempValue });
        });
    }
});

// 회원 탈퇴 (소프트 딜리트) 제어
function confirmDeleteAccount() {
    if (confirm("정말로 탈퇴하시겠습니까? (작성하신 데이터는 안전하게 보관되지만 계정은 비활성화됩니다.)")) {
        fetch(window.SettingsConfig.deleteApiUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert("계정이 성공적으로 비활성화되었습니다. 이용해 주셔서 감사합니다.");
                window.location.href = window.SettingsConfig.homeUrl; 
            } else {
                alert("오류가 발생했습니다: " + data.message);
            }
        })
        .catch(error => console.error('통신 에러:', error));
    }
}

// 작품 보관함 에피소드 필터링 제어
function filterEpisodes(novelId) {
    // 좌측 버튼 스타일 변경 (선택된 버튼 강조)
    const allBtns = document.querySelectorAll('.novel-filter-btn');
    allBtns.forEach(btn => {
        if (btn.dataset.novelId === novelId.toString()) {
            btn.classList.add('bg-purple-200', 'font-bold');
            btn.classList.remove('bg-gray-50');
        } else {
            btn.classList.remove('bg-purple-200', 'font-bold');
            btn.classList.add('bg-gray-50');
        }
    });

    // 우측 에피소드 숨김/표시 처리
    const episodes = document.querySelectorAll('.episode-item');
    let visibleCount = 0;

    episodes.forEach(ep => {
        // '전체 보기'이거나 해당 소설 ID와 일치하면 보여줌
        if (novelId === 'all' || ep.dataset.novelId === novelId.toString()) {
            ep.style.display = 'flex';
            visibleCount++;
        } else {
            ep.style.display = 'none';
        }
    });

    // 필터링 결과가 0개일 때 안내 메시지 출력
    const emptyMsg = document.getElementById('empty-episode-msg');
    if (emptyMsg) {
        if (visibleCount === 0) {
            emptyMsg.classList.remove('hidden');
        } else {
            emptyMsg.classList.add('hidden');
        }
    }

    // 우측 블록 숨김/표시 처리
    const drafts = document.querySelectorAll('.draft-item');
    let visibleDraftCount = 0;

    drafts.forEach(draft => {
        if (novelId === 'all' || draft.dataset.novelId === novelId.toString()) {
            draft.style.display = 'block'; 
            visibleDraftCount++;
        } else {
            draft.style.display = 'none';
        }
    });

    const emptyDraftMsg = document.getElementById('empty-draft-msg');
    if (emptyDraftMsg) {
        if (visibleDraftCount === 0) {
            emptyDraftMsg.classList.remove('hidden');
        } else {
            emptyDraftMsg.classList.add('hidden');
        }
    }
}

function openBlockModal(element) {
    // 숨겨둔 JSON 데이터 가져오기
    const contextData = element.getAttribute('data-context');
    const modalContent = document.getElementById('block-modal-content');

    const promptLabels = {
        "goal_chars": "목표 글자수",
        "characters": "상황 키워드",
        "start": "시작점",
        "situation": "상황",
        "climax": "절정",
        "next": "다음 블록 연결",
    };
    
    // 내용 초기화
    modalContent.innerHTML = '';

    try {
        if (!contextData || contextData === 'null' || contextData === '[]') {
            modalContent.innerHTML = '<p class="text-gray-500 text-center py-8">저장된 상세 지시사항이 없습니다.</p>';
        } else {
            // JSON 문자열을 자바스크립트 객체(배열)로 변환
            const blocks = JSON.parse(contextData);
            
            // 각 블록(방)마다 예쁜 HTML 상자 만들기
            blocks.forEach((block, index) => {
                let blockHtml = `<div class="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
                                    <h4 class="font-bold text-purple-700 mb-3 border-b pb-2">블록 ${index + 1}</h4>
                                    <ul class="space-y-2 text-sm text-gray-700">`;
                
                // 블록 안의 항목(ex: 목표, 분위기 등)을 리스트로 출력
                for (const [key, value] of Object.entries(block)) {
                    if (value && value.trim() !== '') {
                        const displayKey = promptLabels[key] || key;
                        blockHtml += `<li><span class="font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded mr-2">${displayKey}</span> ${value}</li>`;
                    }
                }
                blockHtml += `</ul></div>`;
                modalContent.innerHTML += blockHtml;
            });
        }
    } catch (e) {
        console.error("블록 데이터 파싱 에러:", e);
        modalContent.innerHTML = '<p class="text-red-500 text-center py-8">데이터를 불러오는 중 오류가 발생했습니다.</p>';
    }

    // 4. 모달창 화면에 표시
    document.getElementById('block-detail-modal').classList.remove('hidden');
}

// 블록 모달 닫기
function closeBlockModal() {
    document.getElementById('block-detail-modal').classList.add('hidden');
}