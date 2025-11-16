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
     * Converte a primeira mensagem flash Bootstrap em um modal.
     * Previne a exibição de múltiplos modais se houver várias mensagens.
     */
    function converterFlashParaModal() {
        // Se já existe um modal de mensagem, não faz nada
        if (document.querySelector('.modal.fade.show')) {
            return;
        }

        const alertNode = document.querySelector('.alert[role="alert"]');
        
        if (alertNode) {
            // Extrai tipo e mensagem do primeiro alerta encontrado
            const classes = alertNode.className;
            let tipo = 'info';
            
            if (classes.includes('alert-success')) tipo = 'success';
            else if (classes.includes('alert-danger')) tipo = 'danger';
            else if (classes.includes('alert-warning')) tipo = 'warning';
            
            const mensagem = alertNode.textContent.replace(/×/g, '').trim();
            
            // Remove todos os alertas da página para evitar duplicatas
            document.querySelectorAll('.alert[role="alert"]').forEach(alert => alert.remove());
            
            // Exibe o modal com a mensagem
            if (mensagem) {
                mostrarModal(tipo, mensagem);
            }
        }
    }

    return {
        mostrarModal,
        converterFlashParaModal
    };
})();

// Exportar para uso global
window.App = App;

// Inicialização automática
document.addEventListener('DOMContentLoaded', function() {
    // Converter mensagens flash em modais automaticamente
    App.converterFlashParaModal();
});
