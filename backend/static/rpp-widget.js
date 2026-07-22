/**
 * RPP Expert Chat Widget - SIQROO Edition
 * Versión: 2.0.0 (Iframe Wrapper)
 * Desarrollado para: ConsultaRPP - Quintana Roo / Puebla
 */

(function() {
    class RPPChatWidget extends HTMLElement {
        constructor() {
            super();
            this.attachShadow({ mode: 'open' });
            this.state = { isOpen: false };
        }

        static get observedAttributes() {
            return ['primary-color', 'bot-name', 'endpoint', 'app-url', 'profile-id'];
        }

        connectedCallback() {
            this.renderStructure();
            this.updateView();
        }

        toggleChat() {
            this.state.isOpen = !this.state.isOpen;
            this.updateView();
        }

        updateView() {
            const chatWindow = this.shadowRoot.querySelector('.chat-window');
            const launcher = this.shadowRoot.querySelector('#chat-launcher');
            
            if (chatWindow) {
                chatWindow.style.display = this.state.isOpen ? 'flex' : 'none';
            }
            if (launcher) {
                launcher.innerHTML = this.state.isOpen ? '✕' : '💬';
            }
        }

        renderStructure() {
            const primaryColor = this.getAttribute('primary-color') || '#004a87';
            const botName = this.getAttribute('bot-name') || 'Consultor Experto';
            const endpoint = this.getAttribute('endpoint') || window.location.origin;
            const profileId = this.getAttribute('profile-id') || 'general';
            
            // Si app-url no está seteada, construirla con el profile_id
            let appUrl = this.getAttribute('app-url');
            if (!appUrl) {
                appUrl = `${endpoint}/widget?profile_id=${profileId}`;
            }

            const style = `
                .widget-container { position: fixed; bottom: 20px; right: 20px; z-index: 999999; display: flex; flex-direction: column; align-items: flex-end; }
                .launcher {
                    width: 60px; height: 60px; border-radius: 30px;
                    background: ${primaryColor}; color: white;
                    display: flex; align-items: center; justify-content: center;
                    cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    transition: transform 0.3s ease; font-size: 28px;
                    border: none;
                }
                .launcher:hover { transform: scale(1.1); }
                .chat-window {
                    width: 420px; height: 650px; background: white;
                    border-radius: 20px; margin-bottom: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    display: none;
                    flex-direction: column; overflow: hidden;
                    animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                    border: 1px solid rgba(0,0,0,0.1);
                }
                @keyframes slideUp { from { opacity: 0; transform: translateY(40px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
                iframe { width: 100%; height: 100%; border: none; }
                @media (max-width: 480px) {
                    .chat-window { width: 95vw; height: 90vh; right: 2.5vw; bottom: 80px; }
                }
            `;

            this.shadowRoot.innerHTML = `
                <style>${style}</style>
                <div class="widget-container">
                    <div class="chat-window">
                        <iframe src="${appUrl}" title="${botName}" allow="clipboard-write"></iframe>
                    </div>
                    <button class="launcher" id="chat-launcher">💬</button>
                </div>
            `;

            this.shadowRoot.querySelector('#chat-launcher').onclick = () => this.toggleChat();
        }
    }

    if (!customElements.get('rpp-chat-widget')) {
        customElements.define('rpp-chat-widget', RPPChatWidget);
    }
})();
