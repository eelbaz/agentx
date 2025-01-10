// Global state
let selectedProvider = null;
let selectedModel = null;
let currentSessionId = null;
let ws = null;

// Available LLM providers
const providers = [
    { id: 'ollama', name: 'Ollama' },
    { id: 'openai', name: 'OpenAI' },
    { id: 'anthropic', name: 'Anthropic' },
    { id: 'deepseek', name: 'DeepSeek' }
];

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Model selection handling
async function selectProvider(providerId) {
    selectedProvider = providerId;
    selectedModel = null;
    
    // Update UI
    document.getElementById('selected-provider').textContent = providers.find(p => p.id === providerId).name;
    document.getElementById('selected-model').textContent = 'Select Model';
    
    // Close provider dropdown
    toggleProviderDropdown();
    
    // Fetch and populate models
    try {
        const response = await fetch(`/api/models/${providerId}`);
        const models = await response.json();
        
        const modelDropdown = document.getElementById('model-dropdown');
        modelDropdown.innerHTML = models.map(model => `
            <button onclick="selectModel('${model.id}')" class="w-full text-left px-4 py-2 hover:bg-[#3A3D44]">
                ${model.name}
            </button>
        `).join('');
        
        // Show model dropdown
        toggleModelDropdown();
    } catch (error) {
        console.error('Error fetching models:', error);
        const modelDropdown = document.getElementById('model-dropdown');
        modelDropdown.innerHTML = '<div class="px-4 py-2 text-red-500">Error loading models</div>';
    }
}

function selectModel(modelId) {
    selectedModel = modelId;
    
    // Update UI
    const modelDropdown = document.getElementById('model-dropdown');
    const selectedButton = modelDropdown.querySelector(`button[onclick="selectModel('${modelId}')"]`);
    document.getElementById('selected-model').textContent = selectedButton.textContent.trim();
    
    // Close model dropdown
    toggleModelDropdown();
    
    // Enable new chat button if both provider and model are selected
    const newChatBtn = document.getElementById('new-chat-btn');
    newChatBtn.disabled = false;
    newChatBtn.classList.remove('opacity-50');

    // Start new chat automatically when model is selected
    startNewChat();
}

// Dropdown handling
function toggleProviderDropdown() {
    const dropdown = document.getElementById('provider-dropdown');
    dropdown.classList.toggle('show');
    // Close model dropdown when opening provider dropdown
    document.getElementById('model-dropdown').classList.remove('show');
}

function toggleModelDropdown() {
    // Only allow opening model dropdown if provider is selected
    if (!selectedProvider) {
        alert('Please select a provider first');
        return;
    }
    const dropdown = document.getElementById('model-dropdown');
    dropdown.classList.toggle('show');
}

// Initialize dropdowns
function initializeDropdowns() {
    const providerDropdown = document.getElementById('provider-dropdown');
    providerDropdown.innerHTML = providers.map(provider => `
        <button onclick="selectProvider('${provider.id}')" class="w-full text-left px-4 py-2 hover:bg-[#3A3D44]">
            ${provider.name}
        </button>
    `).join('');

    // Close dropdowns when clicking outside
    window.addEventListener('click', function(event) {
        if (!event.target.closest('#provider-selector')) {
            document.getElementById('provider-dropdown').classList.remove('show');
        }
        if (!event.target.closest('#model-selector')) {
            document.getElementById('model-dropdown').classList.remove('show');
        }
    });
}

// Chat initialization
async function startNewChat() {
    if (!selectedProvider || !selectedModel) {
        alert('Please select a provider and model first');
        return;
    }
    
    try {
        const response = await fetch('/api/chat/new', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.session_id) {
            // Store session ID
            currentSessionId = data.session_id;
            
            // Clear chat messages and show welcome message
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = `
                <div class="flex mb-4">
                    <div class="flex items-start max-w-3xl relative">
                        <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-medium mr-4">
                            A
                        </div>
                        <div class="bg-[#2A2D34] rounded-lg p-4">
                            <div class="text-sm text-gray-300 whitespace-pre-wrap">
                                Hello! I'm ready to help. What would you like to discuss?
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Enable message input and send button
            const messageInput = document.getElementById('message-input');
            const sendButton = document.querySelector('button[onclick="sendMessage()"]');
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.placeholder = 'Type your message...';
            
            // Update WebSocket connection
            if (ws) {
                ws.close();
            }
            ws = new WebSocket(`ws://${window.location.host}/ws/chat/${data.session_id}`);
            ws = setupWebSocketReconnection(ws);
            
            // Set up message handler with logging
            ws.onmessage = function(event) {
                console.log('WebSocket message received:', event.data);
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
        }
    } catch (error) {
        console.error('Error starting new chat:', error);
        alert('Failed to start new chat');
    }
}

// Message handling
function handleMessage(data) {
    console.log('WebSocket message received:', typeof data === 'string' ? data : JSON.stringify(data, null, 2));
    const chatMessages = document.getElementById('chat-messages');
    
    if (data.type === 'thinking') {
        console.log('Processing thinking state:', data.value);
        const thinkingIndicator = document.getElementById('thinking-indicator');
        if (thinkingIndicator) {
            thinkingIndicator.style.display = data.value ? 'block' : 'none';
        }
        
        // Enable/disable input based on thinking state
        const messageInput = document.getElementById('message-input');
        const sendButton = document.querySelector('button[onclick="sendMessage()"]');
        messageInput.disabled = data.value;
        sendButton.disabled = data.value;
        
        // Update button appearance
        if (data.value) {
            sendButton.classList.add('opacity-50', 'cursor-not-allowed');
            isProcessing = true;
        } else {
            sendButton.classList.remove('opacity-50', 'cursor-not-allowed');
            messageInput.focus();
            isProcessing = false;
        }
    } else if (data.type === 'message') {
        console.log('Processing message:', JSON.stringify(data.content, null, 2));
        
        // Skip user messages as they're already added in sendMessage
        if (data.content.role === 'user') {
            console.log('Skipping user message as it was already added');
            return;
        }
        
        const messageId = data.content.id || Date.now().toString();
        const existingMessage = document.getElementById(`message-${messageId}`);
        
        // Format the content based on message type
        let formattedContent = data.content.content;
        if (typeof formattedContent === 'object') {
            try {
                // Format nested objects recursively
                function formatNestedObject(obj, level = 0) {
                    if (!obj || typeof obj !== 'object') {
                        return String(obj);
                    }
                    const indent = '  '.repeat(level);
                    return Object.entries(obj)
                        .map(([key, value]) => {
                            if (value && typeof value === 'object') {
                                const nestedFormatted = formatNestedObject(value, level + 1);
                                return `${indent}${key}:\n${nestedFormatted}`;
                            }
                            return `${indent}${key}: ${value}`;
                        })
                        .join('\n');
                }
                
                formattedContent = formatNestedObject(formattedContent);
                console.log('Formatted content:', formattedContent);
            } catch (e) {
                console.error('Error formatting content:', e);
                formattedContent = JSON.stringify(formattedContent, null, 2);
            }
        }
        
        if (existingMessage) {
            console.log('Updating existing message');
            const contentDiv = existingMessage.querySelector('.text-gray-300');
            if (contentDiv) {
                contentDiv.innerHTML = formatMessage(formattedContent);
                if (!data.content.is_streaming) {
                    // Add a subtle animation to show the message is complete
                    contentDiv.style.transition = 'opacity 0.3s ease';
                    contentDiv.style.opacity = '1';
                }
            }
        } else if (data.content.role === 'assistant') {
            console.log('Creating new assistant message');
            const messageDiv = document.createElement('div');
            messageDiv.id = `message-${messageId}`;
            
            messageDiv.className = 'flex mb-4';
            messageDiv.innerHTML = `
                <div class="flex items-start max-w-3xl relative">
                    <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-medium mr-4">
                        A
                    </div>
                    <div class="bg-[#2A2D34] rounded-lg p-4">
                        <div class="text-sm text-gray-300 whitespace-pre-wrap ${data.content.is_streaming ? 'opacity-80' : ''}">
                            ${formatMessage(formattedContent)}
                        </div>
                    </div>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            messageDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Reset state when message is complete
        if (!data.content.is_streaming) {
            console.log('Processing complete message');
            const thinkingIndicator = document.getElementById('thinking-indicator');
            if (thinkingIndicator) {
                thinkingIndicator.style.display = 'none';
            }
            
            isProcessing = false;
            const messageInput = document.getElementById('message-input');
            const sendButton = document.querySelector('button[onclick="sendMessage()"]');
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        }
    }
}

// Message formatting
function formatMessage(content) {
    if (typeof content === 'object') {
        content = JSON.stringify(content, null, 2);
    }
    
    // Handle code blocks with language
    content = content.replace(/```(\w+)?\n([\s\S]+?)\n```/g, (match, lang, code) => {
        return `<pre class="bg-[#1A1D24] p-4 rounded-lg overflow-x-auto mt-2 mb-2"><code class="language-${lang || ''}">${code}</code></pre>`;
    });
    
    // Handle inline code
    content = content.replace(/`([^`]+)`/g, '<code class="bg-[#1A1D24] px-2 py-1 rounded">$1</code>');
    
    // Handle URLs
    content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="text-blue-500 hover:underline">$1</a>');
    
    // Handle newlines
    content = content.replace(/\n/g, '<br>');
    
    return content;
}

// Message sending
async function sendMessage() {
    console.log('1. sendMessage called');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.querySelector('button[onclick="sendMessage()"]');
    const message = messageInput.value.trim();
    
    if (!message || !currentSessionId || !selectedProvider || !selectedModel || isProcessing) {
        console.log('2. Message validation failed:', {
            hasMessage: !!message,
            hasSessionId: !!currentSessionId,
            hasProvider: !!selectedProvider,
            hasModel: !!selectedModel,
            isProcessing
        });
        return;
    }
    
    try {
        console.log('3. Starting message processing');
        // Set processing state
        isProcessing = true;
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        // Show thinking indicator immediately
        const thinkingIndicator = document.getElementById('thinking-indicator');
        if (thinkingIndicator) {
            console.log('4. Showing thinking indicator');
            thinkingIndicator.style.display = 'block';
        }
        
        // Add user message to chat immediately
        console.log('5. Adding user message to chat');
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex justify-end mb-4';
        messageDiv.innerHTML = `
            <div class="flex items-start max-w-2xl relative">
                <div class="bg-[#1A1D24] rounded-lg p-4">
                    <div class="text-sm text-gray-300 whitespace-pre-wrap">
                        ${formatMessage(message)}
                    </div>
                </div>
                <div class="w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center text-sm font-medium ml-4">
                    U
                </div>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        messageDiv.scrollIntoView({ behavior: 'smooth' });
        
        // Clear input immediately after showing the message
        console.log('6. Clearing input');
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        console.log('7. Sending API request');
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                provider: selectedProvider,
                model: selectedModel,
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        console.log('8. API request successful');
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message');
    }
}

// Model refresh
async function refreshModels() {
    if (!selectedProvider) {
        alert('Please select a provider first');
        return;
    }
    
    try {
        const response = await fetch(`/api/models/${selectedProvider}`);
        const models = await response.json();
        
        const modelDropdown = document.getElementById('model-dropdown');
        modelDropdown.innerHTML = models.map(model => `
            <button onclick="selectModel('${model.id}')" class="w-full text-left px-4 py-2 hover:bg-[#3A3D44]">
                ${model.name}
            </button>
        `).join('');
    } catch (error) {
        console.error('Error refreshing models:', error);
        alert('Failed to refresh models');
    }
}

// WebSocket setup
function setupWebSocketReconnection(ws) {
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const baseDelay = 1000;

    ws.onclose = () => {
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = baseDelay * Math.pow(2, reconnectAttempts);
            setTimeout(() => {
                reconnectAttempts++;
                ws = new WebSocket(`ws://${window.location.host}/ws/chat/${currentSessionId}`);
                setupWebSocketReconnection(ws);
            }, delay);
        }
    };

    return ws;
}

// Add processing state variable
let isProcessing = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dropdowns
    initializeDropdowns();
    
    // Set up input auto-resize
    const messageInput = document.getElementById('message-input');
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
    
    // Handle Enter key for sending messages
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            if (!isProcessing) {
                sendMessage();
            }
        }
    });
}); 