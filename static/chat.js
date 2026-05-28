let sessionId = localStorage.getItem('secucs_session_id') || '';

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesEl = document.getElementById('chatMessages');

    function scrollBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addMessage(role, content, sources) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        const avatarHtml = role === 'user'
            ? '<div class="message-avatar">👤</div>'
            : '<div class="message-avatar pet-icon"></div>';
        const safe = escapeHtml(content);
        let html = avatarHtml + `<div class="message-bubble">${safe}`;
        if (sources && sources.length > 0) {
            html += `<div class="message-sources">📎 ${sources.join(' | ')}</div>`;
        }
        html += '</div>';
        div.innerHTML = html;
        messagesEl.appendChild(div);
        scrollBottom();
        return div;
    }

    async function sendMessage(message) {
        if (!message.trim()) return;

        const sendBtn = document.getElementById('sendBtn');
        const input = document.getElementById('messageInput');
        sendBtn.disabled = true;
        input.value = '';
        input.focus();

        addMessage('user', escapeHtml(message));

        // Pet: waiting for response
        if (window.pet) window.pet.setState('waiting');

        // Move pet from old bot message to new streaming message
        const petEl = document.getElementById('petAvatar');
        const oldContainer = petEl ? petEl.parentNode : null;

        // Replace old pet position with static icon
        if (oldContainer && oldContainer.classList.contains('message')) {
            const staticIcon = document.createElement('div');
            staticIcon.className = 'message-avatar pet-icon';
            oldContainer.insertBefore(staticIcon, petEl);
            oldContainer.removeChild(petEl);
        }

        // Create new bot message and move pet into it
        const botDiv = document.createElement('div');
        botDiv.className = 'message bot';
        if (petEl) botDiv.appendChild(petEl);
        const bubbleEl = document.createElement('div');
        bubbleEl.className = 'message-bubble cursor-blink';
        botDiv.appendChild(bubbleEl);
        messagesEl.appendChild(botDiv);
        scrollBottom();

        const bubble = botDiv.querySelector('.message-bubble');
        let fullText = '';
        let sources = [];

        try {
            const resp = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: sessionId }),
            });

            // Save session id from header
            const sid = resp.headers.get('X-Session-Id');
            if (sid) {
                sessionId = sid;
                localStorage.setItem('secucs_session_id', sid);
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'token') {
                            if (!fullText && window.pet) window.pet.setState('review');
                            fullText += data.content;
                            bubble.textContent = fullText;
                            bubble.classList.add('cursor-blink');
                            scrollBottom();
                        } else if (data.type === 'done') {
                            bubble.classList.remove('cursor-blink');
                            if (window.pet) window.pet.play('waving', 1500);
                        } else if (data.type === 'sources') {
                            sources = data.sources;
                        } else if (data.type === 'error') {
                            bubble.textContent = '抱歉，服务暂不可用，请稍后重试。';
                            bubble.classList.remove('cursor-blink');
                            if (window.pet) window.pet.play('failed', 2000);
                        }
                    } catch (e) { /* skip parse errors */ }
                }
            }

            if (sources.length > 0) {
                const srcDiv = document.createElement('div');
                srcDiv.className = 'message-sources';
                srcDiv.textContent = '📎 ' + sources.join(' | ');
                bubble.appendChild(srcDiv);
            }

        } catch (err) {
            bubble.textContent = '网络错误，请检查服务是否正常运行。';
            bubble.classList.remove('cursor-blink');
            if (window.pet) window.pet.play('failed', 2000);
        }

        sendBtn.disabled = false;
        scrollBottom();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Event listeners
    sendBtn.addEventListener('click', () => sendMessage(input.value));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input.value);
        }
    });

    // Hint click
    document.querySelectorAll('.hint').forEach(el => {
        el.addEventListener('click', () => sendMessage(el.dataset.hint));
    });

    input.focus();

    // --- Dropdown menu ---
    const navBtn = document.getElementById('chatNavBtn');
    const dropdown = document.getElementById('chatDropdown');
    const sessionList = document.getElementById('sessionList');
    const btnNewChat = document.getElementById('btnNewChat');

    navBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
        if (dropdown.classList.contains('show')) loadSessionList();
    });

    document.addEventListener('click', () => dropdown.classList.remove('show'));

    btnNewChat.addEventListener('click', () => {
        localStorage.removeItem('secucs_session_id');
        sessionId = '';
        window.location.reload();
    });

    async function loadSessionList() {
        try {
            const resp = await fetch('/sessions');
            const sessions = await resp.json();
            if (!sessions.length) {
                sessionList.innerHTML = '<div class="dropdown-item placeholder">暂无历史对话</div>';
                return;
            }
            sessionList.innerHTML = sessions.map(s => {
                const date = new Date(s.last_active * 1000);
                const timeStr = date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                const active = s.id === sessionId ? ' active' : '';
                return `<div class="dropdown-item session-item${active}" data-sid="${s.id}">
                    <span class="session-title">${escapeHtml(s.title)}</span>
                    <span class="session-time">${timeStr}</span>
                    <span class="session-del" data-del="${s.id}">✕</span>
                </div>`;
            }).join('');

            sessionList.querySelectorAll('.session-item').forEach(item => {
                item.addEventListener('click', () => {
                    localStorage.setItem('secucs_session_id', item.dataset.sid);
                    window.location.reload();
                });
            });

            sessionList.querySelectorAll('.session-del').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const sid = btn.dataset.del;
                    await fetch(`/sessions/${sid}`, { method: 'DELETE' });
                    if (sid === sessionId) {
                        localStorage.removeItem('secucs_session_id');
                    }
                    loadSessionList();
                    if (sid === sessionId) window.location.reload();
                });
            });
        } catch (e) {
            sessionList.innerHTML = '<div class="dropdown-item placeholder">加载失败</div>';
        }
    }
});
