/**
 * EzaSmart Hydroponics Explainer Chatbot
 * Handles chat UI and API calls to /api/chat
 */

(function() {
  const CHAT_API = '/api/chat';

  function initChatbot() {
    const widget = document.getElementById('chatbot-widget');
    if (!widget) return;

    const toggle = widget.querySelector('.chatbot-toggle');
    const panel = widget.querySelector('.chatbot-panel');
    const closeBtn = widget.querySelector('.chatbot-close');
    const messagesDiv = widget.querySelector('.chatbot-messages');
    const inputEl = widget.querySelector('.chatbot-input');
    const sendBtn = widget.querySelector('.chatbot-send');

    const welcomeMsg = "👋 Hi there! I'm your EzaSmart hydroponics assistant. I can help you with:\n\n• pH and EC management\n• Nutrient solutions\n• Growing lettuce, tomatoes, peppers\n• System setup and troubleshooting\n\nWhat would you like to know?";

    function togglePanel() {
      const isOpening = !panel.classList.contains('open');
      panel.classList.toggle('open');
      
      if (isOpening && messagesDiv.children.length === 0) {
        // Add welcome message with slight delay for smooth animation
        setTimeout(() => {
          addMessage('bot', welcomeMsg);
        }, 150);
      }
      
      if (panel.classList.contains('open')) {
        setTimeout(() => inputEl.focus(), 200);
      }
    }

    function addMessage(role, text) {
      const div = document.createElement('div');
      div.className = `chatbot-msg ${role}`;
      div.style.opacity = '0';
      div.style.transform = 'translateY(10px)';
      div.textContent = text;
      messagesDiv.appendChild(div);
      
      // Smooth fade-in animation
      setTimeout(() => {
        div.style.transition = 'all 0.3s ease-out';
        div.style.opacity = '1';
        div.style.transform = 'translateY(0)';
      }, 10);
      
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function showTyping() {
      const div = document.createElement('div');
      div.className = 'chatbot-typing';
      div.innerHTML = '<span></span><span></span><span></span>';
      div.dataset.typing = '1';
      messagesDiv.appendChild(div);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function hideTyping() {
      const typing = messagesDiv.querySelector('[data-typing="1"]');
      if (typing) typing.remove();
    }

    async function sendMessage() {
      const text = inputEl.value.trim();
      if (!text) return;

      addMessage('user', text);
      inputEl.value = '';
      inputEl.style.height = 'auto'; // Reset height
      sendBtn.disabled = true;
      showTyping();

      try {
        const res = await fetch(CHAT_API, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        
        if (!res.ok) {
          throw new Error('Network response was not ok');
        }
        
        const data = await res.json();
        hideTyping();
        
        const response = data.response || 'Sorry, I could not generate a response.';
        addMessage('bot', response);
      } catch (err) {
        console.error('Chat error:', err);
        hideTyping();
        addMessage('bot', '❌ Sorry, there was a connection error. Please try again or check your internet connection.');
      } finally {
        sendBtn.disabled = false;
        inputEl.focus();
      }
    }

    // Auto-resize textarea as user types
    function autoResize() {
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + 'px';
    }

    // Event listeners
    toggle.addEventListener('click', togglePanel);
    closeBtn.addEventListener('click', togglePanel);
    sendBtn.addEventListener('click', sendMessage);
    
    inputEl.addEventListener('input', autoResize);
    
    inputEl.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Add escape key to close panel
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && panel.classList.contains('open')) {
        togglePanel();
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatbot);
  } else {
    initChatbot();
  }
})();
