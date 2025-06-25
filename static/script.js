document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatWindow = document.getElementById('chat-window');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Function to generate or retrieve a unique thread_id for the session
    function getOrCreateThreadId() {
        let threadId = sessionStorage.getItem('welloChatThreadId');
        if (!threadId) {
            // A simple way to generate a random enough ID for this purpose
            threadId = 'thread_' + Math.random().toString(36).substring(2, 15);
            sessionStorage.setItem('welloChatThreadId', threadId);
        }
        return threadId;
    }

    // Function to add a new message to the UI
    function addMessageToUI(sender, text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.textContent = text;
        chatWindow.appendChild(messageElement);
        // Auto-scroll to the latest message
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = messageInput.value.trim();
        if (!userMessage) return;

        // Display user's message immediately
        addMessageToUI('user', userMessage);
        messageInput.value = '';

        // Show the thinking indicator
        typingIndicator.style.display = 'block';

        try {
            const threadId = getOrCreateThreadId();

            // Call the backend API
            const response = await fetch('/chat/invoke', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    thread_id: threadId,
                }),
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Add the final response from Wello
            addMessageToUI('wello', data.response);

        } catch (error) {
            console.error('Error:', error);
            addMessageToUI('wello', 'Sorry, an error occurred. Please try again.');
        } finally {
            // Always hide the thinking indicator
            typingIndicator.style.display = 'none';
        }
    });
});