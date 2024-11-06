<?php

$res = array();
if ($_SERVER['AUTH_TYPE'] == 'shibboleth'){
   $res["auth"] = TRUE;
   $res["username"] = $_SERVER['uid'];
} else {
   $res["auth"] = FALSE;
}

echo json_encode($res);

?>
