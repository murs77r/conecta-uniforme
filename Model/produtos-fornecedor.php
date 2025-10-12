<?php
require_once __DIR__ . '/../conexao.php';
require_once __DIR__ . '/../classes/Produto.php';
require_once __DIR__ . '/../classes/Homologacao.php';

iniciarSessaoSegura();

if(!isset($_SESSION['logado']) || $_SESSION['user_tipo'] !== 'Fornecedor') {
	header('Location: /login-novo');
	exit;
}

$produtoClass = new Produto();
$homologacaoClass = new Homologacao();

$Fornecedor_id = (int)($_SESSION['user_id'] ?? 0);

$mensagem = '';
$erro = '';
$produto_editando = null;
$variacoes = [];

// Listar escolas homologadas para o fornecedor atual
$sqlEscolas = "SELECT e.*\n                FROM escola e\n                INNER JOIN homologacao h ON e.id = h.escola_id\n                WHERE h.Fornecedor_id = $Fornecedor_id AND h.ativo = 1\n                ORDER BY e.nome";
$resultadoEscolas = $con->query($sqlEscolas);
$escolas_disponiveis = $resultadoEscolas ? $resultadoEscolas->fetch_all(MYSQLI_ASSOC) : [];

// Ações de produtos
if(isset($_POST['criar_produto'])) {
	$dados = [
		'Fornecedor_id' => $Fornecedor_id,
		'nome' => trim($_POST['nome'] ?? ''),
		'descricao' => trim($_POST['descricao'] ?? ''),
		'preco' => (float)($_POST['preco'] ?? 0),
	];

	if($dados['nome'] === '' || $dados['preco'] <= 0) {
		$erro = 'Informe nome e preço válidos para o produto.';
	} else {
		$produto_id = $produtoClass->criar($dados);
		if($produto_id) {
			$escolasSelecionadas = $_POST['escolas'] ?? [];
			foreach($escolasSelecionadas as $registro) {
				[$escolaIdRaw, $serie] = array_pad(explode('|', $registro, 2), 2, null);
				$escolaId = (int)$escolaIdRaw;

				if($escolaId > 0 && $serie) {
					$produtoClass->homologarProduto($produto_id, $escolaId, $serie);
				}
			}

			$mensagem = 'Produto criado com sucesso!';
		} else {
			$erro = 'Não foi possível criar o produto. Verifique se os dados estão corretos.';
		}
	}
}

if(isset($_POST['atualizar_produto'])) {
	$produto_id = (int)($_POST['produto_id'] ?? 0);
	$dados = [
		'nome' => trim($_POST['nome'] ?? ''),
		'descricao' => trim($_POST['descricao'] ?? ''),
		'preco' => (float)($_POST['preco'] ?? 0),
	];

	if($produto_id <= 0) {
		$erro = 'Produto inválido.';
	} elseif($dados['nome'] === '' || $dados['preco'] <= 0) {
		$erro = 'Informe nome e preço válidos para o produto.';
	} else {
		$produtoAtual = $produtoClass->buscarPorId($produto_id);
		if(!$produtoAtual || (int)$produtoAtual['Fornecedor_id'] !== $Fornecedor_id) {
			$erro = 'Produto não encontrado ou sem permissão.';
		} elseif($produtoClass->atualizar($produto_id, $dados)) {
			$mensagem = 'Produto atualizado com sucesso!';
		} else {
			$erro = 'Erro ao atualizar o produto.';
		}
	}
}

if(isset($_POST['toggle_produto'])) {
	$produto_id = (int)($_POST['produto_id'] ?? 0);
	$status = (int)($_POST['status'] ?? 0);

	$produtoAtual = $produtoClass->buscarPorId($produto_id);
	if(!$produtoAtual || (int)$produtoAtual['Fornecedor_id'] !== $Fornecedor_id) {
		$erro = 'Produto inválido.';
	} elseif($produtoClass->ativarDesativar($produto_id, $status)) {
		$mensagem = 'Status do produto atualizado.';
	} else {
		$erro = 'Erro ao atualizar status do produto.';
	}
}

if(isset($_POST['adicionar_variacao'])) {
	$produto_id = (int)($_POST['produto_id'] ?? 0);
	$dadosVariacao = [
		'tamanho' => trim($_POST['tamanho'] ?? ''),
		'cor' => trim($_POST['cor'] ?? ''),
		'genero' => trim($_POST['genero'] ?? ''),
		'quantidade_estoque' => (int)($_POST['quantidade'] ?? 0)
	];

	if($produto_id <= 0 || $dadosVariacao['tamanho'] === '' || $dadosVariacao['genero'] === '') {
		$erro = 'Preencha tamanho e gênero para a variação.';
	} else {
		$produtoAtual = $produtoClass->buscarPorId($produto_id);
		if(!$produtoAtual || (int)$produtoAtual['Fornecedor_id'] !== $Fornecedor_id) {
			$erro = 'Produto inválido.';
		} elseif($produtoClass->adicionarVariacao($produto_id, $dadosVariacao)) {
			$mensagem = 'Variação adicionada com sucesso!';
		} else {
			$erro = 'Erro ao adicionar variação.';
		}
	}
}

if(isset($_POST['atualizar_estoque'])) {
	$variacao_id = (int)($_POST['variacao_id'] ?? 0);
	$quantidade = (int)($_POST['quantidade'] ?? 0);

	if($variacao_id > 0) {
		// Verificar se a variação pertence a um produto do fornecedor
		$sqlVariacao = "SELECT pv.id, p.Fornecedor_id\n                        FROM produto_variacao pv\n                        INNER JOIN produto p ON pv.produto_id = p.id\n                        WHERE pv.id = $variacao_id";
		$resultadoVariacao = $con->query($sqlVariacao);
		$dadosVariacao = $resultadoVariacao ? $resultadoVariacao->fetch_assoc() : null;

		if(!$dadosVariacao || (int)$dadosVariacao['Fornecedor_id'] !== $Fornecedor_id) {
			$erro = 'Variação inválida.';
		} elseif($produtoClass->atualizarEstoque($variacao_id, $quantidade)) {
			$mensagem = 'Estoque atualizado com sucesso!';
		} else {
			$erro = 'Erro ao atualizar estoque.';
		}
	}
}

// Buscar dados atuais
$produtos = $produtoClass->listarPorFornecedor($Fornecedor_id);

if(isset($_GET['editar'])) {
	$produto_id = (int)$_GET['editar'];
	$produto_editando = $produtoClass->buscarPorId($produto_id);

	if(!$produto_editando || (int)$produto_editando['Fornecedor_id'] !== $Fornecedor_id) {
		$produto_editando = null;
		$erro = 'Produto não encontrado ou sem permissão.';
	} else {
		$variacoes = $produtoClass->buscarVariacoes($produto_id);
	}
}

require __DIR__ . '/../View/produtos-fornecedor.view.php';
