// Deep Research Agent plugin for Open WebUI

class DeepResearchPlugin {
    constructor() {
        this.sessions = new Map();
        this.apiEndpoint = pluginConfig.endpoint || 'http://localhost:8000';

        // Register plugin with Open WebUI
        this.registerPlugin();
    }

    async registerPlugin() {
        try {
            // Register UI components
            await this.registerUIComponents();

            // Register API handlers
            await this.registerAPIHandlers();

            console.log('Deep Research Agent plugin initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Deep Research Agent plugin:', error);
        }
    }

    async registerUIComponents() {
        // Register a new chat type for research
        await webui.registerChatType({
            id: 'research',
            name: 'Research Chat',
            icon: 'search',
            description: 'Deep research with Groq and Perplexica',
            createHandler: () => this.createResearchChat()
        });

        // Add a toolbar button for research mode
        await webui.addToolbarButton({
            id: 'new-research-chat',
            icon: 'science',
            label: 'New Research',
            position: 'right',
            action: () => this.createNewResearchChat()
        });
    }

    async registerAPIHandlers() {
        // Register custom API handlers
        webui.on('message:send', async (event) => {
            const {chatId, message} = event.detail;

            // Check if this is a research chat
            if (this.sessions.has(chatId)) {
                event.preventDefault(); // Prevent default handling
                await this.handleResearchQuery(chatId, message);
            }
        });

        // Handle chat deletion
        webui.on('chat:delete', async (event) => {
            const {chatId} = event.detail;
            if (this.sessions.has(chatId)) {
                await this.cleanupSession(chatId);
            }
        });
    }

    async createResearchChat() {
        // Generate a new session ID
        const sessionId = 'research-' + Date.now();

        // Create a new chat in the UI
        const chatId = await webui.createChat({
            title: 'Research Session',
            type: 'research',
            metadata: {
                sessionId: sessionId
            }
        });

        // Create a new research session on the backend
        try {
            await fetch(`${this.apiEndpoint}/api/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({session_id: sessionId})
            });

            // Store session information
            this.sessions.set(chatId, {
                sessionId: sessionId,
                websocket: null,
                status: 'idle'
            });

            // Connect WebSocket
            this.connectWebSocket(chatId, sessionId);

            // Add welcome message
            await webui.addSystemMessage({
                chatId,
                content: 'Welcome to the Deep Research Assistant! Ask me any research question, and I\'ll provide a comprehensive answer using Groq\'s DeepSeek-R1 model and Perplexica search.',
            });

            return chatId;
        } catch (error) {
            console.error('Failed to create research session:', error);
            await webui.addSystemMessage({
                chatId,
                content: 'Error: Failed to initialize research session. Please try again.',
            });
            return chatId;
        }
    }

    async createNewResearchChat() {
        return this.createResearchChat();
    }

    connectWebSocket(chatId, sessionId) {
        const session = this.sessions.get(chatId);
        if (!session) return;

        // Close existing WebSocket if any
        if (session.websocket) {
            session.websocket.close();
        }

        // Create new WebSocket connection
        const wsUrl = `${this.apiEndpoint.replace('http', 'ws')}/ws/${sessionId}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log(`WebSocket connected for session ${sessionId}`);
        };

        ws.onmessage = async (event) => {
            const data = JSON.parse(event.data);
            await this.handleWebSocketMessage(chatId, data);
        };

        ws.onerror = (error) => {
            console.error(`WebSocket error for session ${sessionId}:`, error);
        };

        ws.onclose = () => {
            console.log(`WebSocket closed for session ${sessionId}`);

            // Reconnect if session still exists
            if (this.sessions.has(chatId)) {
                setTimeout(() => {
                    this.connectWebSocket(chatId, sessionId);
                }, 5000); // Reconnect after 5 seconds
            }
        };

        // Store the WebSocket
        session.websocket = ws;
    }

    async handleWebSocketMessage(chatId, data) {
        const session = this.sessions.get(chatId);
        if (!session) return;

        const event = data.event;
        const eventData = data.data || {};

        switch (event) {
            case 'token':
                // Handle streaming token
                await webui.updateLastMessage({
                    chatId,
                    append: eventData.token,
                    done: false
                });
                break;

            case 'research_start':
                // Research started
                session.status = 'processing';
                await webui.updateChatStatus({
                    chatId,
                    status: 'typing'
                });

                // Create initial message
                await webui.addAssistantMessage({
                    chatId,
                    content: 'Researching...',
                    metadata: {
                        model: 'DeepSeek-R1',
                        provider: 'Groq/Ollama'
                    }
                });
                break;

            case 'tool_start':
                // Tool execution started
                await webui.addThinkingMessage({
                    chatId,
                    content: `Using tool: ${eventData.tool}\nInput: ${eventData.input}`
                });
                break;

            case 'tool_end':
                // Tool execution completed
                await webui.addThinkingMessage({
                    chatId,
                    content: `Tool result: ${eventData.output}`
                });
                break;

            case 'research_complete':
                // Research completed
                session.status = 'idle';
                await webui.updateChatStatus({
                    chatId,
                    status: 'idle'
                });

                // Update the final message
                await webui.updateLastMessage({
                    chatId,
                    content: eventData.response.result,
                    done: true,
                    metadata: {
                        model: eventData.response.model,
                        provider: eventData.response.provider,
                        process_time: `${eventData.response.process_time.toFixed(2)}s`
                    }
                });
                break;

            case 'research_error':
                // Research error
                session.status = 'error';
                await webui.updateChatStatus({
                    chatId,
                    status: 'idle'
                });

                // Update message with error
                await webui.updateLastMessage({
                    chatId,
                    content: `Error: ${eventData.error.error}`,
                    done: true,
                    metadata: {
                        error: true
                    }
                });
                break;

            case 'session_state':
                // Session state update
                // Handle existing messages if any
                if (eventData.messages && eventData.messages.length > 0) {
                    for (const message of eventData.messages) {
                        if (message.role === 'user') {
                            await webui.addUserMessage({
                                chatId,
                                content: message.content
                            });
                        } else if (message.role === 'assistant') {
                            await webui.addAssistantMessage({
                                chatId,
                                content: message.content,
                                done: true
                            });
                        }
                    }
                }
                break;
        }
    }

    async handleResearchQuery(chatId, message) {
        const session = this.sessions.get(chatId);
        if (!session) return;

        // Check if a research is already in progress
        if (session.status === 'processing') {
            await webui.addSystemMessage({
                chatId,
                content: 'Please wait for the current research to complete before submitting a new query.',
            });
            return;
        }

        // Add user message to UI
        await webui.addUserMessage({
            chatId,
            content: message
        });

        // Submit query to backend
        try {
            const response = await fetch(`${this.apiEndpoint}/api/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: message,
                    session_id: session.sessionId
                })
            });

            if (!response.ok) {
                throw new Error('Failed to submit research query');
            }

            // Backend will send updates via WebSocket
            session.status = 'processing';

        } catch (error) {
            console.error('Error submitting research query:', error);
            await webui.addSystemMessage({
                chatId,
                content: `Error: ${error.message}`,
            });
        }
    }

    async cleanupSession(chatId) {
        const session = this.sessions.get(chatId);
        if (!session) return;

        // Close WebSocket
        if (session.websocket) {
            session.websocket.close();
        }

        // Delete session on backend
        try {
            await fetch(`${this.apiEndpoint}/api/sessions/${session.sessionId}`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Error deleting session:', error);
        }

        // Remove from local sessions map
        this.sessions.delete(chatId);
    }
}

// Initialize plugin when loaded
const deepResearchPlugin = new DeepResearchPlugin();
