// Agent 별로 미리 준비한 추천 질문
const AGENT_QUESTIONS = {
    file: '현재 디렉토리의 파일 목록을 보여주고, 그 중 하나를 골라 내용을 요약해줘',
    weather: '서울의 현재 날씨를 알려줘'
};

const chatForm = document.getElementById('chatForm');
const agentSelect = document.getElementById('agentSelect');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const messagesEl = document.getElementById('messages');

// Agent를 선택하면 해당 Agent에 어울리는 추천 질문을 입력창에 채워준다.
function applySuggestedQuestion() {
    userInput.value = AGENT_QUESTIONS[agentSelect.value];
}

agentSelect.addEventListener('change', applySuggestedQuestion);
applySuggestedQuestion();

userInput.addEventListener('keydown', (e) => {
    // 한글 입력 조합 중인 Enter는 전송으로 처리하지 않는다.
    if (e.key !== 'Enter' || e.shiftKey || e.isComposing) {
        return;
    }

    e.preventDefault();

    if (!sendBtn.disabled) {
        chatForm.requestSubmit(sendBtn);
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const agent = agentSelect.value;
    const agentLabel = agentSelect.selectedOptions[0].text;

    // 입력이 없으면 추천 질문을 사용하고, 있으면 사용자 입력을 사용한다.
    const request = userInput.value.trim() || AGENT_QUESTIONS[agent];

    appendMessage(`[${agentLabel}] ${request}`, 'user');
    userInput.value = '';
    sendBtn.disabled = true;

    const loadingEl = appendMessage('생각 중...', 'assistant');

    try {
        await requestAi(request, agent, loadingEl);
    } catch (err) {
        console.error(err);
        renderMarkdown(loadingEl, '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
});

// /ai?request=질문&agent=선택한Agent 형식으로 요청하고 완성된 응답을 표시한다.
async function requestAi(request, agent, targetEl) {
    const url = '/ai?request=' + encodeURIComponent(request) + '&agent=' + encodeURIComponent(agent);
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('서버 오류가 발생했습니다.');
    }
    const answer = await response.text();
    renderMarkdown(targetEl, answer);
}

function appendMessage(text, role) {
    const el = document.createElement('div');
    el.className = `message ${role}`;
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
}

// LLM 응답(Markdown)을 안전하게 HTML로 변환하여 표시한다.
function renderMarkdown(el, markdownText) {
    const rawHtml = marked.parse(markdownText);
    el.innerHTML = DOMPurify.sanitize(rawHtml);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}
