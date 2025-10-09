<?php
try {
    if ($con = new mysqli("localhost", "root", "", "conecta_uniformes")) {

    } else {
        throw new Exception();
    }
}
catch(Exception $e) {
    $con = new mysqli("localhost", "root", "senac", "conecta_uniformes");
}