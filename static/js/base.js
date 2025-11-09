/**
 * Conecta Uniforme - Base Script
 */

// Utilitários Gerais
const App = (function() {
    'use strict';

    /**
     * Exibe mensagem em modal
     */
    function mostrarModal(tipo, mensagem, titulo = null) {
        // Mapeamento de tipos para cores e ícones
        const config = {
            success: { cor: 'success', icone: 'bi-check-circle-fill', titulo: 'Sucesso' },
            danger: { cor: 'danger', icone: 'bi-x-circle-fill', titulo: 'Erro' },
            warning: { cor: 'warning', icone: 'bi-exclamation-triangle-fill', titulo: 'Atenção' },
            info: { cor: 'info', icone: 'bi-info-circle-fill', titulo: 'Informação' }
        };

        const cfg = config[tipo] || config.info;
        const tituloFinal = titulo || cfg.titulo;

        // Criar modal dinamicamente
        const modalId = 'modalMensagem_' + Date.now();
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-${cfg.cor} text-white">
                            <h5 class="modal-title">
                                <i class="bi ${cfg.icone} me-2"></i>${tituloFinal}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${mensagem}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Adicionar ao DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalElement = document.getElementById(modalId);
        const modal = new bootstrap.Modal(modalElement);

        // Remover do DOM após fechar
        modalElement.addEventListener('hidden.bs.modal', function() {
            modalElement.remove();
        });

        modal.show();
    }

    /**
     * Converte mensagens flash Bootstrap em modais
     */
    function converterFlashParaModal() {
        const alerts = document.querySelectorAll('.alert[role="alert"]');
        
        alerts.forEach(alert => {
            // Extrair tipo e mensagem
            const classes = alert.className;
            let tipo = 'info';
            
            if (classes.includes('alert-success')) tipo = 'success';
            else if (classes.includes('alert-danger')) tipo = 'danger';
            else if (classes.includes('alert-warning')) tipo = 'warning';
            
            const mensagem = alert.textContent.replace('×', '').trim();
            
            // Remover alert
            alert.remove();
            
            // Mostrar modal
            mostrarModal(tipo, mensagem);
        });
    }

    return {
        mostrarModal,
        converterFlashParaModal
    };
})();

// WebAuthn/Passkey
const WebAuthn = (function() {
    'use strict';

    function b64urlToArrayBuffer(b64url) {
        const pad = '='.repeat((4 - b64url.length % 4) % 4);
        const b64 = b64url.replace(/-/g, '+').replace(/_/g, '/') + pad;
        const raw = atob(b64);
        const buffer = new ArrayBuffer(raw.length);
        const view = new Uint8Array(buffer);
        for (let i = 0; i < raw.length; i++) {
            view[i] = raw.charCodeAt(i);
        }
        return buffer;
    }

    function arrayBufferToB64url(buf) {
        const bytes = new Uint8Array(buf);
        let bin = '';
        bytes.forEach(b => bin += String.fromCharCode(b));
        return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    async function registrar() {
        try {
            const response = await fetch('/auth/webauthn/registro/opcoes');
            const options = await response.json();

            if (options.erro) {
                throw new Error(options.erro);
            }

            options.challenge = b64urlToArrayBuffer(options.challenge);
            options.user.id = b64urlToArrayBuffer(options.user.id);

            if (options.excludeCredentials) {
                options.excludeCredentials = options.excludeCredentials.map(c => ({
                    type: c.type,
                    id: b64urlToArrayBuffer(c.id)
                }));
            }

            const credential = await navigator.credentials.create({ publicKey: options });

            const credentialData = {
                id: credential.id,
                rawId: arrayBufferToB64url(credential.rawId),
                type: credential.type,
                response: {
                    attestationObject: arrayBufferToB64url(credential.response.attestationObject),
                    clientDataJSON: arrayBufferToB64url(credential.response.clientDataJSON)
                },
                transports: credential.response.getTransports ? credential.response.getTransports() : []
            };

            const finishResponse = await fetch('/auth/webauthn/registro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentialData)
            });

            if (!finishResponse.ok) {
                throw new Error(`Falha na requisição: ${finishResponse.status} ${finishResponse.statusText}`);
            }

            const result = await finishResponse.json();

            if (result.status !== 'ok') {
                throw new Error(result.erro || 'Erro desconhecido');
            }

            return { success: true, message: 'Passkey cadastrada com sucesso!' };

        } catch (error) {
            console.error('Erro ao registrar Passkey:', error);
            return { success: false, message: error.message };
        }
    }

    async function login(email, tipo = null) {
        try {
            const params = new URLSearchParams({ email });
            if (tipo) params.append('tipo', tipo);

            const response = await fetch(`/auth/webauthn/login/opcoes?${params.toString()}`);
            const options = await response.json();

            if (options.erro) {
                if (options.erro === 'selecionar_tipo' && Array.isArray(options.tipos)) {
                    return { needsTypeSelection: true, tipos: options.tipos };
                }
                throw new Error(options.erro);
            }

            options.challenge = b64urlToArrayBuffer(options.challenge);

            if (options.allowCredentials) {
                options.allowCredentials = options.allowCredentials.map(c => ({
                    type: c.type,
                    id: b64urlToArrayBuffer(c.id)
                }));
            }

            const assertion = await navigator.credentials.get({ publicKey: options });

            const assertionData = {
                id: assertion.id,
                rawId: arrayBufferToB64url(assertion.rawId),
                type: assertion.type,
                response: {
                    authenticatorData: arrayBufferToB64url(assertion.response.authenticatorData),
                    clientDataJSON: arrayBufferToB64url(assertion.response.clientDataJSON),
                    signature: arrayBufferToB64url(assertion.response.signature),
                    userHandle: assertion.response.userHandle 
                        ? arrayBufferToB64url(assertion.response.userHandle) 
                        : null
                }
            };

            if (tipo) {
                assertionData.tipo = tipo;
            }

            const finishResponse = await fetch('/auth/webauthn/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(assertionData)
            });

            const result = await finishResponse.json();

            if (result.erro === 'selecionar_tipo' && Array.isArray(result.tipos)) {
                return { needsTypeSelection: true, tipos: result.tipos };
            }

            if (result.status !== 'ok') {
                throw new Error(result.erro || 'Falha na autenticação');
            }

            return { success: true, redirectUrl: '/home' };

        } catch (error) {
            console.error('Erro no login Passkey:', error);
            return { success: false, message: error.message };
        }
    }

    async function anular(credentialId) {
        try {
            const response = await fetch('/auth/webauthn/anular', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: credentialId })
            });

            const result = await response.json();

            if (result.status !== 'ok') {
                throw new Error(result.erro || 'Erro ao anular Passkey');
            }

            return { success: true, message: 'Passkey anulada com sucesso.' };

        } catch (error) {
            console.error('Erro ao anular Passkey:', error);
            return { success: false, message: error.message };
        }
    }

    return {
        registrar,
        login,
        anular
    };
})();

// Exportar para uso global
window.App = App;
window.WebAuthn = WebAuthn;

// Inicialização automática
document.addEventListener('DOMContentLoaded', function() {
    // Converter mensagens flash em modais automaticamente
    App.converterFlashParaModal();
});
