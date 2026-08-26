document.addEventListener("DOMContentLoaded", function() {
    // 모달 열기/닫기 제어 (새 요소 추가 모달)
    const addModal = document.getElementById('add-element-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnCancelModal = document.getElementById('btn-cancel-modal');
    const btnOpenAdds = document.querySelectorAll('.btn-open-add');

    if (addModal) {
        btnOpenAdds.forEach(btn => btn.addEventListener('click', () => addModal.classList.remove('hidden')));
        if (btnCloseModal) btnCloseModal.addEventListener('click', () => addModal.classList.add('hidden'));
        if (btnCancelModal) btnCancelModal.addEventListener('click', () => addModal.classList.add('hidden'));
    }


    // [List 페이지] 빵부스러기(Breadcrumb) 네비게이션 렌더링
    const configEl = document.getElementById('world-element-config');
    const breadcrumbContainer = document.getElementById('breadcrumb-container');
    
    if (configEl && breadcrumbContainer) {
        const config = JSON.parse(configEl.textContent);
        let bcHtml = `<a href="${config.worldListUrl}" class="text-slate-400 hover:text-slate-800 transition">내 프로젝트</a>
                      <span class="text-slate-300">/</span>
                      <a href="${config.worldCategoryUrl}" class="text-slate-400 hover:text-slate-800 transition">${config.novelTitle}</a>
                      <span class="text-slate-300">/</span>
                      <a href="?folder=/" class="text-slate-400 hover:text-indigo-600 transition">${config.categoryName}</a>`;
        
        const parts = config.currentFolderStr.split('/').filter(p => p.length > 0);
        let cumulativePath = '/';
        
        parts.forEach((part, index) => {
            cumulativePath += part + '/';
            bcHtml += ` <span class="text-slate-300">/</span> `;
            if (index === parts.length - 1) {
                bcHtml += `<span class="text-indigo-700 font-bold">${part}</span>`;
            } else {
                bcHtml += `<a href="?folder=${cumulativePath}" class="text-slate-400 hover:text-indigo-600 transition">${part}</a>`;
            }
        });
        breadcrumbContainer.innerHTML = bcHtml;
    }

    // 우클릭 컨텍스트 메뉴 및 폴더 제어
    const contextMenu = document.getElementById('custom-context-menu');
    let currentContextElementId = null;
    let contextTargetType = 'element';
    let contextFolderPath = '';

    if (contextMenu) {
        const elementCards = document.querySelectorAll('.element-card');
        const folderCards = document.querySelectorAll('.folder-card');

        elementCards.forEach(card => {
            card.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                contextTargetType = 'element';
                currentContextElementId = this.getAttribute('data-id');
                
                document.getElementById('context-element-actions').classList.remove('hidden');
                document.getElementById('context-delete-text').innerText = '삭제하기';
                
                const targetCheckbox = document.querySelector(`.bulk-checkbox[value="${currentContextElementId}"]`);
                if (targetCheckbox && !targetCheckbox.checked) {
                    document.querySelectorAll('.bulk-checkbox').forEach(cb => cb.checked = false);
                    targetCheckbox.checked = true;
                    document.getElementById('context-target-name').innerText = this.getAttribute('data-name');
                } else {
                    const checkedCount = document.querySelectorAll('.bulk-checkbox:checked').length;
                    document.getElementById('context-target-name').innerText = `선택된 요소 ${checkedCount}개`;
                }
                
                contextMenu.style.left = `${e.pageX}px`;
                contextMenu.style.top = `${e.pageY}px`;
                contextMenu.classList.remove('hidden');
            });
        });

        folderCards.forEach(card => {
            card.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                contextTargetType = 'folder';
                contextFolderPath = this.getAttribute('data-folder-path');
                
                document.getElementById('context-element-actions').classList.add('hidden'); 
                document.getElementById('context-target-name').innerText = `📁 ${this.getAttribute('data-folder-name')}`;
                document.getElementById('context-delete-text').innerText = '폴더 일괄 삭제';
                
                contextMenu.style.left = `${e.pageX}px`;
                contextMenu.style.top = `${e.pageY}px`;
                contextMenu.classList.remove('hidden');
            });
        });

        // 바탕 클릭 시 모달 및 우클릭 메뉴 숨김
        const createFolderModal = document.getElementById('create-folder-modal');
        window.addEventListener('click', (e) => {
            if (addModal && e.target === addModal) addModal.classList.add('hidden');
            if (createFolderModal && e.target === createFolderModal) createFolderModal.classList.add('hidden');
            if (contextMenu && !contextMenu.contains(e.target)) contextMenu.classList.add('hidden');
        });
    }

    // 전역 이벤트 위임 (인라인 onclick 대체)
    // HTML에 하드코딩된 onclick 속성들을 굳이 지우지 않더라도 작동하도록 전역에서 가로챕니다.
    window.openCreateFolderModal = function() {
        const modal = document.getElementById('create-folder-modal');
        if(modal) {
            modal.classList.remove('hidden');
            document.getElementById('new-folder-input').focus();
        }
    };

    window.closeCreateFolderModal = function() {
        const modal = document.getElementById('create-folder-modal');
        if(modal) {
            modal.classList.add('hidden');
            document.getElementById('new-folder-input').value = '';
        }
    };

    window.submitCreateFolder = function() {
        const folderName = document.getElementById('new-folder-input').value;
        const configStr = configEl ? JSON.parse(configEl.textContent).currentFolderStr : '/';
        
        if (folderName && folderName.trim() !== "") {
            const cleanName = folderName.replace(/\//g, "").trim(); 
            const newFolderPath = `${configStr}${cleanName}/`;

            const form = document.createElement('form');
            form.method = 'POST';
            form.action = window.location.pathname + `?folder=${newFolderPath}`;
            
            const csrfToken = window.getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            form.innerHTML = `
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <input type="hidden" name="name" value="__FOLDER_DUMMY__">
                <input type="hidden" name="keyword_name" value="dummy">
            `;
            document.body.appendChild(form);
            form.submit();
        }
    };

    window.executeAction = function(actionType) {
        document.getElementById('form-action').value = actionType;
        document.getElementById('action-form').submit();
    };

    window.submitBulkAction = function(actionType) {
        const checked = document.querySelectorAll('.bulk-checkbox:checked');
        if (checked.length === 0) {
            alert("선택된 요소가 없습니다. 체크박스를 선택해주세요.");
            return;
        }
        if (actionType === 'delete' && !confirm(`선택한 ${checked.length}개의 요소를 삭제하시겠습니까?`)) return;
        window.executeAction(actionType);
    };

    window.triggerContextAction = function(actionType) {
        if(contextMenu) contextMenu.classList.add('hidden');
        if (contextTargetType === 'folder' && actionType === 'delete') {
            if (confirm("🚨 [경고] 정말 이 폴더를 삭제하시겠습니까?\n\n폴더 안의 모든 하위 요소들이 함께 삭제됩니다. 되돌릴 수 없습니다.")) {
                document.getElementById('form-is-folder-action').value = "true";
                document.getElementById('form-action-target-folder').value = contextFolderPath;
                window.executeAction('delete');
            }
        } 
        else if (contextTargetType === 'element') {
            const checkedCount = document.querySelectorAll('.bulk-checkbox:checked').length;
            if (actionType === 'move') {
                window.openFolderModal(); 
            } else {
                const msg = checkedCount > 1 ? `선택한 ${checkedCount}개의 요소를 삭제하시겠습니까?` : "이 요소를 삭제하시겠습니까?";
                if (actionType === 'delete' && !confirm(msg)) return;
                window.executeAction(actionType);
            }
        }
    };

    window.openFolderModal = function() {
        const checkedCount = document.querySelectorAll('.bulk-checkbox:checked').length;
        if (checkedCount === 0) {
            alert("이동할 요소를 먼저 선택해주세요.");
            return;
        }
        document.getElementById('move-folder-modal').classList.remove('hidden');
    };

    window.closeFolderModal = function() {
        document.getElementById('move-folder-modal').classList.add('hidden');
    };

    window.confirmMoveAction = function() {
        const folderPath = document.getElementById('target-folder-input').value.trim() || '/';
        document.getElementById('form-target-folder').value = folderPath;
        window.executeAction('move');
    };

    window.generateRandomBirthday = function(event) {
        const year = Math.floor(Math.random() * 2000) + 500;
        const month = Math.floor(Math.random() * 12) + 1;
        const day = Math.floor(Math.random() * 28) + 1;
        const hour = Math.floor(Math.random() * 24);

        const randomDateStr = `${year}년 ${month}월 ${day}일 ${hour}시`;
        const inputBirthday = document.getElementById('input-birthday');
        if (inputBirthday) inputBirthday.value = randomDateStr;
        
        const btn = event.currentTarget;
        const originalText = btn.innerText;
        btn.innerText = "✅ 완료!";
        btn.classList.add("bg-emerald-100", "text-emerald-700");
        
        setTimeout(() => { 
            btn.innerText = originalText; 
            btn.classList.remove("bg-emerald-100", "text-emerald-700");
        }, 800);
    };

    // [Detail 페이지] 수정/저장 모드 전환 토글
    const toggleBtn = document.getElementById('btn-edit-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            if (toggleBtn.innerText === '수정하기') {
                e.preventDefault(); 
                document.querySelectorAll('.view-mode').forEach(el => el.classList.add('hidden'));
                document.querySelectorAll('.edit-mode').forEach(el => el.classList.remove('hidden'));
                
                toggleBtn.innerText = '저장하기';
                toggleBtn.type = 'submit'; 
                toggleBtn.classList.remove('bg-slate-100', 'text-slate-600', 'hover:bg-slate-200');
                toggleBtn.classList.add('bg-indigo-600', 'text-white', 'hover:bg-indigo-700', 'shadow-md');
            }
        });
    }
});