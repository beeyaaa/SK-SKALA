const DEFAULT_PROMPT = '지금 시간은 어떻게 되나요';

const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const messagesEl = document.getElementById('messages');

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

    // 입력이 없으면 기본 문구를 사용하고, 있으면 사용자 입력을 사용한다.
    const request = userInput.value.trim() || DEFAULT_PROMPT;

    appendMessage(request, 'user');
    userInput.value = '';
    sendBtn.disabled = true;

    const loadingEl = appendMessage('생각 중...', 'assistant');

    try {
        await requestAi(request, loadingEl);
    } catch (err) {
        console.error(err);
        renderMarkdown(loadingEl, '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
});

// /ai?request=질문 형식으로 요청하고 완성된 응답을 표시한다.
async function requestAi(request, targetEl) {
    const response = await fetch('/ai?request=' + encodeURIComponent(request));
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
