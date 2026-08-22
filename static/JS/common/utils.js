/**
 * Django CSRF 토큰을 쿠키에서 추출하는 공통 함수
 * @param {string} name - 가져올 쿠키의 이름 (기본값: 'csrftoken')
 * @returns {string|null} - 쿠키 값
 */
function getCookie(name = 'csrftoken') {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // 이름으로 시작하는 쿠키를 찾음
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 다른 모듈이나 인라인 스크립트에서도 쓸 수 있도록 window 객체에 할당 (선택적)
window.getCookie = getCookie;