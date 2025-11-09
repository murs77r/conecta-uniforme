"""
Módulo de Autenticação
Gerencia login, logout e controle de acesso
"""
from .module import autenticacao_bp, verificar_sessao, verificar_permissao

__all__ = ['autenticacao_bp', 'verificar_sessao', 'verificar_permissao']
