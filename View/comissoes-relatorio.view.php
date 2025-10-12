<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatórios de Comissão - Conecta Uniforme</title>
</head>
<body>
    <h1>Relatórios de Comissão</h1>
    <p>Usuário: <?= htmlspecialchars($_SESSION['user_nome']) ?> (<?= htmlspecialchars($user_tipo) ?>)</p>
    
    <nav>
        <?php if($user_tipo == 'fornecedor'): ?>
            <a href="/dashboard-fornecedor">Dashboard</a> |
        <?php else: ?>
            <a href="/dashboard-gestor">Dashboard</a> |
        <?php endif; ?>
        <a href="/comissoes-relatorio">Relatórios</a> |
        <a href="/logout">Sair</a>
    </nav>
    
    <hr>
    
    <?php if($mensagem): ?>
        <div style="color: green; border: 1px solid green; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($mensagem) ?>
        </div>
    <?php endif; ?>
    
    <?php if($erro): ?>
        <div style="color: red; border: 1px solid red; padding: 10px; margin: 10px 0;">
            <?= htmlspecialchars($erro) ?>
        </div>
    <?php endif; ?>
    
    <?php if($user_tipo == 'gestor'): ?>
        <h2>Gerar Relatório Mensal</h2>
        <form method="POST">
            <label>Ano:</label>
            <input type="number" name="ano" value="<?= date('Y') ?>" min="2020" max="2099" style="width: 100px; padding: 5px;">
            
            <label>Mês:</label>
            <select name="mes" style="padding: 5px;">
                <?php for($m = 1; $m <= 12; $m++): ?>
                    <option value="<?= $m ?>" <?= $m == date('n') ? 'selected' : '' ?>><?= str_pad($m, 2, '0', STR_PAD_LEFT) ?></option>
                <?php endfor; ?>
            </select>
            
            <button type="submit" name="gerar_relatorio">Gerar Relatório</button>
        </form>
        
        <hr>
        
        <h2>Filtrar Comissões</h2>
        <p>
            <a href="/comissoes-relatorio">Todas</a> |
            <a href="/comissoes-relatorio?status=pendente">Pendentes</a> |
            <a href="/comissoes-relatorio?status=pago">Pagas</a>
        </p>
    <?php endif; ?>
    
    <h2>Relatórios de Comissão</h2>
    
    <?php if(count($comissoes) > 0): ?>
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>ID</th>
                    <?php if($user_tipo == 'gestor'): ?><th>Fornecedor</th><?php endif; ?>
                    <th>Mês/Ano</th>
                    <th>Total Vendas</th>
                    <th>Comissão (15%)</th>
                    <th>Valor Líquido</th>
                    <th>Status</th>
                    <th>Data Pagamento</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach($comissoes as $comissao): ?>
                    <tr>
                        <td><?= $comissao['id'] ?></td>
                        <?php if($user_tipo == 'gestor'): ?>
                            <td><?= htmlspecialchars($comissao['fornecedor_nome']) ?></td>
                        <?php endif; ?>
                        <td><?= date('m/Y', strtotime($comissao['mes_referencia'])) ?></td>
                        <td>R$ <?= number_format($comissao['total_vendas'], 2, ',', '.') ?></td>
                        <td>R$ <?= number_format($comissao['total_comissao'], 2, ',', '.') ?></td>
                        <td>R$ <?= number_format($comissao['valor_liquido'], 2, ',', '.') ?></td>
                        <td><?= $comissao['status'] == 'pago' ? '<strong style="color: green;">Pago</strong>' : '<strong style="color: orange;">Pendente</strong>' ?></td>
                        <td><?= $comissao['data_pagamento'] ? date('d/m/Y', strtotime($comissao['data_pagamento'])) : '-' ?></td>
                        <td>
                            <?php if($user_tipo == 'fornecedor'): ?>
                                <a href="/comissoes-relatorio?mes=<?= $comissao['mes_referencia'] ?>">Ver Vendas</a>
                            <?php else: ?>
                                <?php if($comissao['status'] == 'pendente'): ?>
                                    <a href="/comissoes-relatorio?editar=<?= $comissao['id'] ?>">Registrar Pagamento</a>
                                <?php else: ?>
                                    Pago em <?= date('d/m/Y', strtotime($comissao['data_pagamento'])) ?>
                                <?php endif; ?>
                            <?php endif; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else: ?>
        <p>Nenhum relatório de comissão disponível.</p>
    <?php endif; ?>
    
    <?php if($comissao_editando && $user_tipo == 'gestor'): ?>
        <hr>
        <h2>Registrar Pagamento</h2>
        <p><strong>Fornecedor:</strong> <?= htmlspecialchars($comissao_editando['fornecedor_nome']) ?></p>
        <p><strong>Mês/Ano:</strong> <?= date('m/Y', strtotime($comissao_editando['mes_referencia'])) ?></p>
        <p><strong>Valor Líquido a Pagar:</strong> R$ <?= number_format($comissao_editando['valor_liquido'], 2, ',', '.') ?></p>
        
        <form method="POST">
            <input type="hidden" name="comissao_id" value="<?= $comissao_editando['id'] ?>">
            
            <label>Valor Pago (R$):</label><br>
            <input type="number" name="valor_pago" step="0.01" required value="<?= $comissao_editando['valor_liquido'] ?>" style="width: 150px; padding: 5px;"><br><br>
            
            <label>Data do Pagamento:</label><br>
            <input type="date" name="data_pagamento" required value="<?= date('Y-m-d') ?>" style="padding: 5px;"><br><br>
            
            <button type="submit" name="registrar_pagamento">Registrar Pagamento</button>
            <a href="/comissoes-relatorio" style="margin-left: 10px;">Cancelar</a>
        </form>
    <?php endif; ?>
    
    <?php if(count($detalhes_vendas) > 0 && $user_tipo == 'fornecedor'): ?>
        <hr>
        <h2>Detalhes das Vendas</h2>
        <p><a href="/comissoes-relatorio">← Voltar</a></p>
        
        <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
            <thead>
                <tr>
                    <th>Pedido ID</th>
                    <th>Data</th>
                    <th>Escola</th>
                    <th>Aluno</th>
                    <th>Status</th>
                    <th>Total do Pedido</th>
                    <th>Valor Seus Produtos</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach($detalhes_vendas as $venda): ?>
                    <tr>
                        <td><?= $venda['pedido_id'] ?></td>
                        <td><?= date('d/m/Y H:i', strtotime($venda['criado_em'])) ?></td>
                        <td><?= htmlspecialchars($venda['escola_nome']) ?></td>
                        <td><?= htmlspecialchars($venda['aluno_nome']) ?></td>
                        <td><?= htmlspecialchars($venda['status']) ?></td>
                        <td>R$ <?= number_format($venda['total'], 2, ',', '.') ?></td>
                        <td>R$ <?= number_format($venda['valor_fornecedor'], 2, ',', '.') ?></td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php endif; ?>
</body>
</html>
