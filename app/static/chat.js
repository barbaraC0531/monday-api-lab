const messagesEl = document.querySelector('#messages');
const statusEl = document.querySelector('#status');
const form = document.querySelector('#chat-form');
const input = document.querySelector('#message-input');
let conversationId = localStorage.getItem('mondayConversationId');

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = `${role}: ${text}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function ensureConversation() {
  if (conversationId) {
    const res = await fetch(`/api/conversations/${conversationId}`);
    if (res.ok) {
      const data = await res.json();
      data.messages.forEach(m => addMessage(m.role, m.text));
      return;
    }
    localStorage.removeItem('mondayConversationId');
  }
  const res = await fetch('/api/conversations', { method: 'POST' });
  const data = await res.json();
  conversationId = data.conversation_id;
  localStorage.setItem('mondayConversationId', conversationId);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMessage('user', text);
  statusEl.textContent = 'Thinking...';
  statusEl.className = 'status';
  form.querySelector('button').disabled = true;
  try {
    const res = await fetch(`/api/conversations/${conversationId}/messages`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    addMessage('assistant', data.assistant_message.text);
    statusEl.textContent = '';
  } catch (error) {
    statusEl.textContent = error.message;
    statusEl.className = 'status error';
  } finally {
    form.querySelector('button').disabled = false;
  }
});

ensureConversation().catch(error => { statusEl.textContent = error.message; statusEl.className = 'status error'; });
