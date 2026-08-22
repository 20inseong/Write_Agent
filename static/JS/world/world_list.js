document.addEventListener("DOMContentLoaded", function() {
    // 새 세계관 추가 모달 제어
    const modal = document.getElementById('add-novel-modal');
    const openBtn = document.getElementById('btn-open-add-modal');
    const closeBtn = document.getElementById('btn-close-modal');
    const cancelBtn = document.getElementById('btn-cancel-modal');

    if (modal) {
        if (openBtn) openBtn.addEventListener('click', () => modal.classList.remove('hidden'));
        if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
        if (cancelBtn) cancelBtn.addEventListener('click', () => modal.classList.add('hidden'));
        
        window.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        });
    }

    // 우클릭 컨텍스트 메뉴 제어 (세계관 삭제)
    const contextMenu = document.getElementById('custom-context-menu');
    const deleteForm = document.getElementById('delete-form');
    const deleteTargetName = document.getElementById('delete-target-name');
    const cards = document.querySelectorAll('.novel-card');

    if (contextMenu && deleteForm && deleteTargetName) {
        cards.forEach(card => {
            card.addEventListener('contextmenu', function(e) {
                e.preventDefault(); // 기본 우클릭 메뉴 막기
                
                const deleteUrl = this.getAttribute('data-delete-url');
                const novelName = this.getAttribute('data-name');
                
                deleteForm.action = deleteUrl;
                deleteTargetName.innerText = `'${novelName}' 삭제`;
                
                contextMenu.style.left = `${e.pageX}px`;
                contextMenu.style.top = `${e.pageY}px`;
                contextMenu.classList.remove('hidden');
            });
        });

        // 바탕 클릭 시 커스텀 메뉴 숨기기
        window.addEventListener('click', (e) => {
            if (!contextMenu.contains(e.target)) {
                contextMenu.classList.add('hidden');
            }
        });
    }
});