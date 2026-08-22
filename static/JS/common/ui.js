document.addEventListener("DOMContentLoaded", function() {
    // 사이드바 토글 로직
    const sidebar = document.getElementById('sidebar-drawer');
    const toggleBtn = document.getElementById('btn-toggle-sidebar');

    if (sidebar && toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            if (sidebar.classList.contains('w-64')) {
                // 닫기
                sidebar.classList.remove('w-64');
                sidebar.classList.add('w-0', 'border-r-0');
            } else {
                // 열기
                sidebar.classList.add('w-64');
                sidebar.classList.remove('w-0', 'border-r-0');
            }
        });
    }

    // (추가 확장 가능) 전역 모달 닫기 이벤트(ESC 키 등)를 여기에 추가할 수 있습니다.
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.fixed.inset-0:not(.hidden)');
            modals.forEach(modal => modal.classList.add('hidden'));
        }
    });
});