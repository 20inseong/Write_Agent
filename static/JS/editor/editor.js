(function () {
  let config = { dashboardUrl: "/" };
  try {
      const configData = document.getElementById('editor-config');
      if (configData && configData.textContent.trim()) {
          config = JSON.parse(configData.textContent);
      }
  } catch (e) {
      console.error("에디터 설정 JSON 파싱 에러:", e);
  }

    var editor = document.getElementById("main-editor");
    var counter = document.getElementById("char-count");
    
    const similarityDisplay = document.getElementById("similarity-display");
    const similarityGauge = document.getElementById("similarity-gauge");
    const emptyNotice = document.getElementById("empty-ai-notice");
    const maxChars = config.goalWordCount || 5000;

    // N-gram (2어절) 생성기
    function getBigrams(text) {
      const cleanText = text.replace(/[.,!?\"\'\n\r]/g, " ").trim();
      const words = cleanText.split(/\s+/).filter(w => w.length > 0);
      const bigrams = new Set();
      
      if (words.length < 2) {
        if (words.length === 1) bigrams.add(words[0]);
        return bigrams;
      }
      
      for (let i = 0; i < words.length - 1; i++) {
        bigrams.add(words[i] + " " + words[i + 1]);
      }
      return bigrams;
    }

    const aiDraftTextEl = document.getElementById("ai-draft-text");
    let aiText = aiDraftTextEl ? aiDraftTextEl.innerText : "";
    
    if (emptyNotice && aiText.includes(emptyNotice.innerText)) {
      aiText = aiText.replace(emptyNotice.innerText, "").trim();
    }
    
    const aiBigrams = getBigrams(aiText);

    // 실시간 입력 감지 및 유사도 계산
    function handleInput() {
      if(!editor) return;
      const userText = editor.value;
      counter.textContent = `현재 ${userText.length}자 / ${maxChars}자`;

      if (userText.length >= maxChars) {
        counter.className = "text-sm tabular-nums font-bold text-indigo-600";
      } else {
        counter.className = "text-sm tabular-nums text-slate-600";
      }

      if (aiBigrams.size === 0 || userText.trim().length === 0) {
        similarityDisplay.className = "text-xs font-bold text-green-600";
        similarityDisplay.textContent = "0%";
        similarityGauge.style.width = "0%";
        similarityGauge.className = "bg-green-500 h-2 rounded-full transition-all duration-500 ease-out";
        return;
      }

      const userBigrams = getBigrams(userText);
      let intersectionCount = 0;
      userBigrams.forEach(bigram => {
        if (aiBigrams.has(bigram)) intersectionCount++;
      });

      const unionSet = new Set([...aiBigrams, ...userBigrams]);
      const unionCount = unionSet.size;

      let percent = 0;
      if (unionCount > 0) {
        percent = Math.round((intersectionCount / unionCount) * 100);
      }

      let textColorClass = "text-green-600";
      let gaugeColorClass = "bg-green-500";

      if (percent > 60) {
        textColorClass = "text-red-500";
        gaugeColorClass = "bg-red-500";
      } else if (percent > 20) {
        textColorClass = "text-amber-500";
        gaugeColorClass = "bg-amber-500";
      }

      similarityDisplay.className = `text-xs font-bold ${textColorClass}`;
      similarityDisplay.textContent = `${percent}%`;
      similarityGauge.style.width = `${percent}%`;
      similarityGauge.className = `h-2 rounded-full transition-all duration-500 ease-out ${gaugeColorClass}`;
    }

    let debounceTimer;
    const saveStatus = document.getElementById("save-status");
    const manualSaveBtn = document.getElementById("manual-save-btn");

    // 서버로 데이터 비동기 전송
    async function saveDraftToServer() {
      if(!saveStatus) return;
      saveStatus.textContent = "저장 중...";
      saveStatus.className = "text-sm font-medium text-indigo-500 mr-2 transition-colors";
      
      const userContent = editor.value;
      const aiDraftEl = document.getElementById("ai-draft-text");
      const aiContent = aiDraftEl ? aiDraftEl.innerText : "";
      
      let apiUrl = "/api/save_draft/";
      if (config.novelId) {
          apiUrl = `/api/save_draft/${config.novelId}/`;
      }

      try {
        const res = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": window.getCookie("csrftoken") },
          body: JSON.stringify({
            ai_content: aiContent,
            user_content: userContent,
            setup_context: JSON.stringify(currentBlockData || {})
          })
        });
        const data = await res.json();
        if(data.status === "success") {
          saveStatus.textContent = `저장 완료 (${data.updated_at})`;
          saveStatus.className = "text-sm font-medium text-emerald-500 mr-2 transition-colors";
        }
      } catch(e) {
        saveStatus.textContent = "저장 실패";
        saveStatus.className = "text-sm font-medium text-red-500 mr-2 transition-colors";
      }
    }

    if (editor) {
        editor.addEventListener("input", () => {
        handleInput();
        clearTimeout(debounceTimer);
        
        saveStatus.textContent = "입력 중...";
        saveStatus.className = "text-sm font-medium text-slate-500 mr-2 transition-colors";
        
        debounceTimer = setTimeout(saveDraftToServer, 1500);
        });

        // 작가 편의용 단축키 (Ctrl+S / Cmd+S)
        editor.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            clearTimeout(debounceTimer);
            saveDraftToServer();
        }
        });
    }

    if (manualSaveBtn) {
        manualSaveBtn.addEventListener("click", () => {
        clearTimeout(debounceTimer);
        saveDraftToServer();
        });
    }

    // 맞춤법 검사기 열기
    const spellCheckBtn = document.getElementById("spell-check-btn");
    if (spellCheckBtn && editor) {
        spellCheckBtn.addEventListener("click", async () => {
        const textToCopy = editor.value;
        if (!textToCopy.trim()) {
            alert("에디터에 검사할 텍스트가 없습니다.");
            return;
        }
        try {
            await navigator.clipboard.writeText(textToCopy);
            alert("텍스트가 클립보드에 복사되었습니다!\n열리는 검사기 창에서 붙여넣기(Ctrl+V) 해주세요.");
            window.open("https://lab.incruit.com/tools/spell/", "_blank");
        } catch (err) {
            alert("복사에 실패했습니다. 에디터에서 직접 복사 후 검사해주세요.");
            window.open("https://lab.incruit.com/tools/spell/", "_blank");
        }
        });
    }

    const completeWritingBtn = document.getElementById("complete-writing-btn");
    const episodeSaveModal = document.getElementById("episode-save-modal");
    const closeEpisodeModalBtn = document.getElementById("close-episode-modal-btn");
    const episodeSaveForm = document.getElementById("episode-save-form");
    const submitEpisodeBtn = document.getElementById("submit-episode-btn");
    const episodeTitleInput = document.getElementById("episode-title-input");

    if (completeWritingBtn) {
        completeWritingBtn.addEventListener("click", async () => {
        if (!editor.value.trim()) {
            alert("저장할 본문 내용이 없습니다.");
            return;
        }
        clearTimeout(debounceTimer);
        await saveDraftToServer();
        episodeTitleInput.value = "";
        episodeSaveModal.classList.remove("hidden");
        });
    }

    if (closeEpisodeModalBtn) {
        closeEpisodeModalBtn.addEventListener("click", () => {
        episodeSaveModal.classList.add("hidden");
        });
    }

    if (episodeSaveForm) {
        episodeSaveForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const title = episodeTitleInput.value.trim();
        const content = editor.value;
        
        let similarityScore = 0;
        const simText = similarityDisplay.textContent;
        const match = simText.match(/\d+/);
        if (match) {
            similarityScore = parseInt(match[0], 10);
        }

        let apiUrl = "/api/save-episode/";
        if (config.novelId) {
            apiUrl = `/api/save-episode/${config.novelId}/`;
        }

        submitEpisodeBtn.disabled = true;
        submitEpisodeBtn.innerText = "저장 중... ⏳";

        try {
            const response = await fetch(apiUrl, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json", 
                "X-CSRFToken": window.getCookie("csrftoken") 
            },
            body: JSON.stringify({
                title: title,
                content: content,
                ai_similarity: similarityScore
            })
            });
            
            const result = await response.json();
            
            if (result.status === "success") {
            // HTML JSON에서 받아온 동적 URL 사용
            window.location.href = config.dashboardUrl; 
            } else {
            alert("저장 실패: " + result.message);
            submitEpisodeBtn.disabled = false;
            submitEpisodeBtn.innerText = "저장 후 대시보드로 이동";
            }
        } catch (error) {
            alert("서버 통신 중 오류가 발생했습니다.");
            submitEpisodeBtn.disabled = false;
            submitEpisodeBtn.innerText = "저장 후 대시보드로 이동";
        }
        });
    }

    if (editor) handleInput(); 

    const addBlockModal = document.getElementById("add-block-modal");
    const keywordCheckModal = document.getElementById("keyword-check-modal");
    const openModalBtn = document.getElementById("open-modal-btn");
    const closeModalBtn = document.getElementById("close-modal-btn");
    const addBlockForm = document.getElementById("add-block-form");
    const submitBlockBtn = document.getElementById("submit-block-btn");
    const btnAddStub = document.getElementById("btn-add-stub");
    
    let currentBlockData = null;
    let currentNovelId = null;
    let currentUnregistered = [];
    let currentApiUrl = "/api/generate-block/";

    if (openModalBtn) openModalBtn.addEventListener("click", () => addBlockModal.classList.remove("hidden"));
    if (closeModalBtn) closeModalBtn.addEventListener("click", () => addBlockModal.classList.add("hidden"));

    if (addBlockForm) {
        addBlockForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const originalBtnText = submitBlockBtn.innerText;
        submitBlockBtn.innerText = "키워드 스캔 중...";
        submitBlockBtn.disabled = true;

        const formData = new FormData(addBlockForm);
        currentBlockData = {};
        formData.forEach((value, key) => { currentBlockData[key] = value; });

        currentNovelId = config.novelId;
        currentApiUrl = currentNovelId ? `/api/generate-block/${currentNovelId}/` : "/api/generate-block/";

        if (currentNovelId) {
            try {
            const verifyRes = await fetch(`/api/verify-keywords/${currentNovelId}/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": window.getCookie("csrftoken") },
                body: JSON.stringify({ blocks: [currentBlockData] })
            });
            const verifyData = await verifyRes.json();

            if (verifyData.status === "success" && verifyData.unregistered && verifyData.unregistered.length > 0) {
                currentUnregistered = verifyData.unregistered;
                addBlockModal.classList.add("hidden");
                
                const kwContainer = document.getElementById("unregistered-keywords-list");
                kwContainer.innerHTML = currentUnregistered.map(kw =>`
                <div class="flex items-center justify-between bg-slate-50 p-2 rounded border border-slate-200">
                    <span class="text-sm font-bold text-slate-700">${kw}</span>
                    <select class="kw-category-select text-sm border-slate-300 rounded focus:ring-indigo-500 py-1" data-kw="${kw}">
                    <option value="">카테고리 선택 (필수)</option>
                    <option value="CHARACTER">인물</option>
                    <option value="FACTION">단체</option>
                    <option value="ITEM">물건</option>
                    <option value="LOCATION">장소</option>
                    <option value="EVENT">사건</option>
                    <option value="CONCEPT">개념/기타</option>
                    </select>
                </div>
                `).join('');
                
                keywordCheckModal.classList.remove("hidden");
                submitBlockBtn.innerText = originalBtnText; 
                submitBlockBtn.disabled = false;

                const selects = kwContainer.querySelectorAll('.kw-category-select');
                btnAddStub.disabled = true;
                btnAddStub.classList.add("opacity-50", "cursor-not-allowed");

                selects.forEach(sel => {
                sel.addEventListener('change', () => {
                    const allSelected = Array.from(selects).every(s => s.value !== "");
                    if (allSelected) {
                    btnAddStub.disabled = false;
                    btnAddStub.classList.remove("opacity-50", "cursor-not-allowed");
                    } else {
                    btnAddStub.disabled = true;
                    btnAddStub.classList.add("opacity-50", "cursor-not-allowed");
                    }
                });
                });
                return; 
            }
            } catch (error) {
            console.error("키워드 검증 에러:", error);
            }
        }

        await executeGenerateDraft('', []);
        submitBlockBtn.innerText = originalBtnText;
        submitBlockBtn.disabled = false;
        });
    }

    const btnIgnore = document.getElementById("btn-ignore");
    const btnCancelKeyword = document.getElementById("btn-cancel-keyword");

    if (btnAddStub) {
        btnAddStub.addEventListener("click", () => {
        const selects = document.querySelectorAll('.kw-category-select');
        const structuredKeywords = Array.from(selects).map(s => ({
            word: s.getAttribute('data-kw'),
            category: s.value
        }));

        btnAddStub.innerText = "DB 임시 저장 및 초안 생성 중... ⏳";
        btnAddStub.disabled = true;
        if(btnIgnore) btnIgnore.disabled = true;
        if(btnCancelKeyword) btnCancelKeyword.disabled = true;
        executeGenerateDraft('stub', structuredKeywords);
        });
    }

    if (btnIgnore) {
        btnIgnore.addEventListener("click", () => {
        btnIgnore.innerText = "무시하고 초안 생성 중... ⏳";
        if(btnAddStub) btnAddStub.disabled = true;
        btnIgnore.disabled = true;
        if(btnCancelKeyword) btnCancelKeyword.disabled = true;
        executeGenerateDraft('ignore', []);
        });
    }

    if (btnCancelKeyword) {
        btnCancelKeyword.addEventListener("click", () => {
        keywordCheckModal.classList.add("hidden");
        addBlockModal.classList.remove("hidden"); 
        });
    }

    async function executeGenerateDraft(actionStr, keywordsArr) {
      const draftEl = document.getElementById("ai-draft-text");
      const currentAiText = draftEl ? (draftEl.innerText || "") : "";
      const previousContext = currentAiText.length > 200 ? currentAiText.slice(-200) : currentAiText;

      const payload = {
        block: currentBlockData,
        previous_context: previousContext,
        unregistered_action: actionStr,
        unregistered_keywords: keywordsArr
      };

      try {
        const response = await fetch(currentApiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": window.getCookie("csrftoken") },
          body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        if (result.status === "success") {
          if(emptyNotice) emptyNotice.style.display = 'none';
          
          const newDraftHtml = `
            <div class="mt-8 border-t border-slate-600 pt-6 animate-fade-in">
              <h3 class="mb-3 text-xs font-bold text-indigo-400">=== [새 장면 추가] ===</h3>
              <p class="text-slate-200">${result.scene_text.replace(/\n/g, '<br>')}</p>
            </div>`;
          draftEl.insertAdjacentHTML('beforeend', newDraftHtml);
          
          if(addBlockForm) addBlockForm.reset();
          if(keywordCheckModal) keywordCheckModal.classList.add("hidden");
          if(addBlockModal) addBlockModal.classList.add("hidden");

          const updatedAiText = draftEl.innerText || "";
          const updatedAiBigrams = getBigrams(updatedAiText);
          
          aiBigrams.clear();
          updatedAiBigrams.forEach(v => aiBigrams.add(v));

          handleInput(); 
        } else {
          alert("생성 실패: " + result.message);
        }
      } catch (error) {
        alert("통신 중 오류가 발생했습니다.");
      } finally {
        if(btnAddStub) {
            btnAddStub.innerText = "선택한 카테고리로 추가 후 초안 생성";
            btnAddStub.disabled = false;
        }
        if(btnIgnore) {
            btnIgnore.innerText = "무시하고 초안만 생성";
            btnIgnore.disabled = false;
        }
        if(btnCancelKeyword) btnCancelKeyword.disabled = false;
      }
    }
})();