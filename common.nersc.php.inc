<?php

function getUsername(){
    return $_SERVER['uid'];
}

function username2uid($username){
    $uid = 0;
    $mult = 1;
    foreach (str_split(strtoupper($username)) as $c) {
        $uid += (ord($c) - 48) * $mult;
        $mult *= 48;
    }
    return $uid;
}

function getUID(){
    return username2uid(getUsername());
}

?>

