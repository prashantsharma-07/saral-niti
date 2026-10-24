// frontend/js/chatbot.js
// Person 4 — Chatbot frontend logic

const BACKEND_URL = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:5000';
// Create chatbot HTML and inject into page
function initChatbot() {
    const chatHTML = `
    <div id="chatbot-widget" style="position:fixed;bottom:24px;right:24px;z-index:9999;">
      <button id="chat-toggle" onclick="toggleChat()"
        style="background:#1a6ef5;color:white;border:none;border-radius:50%;
               width:56px;height:56px;font-size:24px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.2);">
        💬
      </button>
      <div id="chat-box" style="display:none;flex-direction:column;
           width:320px;height:420px;background:white;border-radius:16px;
           box-shadow:0 8px 24px rgba(0,0,0,0.15);margin-bottom:12px;overflow:hidden;">
        <div style="background:#1a6ef5;color:white;padding:14px 16px;font-weight:bold;">
          🤖 Saral Niti Bot
          <span onclick="toggleChat()" style="float:right;cursor:pointer;">✕</span>
        </div>
        <div id="chat-messages" style="flex:1;overflow-y:auto;padding:12px;
             display:flex;flex-direction:column;gap:8px;background:#f5f7fa;">
          <div class="bot-msg">Namaste! 🙏 Ask me about government schemes.</div>
        </div>
        <div style="display:flex;border-top:1px solid #eee;padding:8px;">
          <input id="chat-input" type="text" placeholder="Type your question..."
            onkeypress="handleKey(event)"
            style="flex:1;border:none;outline:none;padding:8px;font-size:14px;background:transparent;"/>
          <button onclick="sendMessage()"
            style="background:#1a6ef5;color:white;border:none;border-radius:8px;
                   padding:8px 14px;cursor:pointer;font-size:14px;">Send</button>
        </div>
      </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', chatHTML);
    injectChatStyles();
}

function injectChatStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .bot-msg { background:#e8eef8;border-radius:12px 12px 12px 0;padding:10px 14px;
                 max-width:80%;font-size:14px;align-self:flex-start;white-space:pre-line; }
      .user-msg { background:#1a6ef5;color:white;border-radius:12px 12px 0 12px;
                  padding:10px 14px;max-width:80%;font-size:14px;align-self:flex-end; }
    `;
    document.head.appendChild(style);
}

function toggleChat() {
    const box = document.getElementById('chat-box');
    box.style.display = box.style.display === 'none' ? 'flex' : 'none';
}

function handleKey(event) {
    if (event.key === 'Enter') sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, 'user');
    input.value = '';

    try {
        const response = await fetch(`${BACKEND_URL}/api/chatbot`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        appendMessage(data.reply, 'bot');
    } catch (err) {
        appendMessage("Sorry, I'm offline right now. Please try again later.", 'bot');
    }
}

function appendMessage(text, sender) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = sender === 'bot' ? 'bot-msg' : 'user-msg';
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Auto-init when page loads
document.addEventListener('DOMContentLoaded', initChatbot);