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
