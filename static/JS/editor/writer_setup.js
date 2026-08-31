document.addEventListener("DOMContentLoaded", function() {
    // 1. Django 템플릿 설정값 파싱
    const configEl = document.getElementById('writer-setup-config');
    const config = configEl ? JSON.parse(configEl.textContent) : { savedSetupContext: "", verifyApiUrl: "", addBlockUrl: "" };

    let snapshotsList = [];
    let selectedSnapshotContext = null;

    try {
        if (config.savedSetupContext && config.savedSetupContext !== "{}" && config.savedSetupContext !== "None") {
            snapshotsList = JSON.parse(config.savedSetupContext);
        }
    } catch (e) {
        console.error("복원 데이터 파싱 에러:", e);
    }

    // --- [모달 및 불러오기 제어] ---
    const loadModal = document.getElementById('load-blocks-modal');
    const btnOpenLoad = document.getElementById('btn-open-load-modal');
    const btnCloseLoad = document.getElementById('btn-close-load-modal');
    const btnCancelLoad = document.getElementById('btn-cancel-load');
    const btnApplyLoad = document.getElementById('btn-apply-load');
    const blocksListContainer = document.getElementById('saved-blocks-list');

    if (btnOpenLoad && loadModal && blocksListContainer && btnApplyLoad) {
        btnOpenLoad.addEventListener('click', () => {
            if (snapshotsList.length === 0) {
                blocksListContainer.innerHTML = `<div class="text-center text-slate-400 py-8 font-medium">최근 저장된 블록 데이터가 없습니다.</div>`;
                btnApplyLoad.disabled = true;
                btnApplyLoad.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                btnApplyLoad.disabled = true;
                btnApplyLoad.classList.add('opacity-50', 'cursor-not-allowed');
                
                blocksListContainer.innerHTML = snapshotsList.map((snap, index) => {
                    const blockCount = snap.context.length;
                    const ctx = blockCount > 0 ? snap.context[0] : {};
                    const firstBlockKeyword = ctx.characters || "키워드 미입력";
                    const firstBlockSituation = ctx.situation || ctx.start || "상황 미입력";
                    
                    return `
                    <label class="cursor-pointer block mb-3">
                      <input type="radio" name="snapshot_select" value="${index}" class="peer sr-only">
                      <div class="bg-white border-2 border-slate-200 rounded-lg p-4 shadow-sm transition hover:border-indigo-300 peer-checked:border-indigo-600 peer-checked:bg-indigo-50 peer-checked:ring-1 peer-checked:ring-indigo-600 flex flex-col gap-2">
                        <div class="flex justify-between items-center mb-1">
                          <span class="text-indigo-700 font-bold text-sm">📅 ${snap.created_at} 저장본</span>
                          <span class="text-xs font-semibold bg-slate-100 text-slate-500 px-2 py-1 rounded">총 ${blockCount}개 블록</span>
                        </div>
                        <p class="text-sm text-slate-700 line-clamp-1"><strong class="text-slate-500">키워드:</strong> ${firstBlockKeyword}</p>
                        <p class="text-sm text-slate-700 line-clamp-2"><strong class="text-slate-500">상황:</strong> ${firstBlockSituation}</p>
                      </div>
                    </label>`;
                }).join('');

                const radios = blocksListContainer.querySelectorAll('input[name="snapshot_select"]');
                radios.forEach(radio => {
                    radio.addEventListener('change', (e) => {
                        const selectedIdx = e.target.value;
                        selectedSnapshotContext = snapshotsList[selectedIdx].context;
                        btnApplyLoad.disabled = false;
                        btnApplyLoad.classList.remove('opacity-50', 'cursor-not-allowed');
                    });
                });
            }
            loadModal.classList.remove('hidden');
        });

        const closeLoadModal = () => loadModal.classList.add('hidden');
        if (btnCloseLoad) btnCloseLoad.addEventListener('click', closeLoadModal);
        if (btnCancelLoad) btnCancelLoad.addEventListener('click', closeLoadModal);

        btnApplyLoad.addEventListener('click', async () => {
            if (!selectedSnapshotContext) {
                alert("먼저 복원할 저장본을 리스트에서 선택해주세요!");
                return;
            }
            if (!confirm("현재 작성 중인 폼 내용이 초기화되고 선택한 데이터로 덮어씌워집니다. 진행하시겠습니까?")) return;
            
            closeLoadModal();
            
            fillBlockData(1, selectedSnapshotContext[0]);

            for (let i = 1; i < selectedSnapshotContext.length; i++) {
                const btn = document.getElementById("add-block-btn");
                if (!btn) continue;

                btn.setAttribute("hx-get", `${config.addBlockUrl}?index=${i + 1}`);
                
                await new Promise(resolve => {
                    if (typeof htmx !== 'undefined') htmx.process(btn);
                    if (typeof htmx !== 'undefined') htmx.trigger(btn, "click");
                    document.body.addEventListener("htmx:afterSettle", function onSettle() {
                        document.body.removeEventListener("htmx:afterSettle", onSettle);
                        resolve();
                    }, { once: true });
                });
                fillBlockData(i + 1, selectedSnapshotContext[i]);
            }
            updateBlockNumbers();
        });
    }

    function fillBlockData(blockNum, data) {
        if (!data) return;
        for (const [key, value] of Object.entries(data)) {
            const fieldName = `${key}_${blockNum}`;
            const inputEl = document.querySelector(`[name="${fieldName}"]`);
            if (inputEl) inputEl.value = value;
        }
    }

    // --- [HTMX 이벤트 제어] ---
    document.body.addEventListener("htmx:afterSwap", function (event) {
        if (event.detail.target.id !== "blocks-container") return;
        const btn = document.getElementById("add-block-btn");
        if (!btn) return;

        const blocks = document.querySelectorAll("#blocks-container [data-block-index]");
        const nextIndex = blocks.length + 1;
        btn.setAttribute("hx-get", `${config.addBlockUrl}?index=${nextIndex}`);
        if (typeof htmx !== 'undefined') htmx.process(btn);
    });

    function updateBlockNumbers() {
        const blocks = document.querySelectorAll('.input-block'); 
        blocks.forEach((block, index) => {
            const actualNumber = index + 1;
            const titleLabel = block.querySelector('.block-title'); 
            if (titleLabel) {
                titleLabel.textContent = `입력 블록 #${actualNumber}`;
            }

            const inputs = block.querySelectorAll('input:not([type="hidden"]), textarea');
            inputs.forEach(input => {
                const oldName = input.getAttribute('name');
                if (oldName) {
                    const baseName = oldName.substring(0, oldName.lastIndexOf('_'));
                    input.setAttribute('name', `${baseName}_${actualNumber}`);
                }

                const oldId = input.getAttribute('id');
                if (oldId) {
                    const baseId = oldId.substring(0, oldId.lastIndexOf('-'));
                    const newId = `${baseId}-${actualNumber}`;
                    input.setAttribute('id', newId);
                    
                    const label = block.querySelector(`label[for="${oldId}"]`);
                    if (label) {
                        label.setAttribute('for', newId);
                    }
                }
            });
        });

        const addBtn = document.getElementById('add-block-btn');
        if (addBtn) {
            const nextIndex = blocks.length + 1;
            addBtn.setAttribute('hx-get', `${config.addBlockUrl}?index=${nextIndex}`);
            if (typeof htmx !== 'undefined') htmx.process(addBtn); 
        }
    }

    document.body.addEventListener('htmx:afterSettle', function(event) {
        updateBlockNumbers();
    });

    // --- [폼 검증 및 전송 (RAG)] ---
    const form = document.getElementById('editor-setup-form');
    if (form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = "AI 초안 생성 시작";

        let tipText = document.getElementById('ai-tip-text');
        if (!tipText && submitBtn) {
            tipText = document.createElement('p');
            tipText.id = 'ai-tip-text';
            tipText.className = 'mb-4 text-sm font-bold text-indigo-500 text-center transition-all duration-300 opacity-0 h-0 overflow-hidden';
            tipText.innerText = '💡 팁: 빈칸을 모두 구체적으로 채우면 AI가 훨씬 정교한 초안을 완성합니다.';
            submitBtn.parentNode.insertBefore(tipText, submitBtn);
        }

        const urlParams = new URLSearchParams(window.location.search);
        const isRandomMode = urlParams.get('mode') === 'random';

        if (isRandomMode && submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = originalBtnText;
        } else {
            const checkInputs = () => {
                if (!submitBtn) return;
                const inputs = form.querySelectorAll('input:not([type="hidden"]):not([type="number"]):not(.quick-input), textarea:not(.quick-input)');
                let filledCount = 0;
                let totalCount = 0;

                inputs.forEach(input => {
                    totalCount++;
                    if (input.value.trim() !== '') filledCount++;
                });

                if (filledCount === 0) {
                    submitBtn.disabled = true;
                    submitBtn.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
                    submitBtn.classList.add('opacity-50', 'cursor-not-allowed', 'bg-slate-400');
                    submitBtn.innerText = '블록 내용을 입력해주세요 🔒';
                    if (tipText) {
                        tipText.classList.remove('opacity-100', 'h-5');
                        tipText.classList.add('opacity-0', 'h-0');
                    }
                } else if (filledCount > 0 && filledCount < totalCount) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed', 'bg-slate-400');
                    submitBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
                    submitBtn.innerText = originalBtnText;
                    if (tipText) {
                        tipText.classList.remove('opacity-0', 'h-0');
                        tipText.classList.add('opacity-100', 'h-5');
                    }
                } else if (filledCount === totalCount) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed', 'bg-slate-400');
                    submitBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
                    submitBtn.innerText = originalBtnText;
                    if (tipText) {
                        tipText.classList.remove('opacity-100', 'h-5');
                        tipText.classList.add('opacity-0', 'h-0');
                    }
                }
            };

            const blocksContainer = document.getElementById('blocks-container');
            if (blocksContainer) {
                const observer = new MutationObserver(function() { checkInputs(); });
                observer.observe(blocksContainer, { childList: true, subtree: true });
            }
            checkInputs();
            form.addEventListener('input', checkInputs);
        }

        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingMessage = document.getElementById('loading-message');
        const keywordModal = document.getElementById('keyword-modal');
        const unregisteredList = document.getElementById('unregistered-list');
        
        const inputAction = document.getElementById('unregistered_action');
        const inputKeywords = document.getElementById('unregistered_keywords');
        const inputManualData = document.getElementById('manual_setup_data');

        const quickSetupBox = document.getElementById('quick-setup-box');
        const quickSetupWord = document.getElementById('quick-setup-word');
        const quickCategory = document.getElementById('quick-category');
        const dynamicFormContainer = document.getElementById('dynamic-form-container'); 
        const btnQuickSave = document.getElementById('btn-quick-save');
        const btnQuickCancel = document.getElementById('btn-quick-cancel');
        const btnManualComplete = document.getElementById('btn-modal-manual-complete');
        
        let isVerified = false; 
        let currentKeywords = [];
        let manualData = {}; 
        let currentlyEditingWord = "";

        function showLoading(msg) {
            if (msg && loadingMessage) loadingMessage.innerText = msg;
            if (loadingOverlay) loadingOverlay.classList.remove('hidden');
        }
        function hideLoading() {
            if (loadingOverlay) loadingOverlay.classList.add('hidden');
        }

        function getFormTemplate(categoryValue) {
            const otherDetailsHtml = `<div><label class="block text-xs font-semibold text-slate-600 mb-1">기타 사항</label><textarea name="other_details" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs" placeholder="추가적인 설정이나 특이사항"></textarea></div>`;
            if (categoryValue === 'CHARACTER') {
                return `
                    <div class="grid grid-cols-2 gap-3">
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">이명/별호</label><input type="text" name="aliases" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">생일</label><input type="text" name="birthday" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">주력 능력</label><input type="text" name="main_skill" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">수준/경지</label><input type="text" name="level" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">사용 무기</label><input type="text" name="weapon" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">주요 복식</label><input type="text" name="clothing" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                    </div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">성격 (장/단점)</label><textarea name="personality" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">첫인상 및 신체적 특징</label><textarea name="appearance" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">궁극적인 욕망</label><textarea name="desire" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">금기</label><textarea name="taboo" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div class="grid grid-cols-2 gap-3">                    
                      <div><label class="block text-xs font-semibold text-slate-600 mb-1">우호 관계</label><input type="text" name="allies" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                      <div><label class="block text-xs font-semibold text-slate-600 mb-1">적대 관계</label><input type="text" name="enemies" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                    </div>
                    ${otherDetailsHtml}
                `;
            } else if (categoryValue === 'FACTION') {
                return `
                    <div class="grid grid-cols-2 gap-3">
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">세력 성향</label><input type="text" name="alignment" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">본거지 위치</label><input type="text" name="base_location" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                    </div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">이념 및 창립 목적</label><textarea name="ideology" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">구조 및 위계</label><textarea name="hierarchy" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">핵심 소속 인물</label><textarea name="key_members" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">고유 기술/자산</label><textarea name="assets" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    ${otherDetailsHtml}
                    `;
            } else if (categoryValue === 'ITEM') {
                return `
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">분류</label><input type="text" name="item_type" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">외형 및 특유의 기운</label><textarea name="appearance" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">효과 및 이점</label><textarea name="effect" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">제약 및 부작용</label><textarea name="penalty" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">기원/이전 주인</label><textarea name="origin" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    ${otherDetailsHtml}
                `;
            } else if (categoryValue === 'LOCATION') {
                return `
                    <div class="grid grid-cols-2 gap-3">
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">소속 지역</label><input type="text" name="region" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                        <div><label class="block text-xs font-semibold text-slate-600 mb-1">통치자/지배세력</label><input type="text" name="ruler" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                    </div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">환경, 기후, 지형</label><textarea name="climate" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">스토리적 상징성</label><textarea name="significance" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">숨겨진 역사</label><textarea name="hidden_history" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    ${otherDetailsHtml}
                `;
            } else if (categoryValue === 'EVENT') {
                return `
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">발생 시점</label><input type="text" name="timeline" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">관련 주체</label><input type="text" name="participants" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>                
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">발발 원인 및 전개</label><textarea name="trigger" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">파급력 및 결과</label><textarea name="impact" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    ${otherDetailsHtml}
                `;
            } else if (categoryValue === 'CONCEPT') {
                return `
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">개념 분류 (무공, 법칙 등)</label><input type="text" name="concept_type" class="quick-input w-full px-2 py-1.5 text-xs border border-slate-300 rounded"></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">상세 설명 및 원리</label><textarea name="description" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">적용 범위 및 한계</label><textarea name="application" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    <div><label class="block text-xs font-semibold text-slate-600 mb-1">부작용 및 리스크</label><textarea name="side_effects" rows="2" class="quick-input w-full px-2 py-1 border border-slate-300 rounded text-xs"></textarea></div>
                    ${otherDetailsHtml}
                `;
            }
            return otherDetailsHtml; // 간략화 템플릿 처리 (필요시 기존 코드 확장 복사 가능)
        }

        if (quickCategory && dynamicFormContainer) {
            quickCategory.addEventListener('change', (e) => {
                dynamicFormContainer.innerHTML = getFormTemplate(e.target.value);
            });
        }

        form.addEventListener('submit', async function(e) {
            if (isRandomMode || isVerified || !config.verifyApiUrl) {
                showLoading('AI가 소설 본문을 집필하고 있습니다...');
                return;
            }
            
            e.preventDefault();
            showLoading('세계관 키워드를 분석 중입니다...');
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerText = 'AI가 세계관을 스캔 중입니다... 🔍';
            }

            try {
                const blocks = [];
                const blockElements = document.querySelectorAll('.input-block');
                blockElements.forEach(block => {
                    const blockData = {};
                    const inputs = block.querySelectorAll('input:not([type="hidden"]), textarea');
                    inputs.forEach(input => {
                        const fieldName = input.getAttribute('name').split('_')[0];
                        blockData[fieldName] = input.value;
                    });
                    blocks.push(blockData);
                });

                const response = await fetch(config.verifyApiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value
                    },
                    body: JSON.stringify({ blocks: blocks })
                });

                const result = await response.json();
                hideLoading();

                if (result.unregistered && result.unregistered.length > 0) {
                    currentKeywords = result.unregistered;
                    if (inputKeywords) inputKeywords.value = currentKeywords.join(','); 
                    renderKeywordBadges(); 
                    if (keywordModal) keywordModal.classList.remove('hidden');
                } else {
                    isVerified = true;
                    showLoading('AI가 소설 본문을 집필하고 있습니다...');
                    form.submit();
                }
            } catch (error) {
                console.error("검증 통신 에러:", error);
                hideLoading();
                isVerified = true;
                form.submit();
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });

        function renderKeywordBadges() {
            if (!unregisteredList) return;
            unregisteredList.innerHTML = '';
            let filledCount = 0;
            currentKeywords.forEach(kw => {
                const isDone = manualData[kw] !== undefined;
                if (isDone) filledCount++;
                
                const badge = document.createElement('button');
                badge.type = 'button';
                badge.className = isDone 
                ? 'px-3 py-1.5 rounded-full text-sm font-semibold bg-emerald-100 text-emerald-700 flex items-center gap-1 cursor-default'
                : 'px-3 py-1.5 rounded-full text-sm font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition underline cursor-pointer shadow-sm';
                
                badge.innerHTML = isDone ? `✅ ${kw}` : `📝 ${kw}`;
                
                if (!isDone) {
                    badge.addEventListener('click', () => openQuickSetup(kw));
                }
                unregisteredList.appendChild(badge);
            });

            if (btnManualComplete) {
                if (filledCount > 0) {
                    btnManualComplete.disabled = false;
                    btnManualComplete.classList.remove('opacity-50', 'cursor-not-allowed', 'hidden');
                    btnManualComplete.innerText = `📝 작성 완료한 ${filledCount}개 설정 저장 후 소설 생성`;
                } else {
                    btnManualComplete.disabled = true;
                    btnManualComplete.classList.add('opacity-50', 'cursor-not-allowed');
                    btnManualComplete.classList.remove('hidden');
                    btnManualComplete.innerText = `📝 하나 이상 설정을 작성하면 활성화됩니다`;
                }
            }
        }

        function openQuickSetup(word) {
            currentlyEditingWord = word;
            if (quickSetupWord) quickSetupWord.innerText = `'${word}'`;
            if (quickCategory) quickCategory.value = 'CHARACTER'; 
            if (dynamicFormContainer) dynamicFormContainer.innerHTML = getFormTemplate('CHARACTER'); 
            if (quickSetupBox) quickSetupBox.classList.remove('hidden');
        }

        if (btnQuickCancel) {
            btnQuickCancel.addEventListener('click', () => {
                if (quickSetupBox) quickSetupBox.classList.add('hidden');
                currentlyEditingWord = "";
            });
        }

        if (btnQuickSave) {
            btnQuickSave.addEventListener('click', () => {
                if (!dynamicFormContainer) return;
                const inputs = dynamicFormContainer.querySelectorAll('.quick-input');
                const detailData = {};
                let hasData = false;
                
                inputs.forEach(input => {
                    if(input.value.trim() !== '') {
                        detailData[input.name] = input.value.trim();
                        hasData = true;
                    }
                });

                if(!hasData) {
                    alert("최소 한 항목 이상 작성해주세요!");
                    return;
                }

                manualData[currentlyEditingWord] = {
                    category: quickCategory ? quickCategory.value : 'CONCEPT',
                    details: detailData 
                };
                
                if (inputManualData) inputManualData.value = JSON.stringify(manualData);
                if (quickSetupBox) quickSetupBox.classList.add('hidden');
                renderKeywordBadges();
            });
        }

        if (btnManualComplete) {
            btnManualComplete.addEventListener('click', () => {
                if (inputAction) inputAction.value = 'manual';
                if (keywordModal) keywordModal.classList.add('hidden');
                isVerified = true;
                showLoading('작성하신 부분 설정을 저장하고 본문을 집필합니다...');
                form.submit();
            });
        }

        const btnModalIgnore = document.getElementById('btn-modal-ignore');
        if (btnModalIgnore) {
            btnModalIgnore.addEventListener('click', () => {
                if (inputAction) inputAction.value = 'ignore';
                if (keywordModal) keywordModal.classList.add('hidden');
                isVerified = true;
                showLoading('키워드를 무시하고 본문을 집필합니다...');
                form.submit();
            });
        }
        
        const btnModalCancel = document.getElementById('btn-modal-cancel-generation');
        if (btnModalCancel) {
            btnModalCancel.addEventListener('click', () => {
                if (keywordModal) keywordModal.classList.add('hidden');
                if (quickSetupBox) quickSetupBox.classList.add('hidden'); 
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = originalBtnText;
                }
                isVerified = false;
            });
        }
    }

    // --- [사이드바 검색 필터링 로직 추가] ---
    const searchInput = document.getElementById('world-search-input');
    const elementItems = document.querySelectorAll('.world-element-item');
    const categoryGroups = document.querySelectorAll('.world-category-group');

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const keyword = e.target.value.toLowerCase().trim();

            elementItems.forEach(item => {
                const name = item.getAttribute('data-name').toLowerCase();
                // 검색어가 포함되어 있으면 보이고, 아니면 숨김 처리
                if (name.includes(keyword)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });

            // 내부 요소가 모두 숨겨진 카테고리 그룹(예: '인물', '물건' 타이틀)도 숨기기
            categoryGroups.forEach(group => {
                const visibleItems = Array.from(group.querySelectorAll('.world-element-item')).filter(item => item.style.display !== 'none');
                if (visibleItems.length === 0) {
                    group.style.display = 'none';
                } else {
                    group.style.display = '';
                }
            });
        });
    }
});