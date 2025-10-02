<?php 
require 'router.php';

/* 
O conteúdo não fica aqui. O router.php chama uma página da lista permitida baseado na url da página,
depois chama o template.php que então chama o header.php e o footer.php que são as partes de cima e de 
baixo da página. Entre o footer e header ele chama o conteúdo da página, que ficam dentro da pasta View.

A ideia é colocar qualquer HTML que repete entre todas as páginas no template, reduzindo o tanto de trabalho por
página individual. */