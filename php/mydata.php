<?php

include "common.php.inc";
$dbh = getDBHandle();

function getMyData($dbh, $uid) {
    global $config;
    $stmt = $dbh->prepare("SELECT IFNULL(SUM(total_files),0) as total_files, IFNULL(SUM(flagged_files),0) as flagged_files, (SELECT COUNT(1)+1 FROM submissions WHERE  total_files > (SELECT IFNULL((SELECT total_files FROM submissions WHERE userid = ?), 0))) as rank FROM submissions WHERE submissions.userid = ?");
    $stmt->bindParam(1, $uid, PDO::PARAM_INT);
    $stmt->bindParam(2, $uid, PDO::PARAM_INT);
    $stmt->execute();
    if ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $row['userclass'] = userClass($row['total_files']);
        $row['missingfiles'] = missingFilesForNextClass($row['total_files'], $row['userclass']);
        // convert to integers
        $row['flagged_files'] = (int)$row['flagged_files'];
        $row['total_files'] = (int)$row['total_files'];
        $row['rank'] = (int)$row['rank'];
        if (function_exists('getUsername')) $row['username'] = getUsername();
      
        return $row;
    }
    else {
        return FALSE;
    }
}

function getMyOtherProblems($dbh, $uid) {
    $stmt = $dbh->prepare("SELECT DISTINCT(detail) FROM qa WHERE userid=".$uid." AND (problem=255 or problem=1006) AND detail IS NOT NULL");
    $stmt->execute();
    $problems = array();
    while ($row = $stmt->fetch(PDO::FETCH_NUM))
        array_push($problems, $row[0]);
    return $problems;
}

$uid = getUIDFromSID($dbh);
if ($uid !== FALSE) {
    $result = getMyData($dbh, $uid);
    $result['problems'] = getMyOtherProblems($dbh, $uid);
    echo json_encode($result);
}
?>
