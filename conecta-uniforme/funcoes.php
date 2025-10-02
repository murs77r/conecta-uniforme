<?php
function consulta_sql($sql) {
    $resultado = $mysqli->query($sql);
    $resultado = $resultado->fetch_all(MYSQLI_ASSOC);

    return array_change_key_case($resultado, CASE_LOWER); // transforma tudo em lower case só pra ter certeza.
}