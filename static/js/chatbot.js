// SHOPLIO Enhanced Chatbot JavaScript
// Fully trained on all products with smart formatting

document.addEventListener('DOMContentLoaded', function () {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');

    // Toggle chatbot window
    chatbotToggle.addEventListener('click', function () {
        if (chatbotWindow.style.display === 'none' || !chatbotWindow.style.display) {
            chatbotWindow.style.display = 'flex';
            chatbotInput.focus();
        } else {
            chatbotWindow.style.display = 'none';
        }
    });

    // Add hover effect to chatbot icon
    const chatIcon = chatbotToggle.querySelector('img');
    if (chatIcon) {
        chatIcon.addEventListener('mouseenter', () => chatIcon.style.transform = 'scale(1.1)');
        chatIcon.addEventListener('mouseleave', () => chatIcon.style.transform = 'scale(1)');
    }

    // Close chatbot
    chatbotClose.addEventListener('click', function () {
        chatbotWindow.style.display = 'none';
    });

    // Format text with markdown-style formatting
    function formatMessage(text) {
        // Convert **bold** to <strong>
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Convert line breaks
        text = text.replace(/\n/g, '<br>');

        // Convert bullet points
        text = text.replace(/^• /gm, '&bull; ');

        return text;
    }

    // Send message function
    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        chatbotInput.value = '';

        // Show typing indicator
        const typingIndicator = addMessage('Typing...', 'bot', true);

        // Send to backend
        fetch('/chatbot-api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'message=' + encodeURIComponent(message)
        })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                typingIndicator.remove();

                // Add bot response with formatting
                addMessage(data.response, 'bot');
            })
            .catch(error => {
                typingIndicator.remove();
                addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                console.error('Error:', error);
            });
    }

    // Add message to chat
    function addMessage(text, type, isTyping = false) {
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            padding: 0.8rem;
            margin-bottom: 0.75rem;
            border-radius: 12px;
            max-width: 85%;
            ${type === 'user' ?
                'background: #FF6B00; color: white; margin-left: auto; text-align: right;' :
                'background: white; color: #1F2937; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'
            }
            ${isTyping ? 'opacity: 0.6; font-style: italic;' : ''}
        `;

        if (isTyping) {
            messageDiv.textContent = text;
        } else {
            messageDiv.innerHTML = formatMessage(text);
        }

        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

        return messageDiv;
    }

    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Send on button click
    chatbotSend.addEventListener('click', sendMessage);

    // Send on Enter key
    chatbotInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
