/**
 * RPP Expert Chat Widget - SIQROO Edition
 * Versión: 1.0.0
 * Desarrollado para: ConsultaRPP - Quintana Roo / Puebla
 */

(function() {
    class RPPChatWidget extends HTMLElement {
        constructor() {
            super();
            this.attachShadow({ mode: 'open' });
            this.state = { isOpen: false, messages: [] };
        }

        static get observedAttributes() {
            return ['primary-color', 'bot-name', 'endpoint', 'accent-color'];
        }

        connectedCallback() {
            this.render();
        }

        toggleChat() {
            this.state.isOpen = !this.state.isOpen;
            this.render();
        }

        async sendMessage() {
            const input = this.shadowRoot.querySelector('#chat-input');
            const message = input.value.trim();
            if (!message) return;

            // Add user message to UI
            this.state.messages.push({ role: 'user', content: message });
            input.value = '';
            this.render();

            const chatContainer = this.shadowRoot.querySelector('.chat-body');
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                // Show thinking status
                const thinkingMsg = { role: 'assistant', content: '...', isThinking: true };
                this.state.messages.push(thinkingMsg);
                this.render();

                const endpoint = this.getAttribute('endpoint') || 'http://localhost:3001';
                const response = await fetch(`${endpoint}/api/v1/chat/query`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Remove thinking and add real response
                this.state.messages = this.state.messages.filter(m => !m.isThinking);
                this.state.messages.push({ 
                    role: 'assistant', 
                    content: data.data.response,
                    sources: data.data.sources 
                });
                
                this.render();
            } catch (error) {
                console.error("Widget Error:", error);
                this.state.messages = this.state.messages.filter(m => !m.isThinking);
                this.state.messages.push({ role: 'assistant', content: 'Lo siento, hubo un error al conectar con el servicio.' });
                this.render();
            }
        }

        render() {
            const primaryColor = this.getAttribute('primary-color') || '#004a87';
            const accentColor = this.getAttribute('accent-color') || '#f0f4f8';
            const botName = this.getAttribute('bot-name') || 'Consultor Experto';
            const endpoint = this.getAttribute('endpoint') || '';

            const style = `
                :host {
                    --primary: ${primaryColor};
                    --accent: ${accentColor};
                    --bg: #ffffff;
                    --text: #1a202c;
                    font-family: 'Inter', system-ui, sans-serif;
                }
                .widget-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; }
                .launcher {
                    width: 60px; height: 60px; border-radius: 30px;
                    background: var(--primary); color: white;
                    display: flex; align-items: center; justify-content: center;
                    cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    transition: transform 0.3s ease; font-size: 24px;
                }
                .launcher:hover { transform: scale(1.1); }
                .chat-window {
                    width: 380px; height: 500px; background: white;
                    border-radius: 16px; margin-bottom: 15px;
                    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                    display: ${this.state.isOpen ? 'flex' : 'none'};
                    flex-direction: column; overflow: hidden;
                    animation: slideUp 0.3s ease-out;
                }
                @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
                .chat-header { background: var(--primary); color: white; padding: 15px; display: flex; align-items: center; justify-content: space-between; }
                .chat-body { flex: 1; padding: 15px; overflow-y: auto; background: var(--accent); display: flex; flex-direction: column; gap: 10px; }
                .message { padding: 10px 14px; border-radius: 12px; max-width: 80%; font-size: 14px; line-height: 1.4; }
                .user-msg { align-self: flex-end; background: var(--primary); color: white; border-bottom-right-radius: 2px; }
                .bot-msg { align-self: flex-start; background: white; color: var(--text); border-bottom-left-radius: 2px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
                .chat-footer { padding: 15px; display: flex; gap: 10px; border-top: 1px solid #eee; }
                #chat-input { flex: 1; border: 1px solid #ddd; border-radius: 20px; padding: 8px 15px; outline: none; }
                .send-btn { background: var(--primary); color: white; border: none; width: 34px; height: 34px; border-radius: 17px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
                .btn-close { cursor: pointer; font-size: 20px; }
                .sources { font-size: 10px; margin-top: 5px; color: #718096; border-top: 1px solid #edf2f7; padding-top: 4px; }
            `;

            const messagesHtml = this.state.messages.map(m => `
                <div class="message ${m.role === 'user' ? 'user-msg' : 'bot-msg'}">
                    ${m.content}
                    ${m.sources && m.sources.length > 0 ? `<div class="sources">Fuentes: ${m.sources.join(', ')}</div>` : ''}
                </div>
            `).join('');

            this.shadowRoot.innerHTML = `
                <style>${style}</style>
                <div class="widget-container">
                    <div class="chat-window">
                        <div class="chat-header">
                            <div style="font-weight: 600;">${botName}</div>
                            <div class="btn-close" id="close-chat">&times;</div>
                        </div>
                        <div class="chat-body" id="chat-body">
                            ${messagesHtml || '<div class="bot-msg">¡Hola! Soy tu consultor experto en temas registrales. ¿En qué puedo ayudarte hoy?</div>'}
                        </div>
                        <div class="chat-footer">
                            <input type="text" id="chat-input" placeholder="Escribe tu consulta..." />
                            <button class="send-btn" id="send-btn">➔</button>
                        </div>
                    </div>
                    <div class="launcher" id="chat-launcher">
                        ${this.state.isOpen ? '✕' : '💬'}
                    </div>
                </div>
            `;

            // Event Listeners
            this.shadowRoot.querySelector('#chat-launcher').onclick = () => this.toggleChat();
            this.shadowRoot.querySelector('#close-chat').onclick = () => this.toggleChat();
            this.shadowRoot.querySelector('#send-btn').onclick = () => this.sendMessage();
            this.shadowRoot.querySelector('#chat-input').onkeypress = (e) => {
                if (e.key === 'Enter') this.sendMessage();
            };
        }
    }

    if (!customElements.get('rpp-chat-widget')) {
        customElements.define('rpp-chat-widget', RPPChatWidget);
    }
})();
