<?php
// Arquivo simples para criar Model do logout
session_start();
session_destroy();
header('Location: /conecta-uniforme/');
exit;
