"""
============================================
CORE - MODELS
============================================
Classes de modelo (entidades) do sistema
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Usuario:
    """Modelo de usuário"""
    id: Optional[int] = None
    nome: str = ''
    email: str = ''
    telefone: Optional[str] = None
    tipo: str = ''  # administrador, escola, fornecedor, responsavel
    ativo: bool = True
    data_cadastro: Optional[datetime] = None
    data_atualizacao: Optional[datetime] = None


@dataclass
class Escola:
    """Modelo de escola"""
    id: Optional[int] = None
    usuario_id: int = 0
    cnpj: str = ''
    razao_social: str = ''
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    ativo: bool = True


@dataclass
class GestorEscolar:
    """Modelo de gestor escolar"""
    id: Optional[int] = None
    escola_id: int = 0
    nome: str = ''
    email: Optional[str] = None
    telefone: Optional[str] = None
    cpf: Optional[str] = None
    tipo_gestor: Optional[str] = None
    data_cadastro: Optional[datetime] = None


@dataclass
class Fornecedor:
    """Modelo de fornecedor"""
    id: Optional[int] = None
    usuario_id: int = 0
    cnpj: str = ''
    razao_social: str = ''
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    ativo: bool = True


@dataclass
class Produto:
    """Modelo de produto"""
    id: Optional[int] = None
    fornecedor_id: int = 0
    escola_id: Optional[int] = None
    nome: str = ''
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    tamanho: Optional[str] = None
    cor: Optional[str] = None
    preco: float = 0.0
    estoque: int = 0
    imagem_url: Optional[str] = None
    ativo: bool = True
    data_cadastro: Optional[datetime] = None


@dataclass
class Pedido:
    """Modelo de pedido"""
    id: Optional[int] = None
    responsavel_id: int = 0
    escola_id: Optional[int] = None
    status: str = 'carrinho'  # carrinho, pendente, pago, cancelado
    valor_total: float = 0.0
    data_pedido: Optional[datetime] = None
    data_atualizacao: Optional[datetime] = None


@dataclass
class ItemPedido:
    """Modelo de item de pedido"""
    id: Optional[int] = None
    pedido_id: int = 0
    produto_id: int = 0
    quantidade: int = 0
    preco_unitario: float = 0.0
    subtotal: float = 0.0


@dataclass
class Responsavel:
    """Modelo de responsável"""
    id: Optional[int] = None
    usuario_id: int = 0
    cpf: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None


@dataclass
class RepasseFinanceiro:
    """Modelo de repasse financeiro"""
    id: Optional[int] = None
    fornecedor_id: int = 0
    pedido_id: int = 0
    valor: float = 0.0
    taxa_plataforma: float = 0.0
    valor_liquido: float = 0.0
    status: str = 'pendente'  # pendente, concluido, cancelado
    data_repasse: Optional[datetime] = None
    data_processamento: Optional[datetime] = None
