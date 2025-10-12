<?php
// Listagem / gestão básica de usuários (apenas lista para admin)
require_once __DIR__ . '/../funcoes.php';

$usuarios = consulta_sql('SELECT u.id, u.nome, u.email, u.role, u.ativo, e.nome as escola FROM usuario u LEFT JOIN escola e ON u.escola_id = e.id');

include __DIR__ . '/../View/usuarios.view.php';
