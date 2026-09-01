const DEFAULT_PROMPT = '너를 소개 시켜줘';

const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const modeSelect = document.getElementById('modeSelect');
const messagesEl = document.getElementById('messages');

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // 입력이 없으면 기본 문구를 사용하고, 있으면 사용자 입력을 사용한다.
    const question = userInput.value.trim() || DEFAULT_PROMPT;
    const mode = modeSelect.value; // 'sync' | 'async'

    appendMessage(question, 'user');
    userInput.value = '';
    sendBtn.disabled = true;

    const loadingEl = appendMessage('생각 중...', 'assistant');

    try {
        if (mode === 'async') {
            await requestAsync(question, loadingEl);
        } else {
            await requestSync(question, loadingEl);
        }
    } catch (err) {
        console.error(err);
        renderMarkdown(loadingEl, '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
});

// 동기 방식: /ai 호출 후 완성된 응답을 한번에 표시
async function requestSync(question, targetEl) {
    const response = await fetch('/ai?userInput=' + encodeURIComponent(question));
    if (!response.ok) {
        throw new Error('서버 오류가 발생했습니다.');
    }
    const answer = await response.text();
    renderMarkdown(targetEl, answer);
}

// 비동기(스트리밍) 방식: /ai/stream 호출 후 토큰이 도착하는 대로 이어붙여 표시
async function requestAsync(question, targetEl) {
    const response = await fetch('/ai/stream?userInput=' + encodeURIComponent(question));
    if (!response.ok || !response.body) {
        throw new Error('서버 오류가 발생했습니다.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let answer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE 이벤트는 빈 줄("\n\n")로 구분되고, 각 줄은 "data:"로 시작한다.
        const events = buffer.split('\n\n');
        buffer = events.pop(); // 아직 완성되지 않은 마지막 조각은 버퍼에 유지

        for (const rawEvent of events) {
            const chunk = rawEvent
                .split('\n')
                .filter((line) => line.startsWith('data:'))
                .map((line) => line.slice(5))
                .join('\n');
            answer += chunk;
            renderMarkdown(targetEl, answer);
        }
    }

    if (answer.length === 0) {
        renderMarkdown(targetEl, '(응답이 없습니다)');
    }
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

// -----------------------------------------------------------------------------
// 아래부터 기존 채팅 Frontend에 추가한 메뉴 및 Structured Output 기능이다.
// -----------------------------------------------------------------------------
const STRUCTURED_OUTPUT_CONFIG = Object.freeze({
    bean: {
        prompt: '톰 행크스에 대한 5개 영화 필로그래피를 알려주세요',
        endpoint: '/ai/bean'
    },
    'list-bean': {
        prompt: '톰 행크스와 빌머레이에 대한 5개 영화 필로그래피를 알려주세요',
        endpoint: '/ai/list-bean'
    },
    map: {
        prompt: '과일 이름과 맛 10종류를 리스트로 제공해줘',
        endpoint: '/ai/map'
    },
    list: {
        prompt: '아이스크림 맛을 10가지 제시해줘',
        endpoint: '/ai/list'
    }
});

const menuItems = document.querySelectorAll('.sidebar-menu-item');
const contentPages = document.querySelectorAll('.content-page');
const structuredForm = document.getElementById('structuredForm');
const structuredType = document.getElementById('structuredType');
const structuredInput = document.getElementById('structuredInput');
const structuredEndpoint = document.getElementById('structuredEndpoint');
const structuredSubmitBtn = document.getElementById('structuredSubmitBtn');
const structuredResultType = document.getElementById('structuredResultType');
const structuredResultEmpty = document.getElementById('structuredResultEmpty');
const structuredResultOutput = document.getElementById('structuredResultOutput');
const structuredResultCode = structuredResultOutput.querySelector('code');
const structuredErrorOutput = document.getElementById('structuredErrorOutput');

menuItems.forEach((menuItem) => {
    menuItem.addEventListener('click', () => {
        menuItems.forEach((item) => item.classList.remove('active'));
        contentPages.forEach((page) => page.classList.remove('active'));

        menuItem.classList.add('active');
        document.getElementById(menuItem.dataset.target).classList.add('active');
    });
});

function applyStructuredOutputType(type) {
    const config = STRUCTURED_OUTPUT_CONFIG[type];
    if (!config) return;

    structuredInput.value = config.prompt;
    structuredEndpoint.textContent = `GET ${config.endpoint}`;
    structuredResultType.textContent = type;
}

structuredType.addEventListener('change', (event) => {
    applyStructuredOutputType(event.target.value);
});

structuredForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const type = structuredType.value;
    const config = STRUCTURED_OUTPUT_CONFIG[type];
    const question = structuredInput.value.trim() || config.prompt;

    structuredInput.value = question;
    structuredResultType.textContent = type;
    structuredSubmitBtn.disabled = true;
    structuredSubmitBtn.textContent = '처리 중...';
    structuredResultEmpty.hidden = true;
    structuredResultOutput.hidden = true;
    structuredErrorOutput.hidden = true;

    try {
        const response = await fetch(
            `${config.endpoint}?userInput=${encodeURIComponent(question)}`,
            { headers: { Accept: 'application/json' } }
        );

        if (!response.ok) {
            const detail = await response.text();
            throw new Error(detail || `서버 요청에 실패했습니다. (${response.status})`);
        }

        const result = await response.json();
        structuredResultCode.textContent = JSON.stringify(result, null, 2);
        structuredResultOutput.hidden = false;
    } catch (error) {
        console.error(error);
        structuredErrorOutput.textContent = `응답을 가져오지 못했습니다. ${error.message}`;
        structuredErrorOutput.hidden = false;
    } finally {
        structuredSubmitBtn.disabled = false;
        structuredSubmitBtn.textContent = '확인';
    }
});

applyStructuredOutputType(structuredType.value);

// -----------------------------------------------------------------------------
// Embedding: 저장 -> 의미 검색 -> ID 삭제
// -----------------------------------------------------------------------------
const embeddingSaveForm = document.getElementById('embeddingSaveForm');
const embeddingSaveText = document.getElementById('embeddingSaveText');
const embeddingSaveResult = document.getElementById('embeddingSaveResult');
const embeddingSearchForm = document.getElementById('embeddingSearchForm');
const embeddingSearchQuery = document.getElementById('embeddingSearchQuery');
const embeddingSearchResult = document.getElementById('embeddingSearchResult');
const embeddingDeleteForm = document.getElementById('embeddingDeleteForm');
const embeddingDeleteId = document.getElementById('embeddingDeleteId');
const embeddingDeleteResult = document.getElementById('embeddingDeleteResult');

embeddingSaveForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    setEmbeddingStatus(embeddingSaveResult, '저장 중...');

    try {
        const response = await fetch('/ai/embedding/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ text: embeddingSaveText.value.trim() })
        });
        const savedDocument = await readJsonResponse(response);

        embeddingDeleteId.value = savedDocument.id;
        setEmbeddingStatus(embeddingSaveResult, `저장 완료 · ID: ${savedDocument.id}`);
    } catch (error) {
        setEmbeddingStatus(embeddingSaveResult, error.message, true);
    }
});

embeddingSearchForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    embeddingSearchResult.textContent = '검색 중...';

    try {
        const query = encodeURIComponent(embeddingSearchQuery.value.trim());
        const response = await fetch(`/ai/embedding/search?query=${query}`);
        const documents = await readJsonResponse(response);
        renderDocumentResults(embeddingSearchResult, documents, (documentId) => {
            embeddingDeleteId.value = documentId;
            deleteEmbeddingDocument(documentId);
        });
    } catch (error) {
        embeddingSearchResult.textContent = error.message;
        embeddingSearchResult.classList.add('error');
    }
});

embeddingDeleteForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    await deleteEmbeddingDocument(embeddingDeleteId.value.trim());
});

async function deleteEmbeddingDocument(documentId) {
    setEmbeddingStatus(embeddingDeleteResult, '삭제 중...');

    try {
        const response = await fetch(`/ai/embedding/delete/${encodeURIComponent(documentId)}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error(`삭제에 실패했습니다. (${response.status})`);
        }

        embeddingDeleteId.value = documentId;
        setEmbeddingStatus(embeddingDeleteResult, `삭제 완료 · ID: ${documentId}`);
    } catch (error) {
        setEmbeddingStatus(embeddingDeleteResult, error.message, true);
    }
}

// 검색 결과 렌더링 (Embedding 페이지, RAG-ETL 페이지 공용).
// onDelete를 넘기면 각 결과에 삭제 버튼이 추가된다.
function renderDocumentResults(container, documents, onDelete) {
    container.replaceChildren();
    container.classList.remove('error');

    if (documents.length === 0) {
        container.textContent = '비슷한 문서를 찾지 못했습니다.';
        return;
    }

    documents.forEach((storedDocument) => {
        const resultItem = document.createElement('article');
        resultItem.className = 'embedding-result-item';

        const text = document.createElement('p');
        text.textContent = storedDocument.text;

        const details = document.createElement('small');
        const score = typeof storedDocument.score === 'number'
            ? ` · 유사도 ${storedDocument.score.toFixed(4)}`
            : '';
        details.textContent = `ID: ${storedDocument.id}${score}`;

        resultItem.append(text, details);

        if (onDelete) {
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'result-delete-button';
            deleteButton.textContent = '이 문서 삭제';
            deleteButton.addEventListener('click', () => onDelete(storedDocument.id));
            resultItem.append(deleteButton);
        }

        container.appendChild(resultItem);
    });
}

function setEmbeddingStatus(element, message, isError = false) {
    element.textContent = message;
    element.classList.toggle('error', isError);
}

async function readJsonResponse(response) {
    if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || `요청에 실패했습니다. (${response.status})`);
    }
    return response.json();
}

// -----------------------------------------------------------------------------
// RAG-ETL: documents 폴더의 파일 목록 조회 -> 확장자별 ETL 실행(txt/pdf)
// -----------------------------------------------------------------------------
const ETL_EXECUTE_ENDPOINT = {
    txt: '/ai/etl/txt',
    pdf: '/ai/etl/pdf'
};

const etlFileList = document.getElementById('etlFileList');
const etlResult = document.getElementById('etlResult');
const etlSearchForm = document.getElementById('etlSearchForm');
const etlSearchQuery = document.getElementById('etlSearchQuery');
const etlSearchResult = document.getElementById('etlSearchResult');

async function loadEtlFiles() {
    etlFileList.textContent = '불러오는 중...';

    try {
        const response = await fetch('/ai/etl/files');
        const files = await readJsonResponse(response);
        renderEtlFiles(files);
    } catch (error) {
        etlFileList.textContent = `파일 목록을 불러오지 못했습니다. ${error.message}`;
    }
}

function renderEtlFiles(files) {
    etlFileList.replaceChildren();

    if (files.length === 0) {
        etlFileList.textContent = 'documents 폴더에 파일이 없습니다.';
        return;
    }

    files.forEach((file) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'etl-file-item';

        const name = document.createElement('span');
        name.textContent = file.name;

        const extension = document.createElement('span');
        extension.className = 'etl-file-extension';
        extension.textContent = file.extension.toUpperCase();

        item.append(name, extension);
        item.addEventListener('click', () => executeEtl(file, item));

        etlFileList.appendChild(item);
    });
}

async function executeEtl(file, itemEl) {
    const endpoint = ETL_EXECUTE_ENDPOINT[file.extension];
    if (!endpoint) {
        setEtlStatus(`지원하지 않는 확장자입니다. (${file.extension})`, true);
        return;
    }

    etlFileList.querySelectorAll('.etl-file-item').forEach((el) => el.classList.remove('active'));
    itemEl.classList.add('active');
    setEtlStatus(`${file.fileName} 파일을 ETL 처리 중입니다...`);

    try {
        const response = await fetch(`${endpoint}?fileName=${encodeURIComponent(file.fileName)}`, {
            method: 'POST'
        });
        const result = await readJsonResponse(response);
        setEtlStatus(`저장 완료 · ${result.fileName} · 청크 ${result.chunkCount}건`);
    } catch (error) {
        setEtlStatus(error.message, true);
    }
}

function setEtlStatus(message, isError = false) {
    etlResult.textContent = message;
    etlResult.classList.toggle('error', isError);
}

etlSearchForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    etlSearchResult.textContent = '검색 중...';

    try {
        const query = encodeURIComponent(etlSearchQuery.value.trim());
        const response = await fetch(`/ai/etl/search?query=${query}`);
        const documents = await readJsonResponse(response);
        renderDocumentResults(etlSearchResult, documents);
    } catch (error) {
        etlSearchResult.textContent = error.message;
        etlSearchResult.classList.add('error');
    }
});

loadEtlFiles();

// -----------------------------------------------------------------------------
// RAG: QuestionAnswer(/ai/rag/simple) / RetrievalAugmentation(/ai/rag/advanced)
//      중 선택하여 질의응답. advanced는 응답에 conversationId(세션 ID)가 포함된다.
// -----------------------------------------------------------------------------
const RAG_CONFIG = Object.freeze({
    simple: {
        label: 'QuestionAnswerAdvisor',
        prompt: '대한민국의 주권은 누구에게 있는가?',
        endpoint: '/ai/rag/simple',
        available: true
    },
    rewrite: {
        label: 'RewriteQueryTransformer',
        // 대화 이력은 세션 쿠키(conversationId)로 식별되어 서버에 누적된다.
        prompt: '국회의원이 하라는 일은 하지 않고, 자기 개인 이익만 챙기고 있고 이게 국회의원이 할일이냐?',
        endpoint: '/ai/rag/advanced',
        available: true
    },
    compression: {
        label: 'CompressionQueryTransformer',
        // 대화 이력은 세션 쿠키(conversationId)로 식별되어 서버에 누적된다.
        prompt: '대통령은?',
        endpoint: '/ai/rag/advanced',
        available: true
    },
    multiquery: {
        label: 'MultiQueryTransformer',
        // 대화 이력은 세션 쿠키(conversationId)로 식별되어 서버에 누적된다.
        prompt: '국회는 국회의원을 위한 곳인가 국민을 위한 곳인가?',
        endpoint: '/ai/rag/advanced',
        available: true
    },
    fullRag: {
        label: 'Full RAG',
        // 대화 이력은 세션 쿠키(conversationId)로 식별되어 서버에 누적된다.
        prompt: '국회의 임시회의는 어떤 조건에 개최될수 있나요?',
        endpoint: '/ai/rag/full-rag',
        available: true
    }
});

const ragForm = document.getElementById('ragForm');
const ragType = document.getElementById('ragType');
const ragQuestion = document.getElementById('ragQuestion');
const ragEndpoint = document.getElementById('ragEndpoint');
const ragSubmitBtn = document.getElementById('ragSubmitBtn');
const ragResultType = document.getElementById('ragResultType');
const ragResultEmpty = document.getElementById('ragResultEmpty');
const ragConversationId = document.getElementById('ragConversationId');
const ragResultOutput = document.getElementById('ragResultOutput');
const ragNoticeOutput = document.getElementById('ragNoticeOutput');
const ragErrorOutput = document.getElementById('ragErrorOutput');

function applyRagType(type) {
    const config = RAG_CONFIG[type];
    if (!config) return;

    ragQuestion.value = config.prompt;
    ragResultType.textContent = config.label;
    ragEndpoint.textContent = config.available ? `GET ${config.endpoint}` : '개발 예정';
}

ragType.addEventListener('change', (event) => {
    applyRagType(event.target.value);
});

ragForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const type = ragType.value;
    const config = RAG_CONFIG[type];
    const question = ragQuestion.value.trim() || config.prompt;

    ragQuestion.value = question;
    ragResultType.textContent = config.label;
    ragResultEmpty.hidden = true;
    ragConversationId.hidden = true;
    ragResultOutput.hidden = true;
    ragNoticeOutput.hidden = true;
    ragErrorOutput.hidden = true;

    ragSubmitBtn.disabled = true;
    ragSubmitBtn.textContent = '처리 중...';

    try {
        const response = await fetch(`${config.endpoint}?question=${encodeURIComponent(question)}`);
        const result = await readJsonResponse(response);
        renderMarkdown(ragResultOutput, result.answer);
        ragResultOutput.hidden = false;

        // advanced(RetrievalAugmentationAdvisor)는 응답에 conversationId(세션 ID)를 포함한다.
        if (result.conversationId) {
            ragConversationId.textContent = `대화 ID: ${result.conversationId}`;
            ragConversationId.hidden = false;
        }
    } catch (error) {
        console.error(error);
        ragErrorOutput.textContent = `응답을 가져오지 못했습니다. ${error.message}`;
        ragErrorOutput.hidden = false;
    } finally {
        ragSubmitBtn.disabled = false;
        ragSubmitBtn.textContent = '확인';
    }
});

applyRagType(ragType.value);

// -----------------------------------------------------------------------------
// ChatMemory: in-memory(MessageChatMemory) / vector-store(VectorStoreChatMemory) 중 선택.
// 준비된 질문을 위에서부터 하나씩 실행하며, 답변이 이전 질문(대화)을 기억하는지 눈으로 확인한다.
// 대화 구분은 서버가 발급하는 HttpSession(conversationId)으로 유지된다.
// -----------------------------------------------------------------------------
const CHAT_MEMORY_CONFIG = Object.freeze({
    'in-memory': {
        label: 'MessageChatMemory (in-memory)',
        endpoint: '/ai/chat-memory/in-memory'
    },
    'vector-store': {
        label: 'VectorStoreChatMemory (vector-store)',
        endpoint: '/ai/chat-memory/vector-store'
    }
});

// 기억 여부를 확인하기 좋도록, 앞 질문의 정보를 뒤 질문이 되묻는 형태로 구성한 기본 질문 목록.
const CHAT_MEMORY_DEFAULT_QUESTIONS = [
    '나는 이름은 홍길동이고, SKALA에서 Spring AI를 현재 공부하고 있어. ',
    '내 이름이 뭐라고 했었지?',
    '내가 어디서 공부하고 있다고 했었지?',
    '내가 뭘 공부하고 있다고 했었지?',
    '지금까지 나눈 대화를 한 문장으로 요약해줘.'
];

const chatMemoryType = document.getElementById('chatMemoryType');
const chatMemoryEndpoint = document.getElementById('chatMemoryEndpoint');
const chatMemoryQuestionList = document.getElementById('chatMemoryQuestionList');
const chatMemoryAddQuestionBtn = document.getElementById('chatMemoryAddQuestionBtn');
const chatMemoryClearLogBtn = document.getElementById('chatMemoryClearLogBtn');
const chatMemoryConversationId = document.getElementById('chatMemoryConversationId');
const chatMemoryLog = document.getElementById('chatMemoryLog');
const chatMemoryLogEmpty = document.getElementById('chatMemoryLogEmpty');

let chatMemoryAskSeq = 0; // 실행 순서를 보여주기 위한 전역 일련번호(질문 목록 순서와는 별개)

function applyChatMemoryType(type) {
    const config = CHAT_MEMORY_CONFIG[type];
    if (!config) return;
    chatMemoryEndpoint.textContent = `GET ${config.endpoint}`;
}

chatMemoryType.addEventListener('change', (event) => {
    const config = CHAT_MEMORY_CONFIG[event.target.value];
    applyChatMemoryType(event.target.value);
    appendChatMemoryNote(`메모리 방식이 "${config.label}"(으)로 변경되었습니다. (서버에 저장된 대화 기록은 방식별로 별도 유지됩니다)`);
});

// 질문 목록(li) 하나를 생성한다: 순번 배지 + 수정 가능한 텍스트 + 질문하기/삭제 버튼
function createChatMemoryQuestionItem(text) {
    const item = document.createElement('li');
    item.className = 'chatmemory-question-item';

    const head = document.createElement('div');
    head.className = 'chatmemory-question-head';

    const indexBadge = document.createElement('span');
    indexBadge.className = 'chatmemory-question-index';

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'chatmemory-question-remove';
    removeBtn.textContent = '삭제';
    removeBtn.addEventListener('click', () => {
        item.remove();
        renumberChatMemoryQuestions();
    });

    head.append(indexBadge, removeBtn);

    const textarea = document.createElement('textarea');
    textarea.className = 'chatmemory-question-text';
    textarea.rows = 2;
    textarea.value = text;

    const actions = document.createElement('div');
    actions.className = 'chatmemory-question-actions';

    const askBtn = document.createElement('button');
    askBtn.type = 'button';
    askBtn.className = 'chatmemory-ask-button';
    askBtn.textContent = '이 질문하기';

    const askCount = document.createElement('span');
    askCount.className = 'chatmemory-ask-count';
    askCount.textContent = '';

    askBtn.addEventListener('click', () => askChatMemoryQuestion(item, textarea, askBtn, askCount, indexBadge));

    actions.append(askBtn, askCount);
    item.append(head, textarea, actions);

    return item;
}

// 목록 순서가 바뀔 때(추가/삭제) Q1, Q2 ... 배지를 다시 매긴다.
function renumberChatMemoryQuestions() {
    const items = chatMemoryQuestionList.querySelectorAll('.chatmemory-question-item');
    items.forEach((item, idx) => {
        const badge = item.querySelector('.chatmemory-question-index');
        badge.textContent = `Q${idx + 1}`;
    });
}

function addChatMemoryQuestion(text = '') {
    const item = createChatMemoryQuestionItem(text);
    chatMemoryQuestionList.appendChild(item);
    renumberChatMemoryQuestions();
    item.querySelector('.chatmemory-question-text').focus();
}

async function askChatMemoryQuestion(item, textarea, askBtn, askCount, indexBadge) {
    const question = textarea.value.trim();
    if (!question) {
        textarea.focus();
        return;
    }

    const config = CHAT_MEMORY_CONFIG[chatMemoryType.value];
    const questionLabel = indexBadge.textContent;

    askBtn.disabled = true;
    askBtn.textContent = '질문 중...';

    const seq = ++chatMemoryAskSeq;
    const entry = appendChatMemoryLogEntry(seq, questionLabel, question, '답변을 기다리는 중...');

    try {
        const response = await fetch(`${config.endpoint}?question=${encodeURIComponent(question)}`);
        const result = await readJsonResponse(response);

        renderMarkdown(entry.answerEl, result.answer);
        if (result.conversationId) {
            chatMemoryConversationId.textContent = `대화 ID: ${result.conversationId}`;
        }

        item.classList.add('answered');
        const askedTimes = Number(askBtn.dataset.askedTimes || '0') + 1;
        askBtn.dataset.askedTimes = String(askedTimes);
        askCount.textContent = `질문한 횟수: ${askedTimes}`;
    } catch (error) {
        console.error(error);
        entry.el.classList.add('error');
        entry.answerEl.textContent = `응답을 가져오지 못했습니다. ${error.message}`;
    } finally {
        askBtn.disabled = false;
        askBtn.textContent = '이 질문하기';
    }
}

// 대화 기록(로그)에 "질문 -> 답변" 한 건을 추가한다. 답변 영역 엘리먼트는 이후 renderMarkdown으로 갱신한다.
function appendChatMemoryLogEntry(seq, questionLabel, question, placeholderAnswer) {
    chatMemoryLogEmpty.hidden = true;

    const entryEl = document.createElement('article');
    entryEl.className = 'chatmemory-log-entry';

    const questionRow = document.createElement('div');
    questionRow.className = 'chatmemory-log-question';

    const seqBadge = document.createElement('span');
    seqBadge.className = 'chatmemory-log-seq';
    seqBadge.textContent = `#${seq} · ${questionLabel}`;

    const questionText = document.createElement('span');
    questionText.textContent = question;

    questionRow.append(seqBadge, questionText);

    const answerEl = document.createElement('div');
    answerEl.className = 'chatmemory-log-answer';
    answerEl.textContent = placeholderAnswer;

    entryEl.append(questionRow, answerEl);
    chatMemoryLog.appendChild(entryEl);
    chatMemoryLog.scrollTop = chatMemoryLog.scrollHeight;

    return { el: entryEl, answerEl };
}

function appendChatMemoryNote(message) {
    chatMemoryLogEmpty.hidden = true;

    const noteEl = document.createElement('div');
    noteEl.className = 'chatmemory-log-note';
    noteEl.textContent = message;

    chatMemoryLog.appendChild(noteEl);
    chatMemoryLog.scrollTop = chatMemoryLog.scrollHeight;
}

function clearChatMemoryLog() {
    chatMemoryLog.querySelectorAll('.chatmemory-log-entry, .chatmemory-log-note').forEach((el) => el.remove());
    chatMemoryLogEmpty.hidden = false;
    chatMemoryConversationId.textContent = '대화 ID: -';
}

chatMemoryAddQuestionBtn.addEventListener('click', () => addChatMemoryQuestion());
chatMemoryClearLogBtn.addEventListener('click', clearChatMemoryLog);

CHAT_MEMORY_DEFAULT_QUESTIONS.forEach((question) => addChatMemoryQuestion(question));
applyChatMemoryType(chatMemoryType.value);
