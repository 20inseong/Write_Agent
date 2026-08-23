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
            ep.style.display = 'flex'; // Tailwind flex 클래스와 맞춤
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
}