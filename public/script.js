const messagesDiv = document.getElementById('messages');
const messageForm = document.getElementById('message-form');
const usernameInput = document.getElementById('username');
const messageInput = document.getElementById('message-input');

// Load existing messages
async function loadMessages() {
    try {
        const response = await fetch('/messages');
        const messages = await response.json();
        displayMessages(messages);
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Display messages
function displayMessages(messages) {
    messagesDiv.innerHTML = '';
    messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        
        // Mark Claude messages with special attribute
        if (msg.username.toLowerCase() === 'claude') {
            messageDiv.setAttribute('data-claude', 'true');
        }
        
        messageDiv.innerHTML = `
            <div class="username">${msg.username}</div>
            <div class="message-text">${msg.message}</div>
            <div class="timestamp">${new Date(msg.timestamp).toLocaleString()}</div>
        `;
        messagesDiv.appendChild(messageDiv);
    });
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Send message
messageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = usernameInput.value.trim();
    const message = messageInput.value.trim();
    
    if (!username || !message) return;

    try {
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, message })
        });

        if (response.ok) {
            messageInput.value = '';
            loadMessages(); // Refresh messages
        }
    } catch (error) {
        console.error('Error sending message:', error);
    }
});

// Load messages on page load
loadMessages();

// Poll for new messages every 2 seconds
setInterval(loadMessages, 2000);