<?php

include "common.php.inc";
$dbh = getDBHandle();

function getMyDataOld($dbh, $uid) {
    global $config;
    $stmt = $dbh->prepare("SELECT IFNULL(SUM(total_files),0) as total_files, IFNULL(SUM(flagged_files),0) as flagged_files, (SELECT COUNT(1)+1 FROM submissions WHERE release=? AND total_files > (SELECT IFNULL((SELECT total_files FROM submissions WHERE userid = ? and release = ?), 0))) as rank FROM submissions WHERE submissions.userid = ?");
    $stmt->bindParam(1, $config['release'], PDO::PARAM_STR, 4);
    $stmt->bindParam(2, $uid, PDO::PARAM_INT);
    $stmt->bindParam(3, $config['release'], PDO::PARAM_STR, 4);
    $stmt->bindParam(4, $uid, PDO::PARAM_INT);
    $stmt->execute();
    if ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $row['userclass'] = userClass($row['total_files']);
        $row['missingfiles'] = missingFilesForNextClass($row['total_files'], $row['userclass']);
        // convert to integers
        $row['flagged_files'] = (int)$row['flagged_files'];
        $row['total_files'] = (int)$row['total_files'];
        $row['rank'] = (int)$row['rank'];
        if (function_exists('getUsername')) $row['username'] = getUsername();
        $row['version'] = SQLite3::version();
        return $row;
    }
    else {
        return FALSE;
    }
}

//This query builds a temporary table with ranked users.
//See description in addendum here:
//https://stackoverflow.com/a/28378633/4075339
//But unfortunately this doesn't work with the version of PHP at NERSC
//https://stackoverflow.com/a/26588223/4075339
//"WITH tt (userid, total_files, flagged_files) AS (SELECT userid, COUNT(userid) AS total_files, SUM(problem > 0) AS flagged_files FROM qa GROUP BY userid) SELECT total_files,flagged_files,(select count(*)+1 FROM tt AS r WHERE r.total_files > s.total_files) AS rank FROM tt AS s WHERE userid = 436584464947"

function getMyData($dbh, $uid) {
    global $config;

    // default values
    $response = array();
    $response['total_files'] = 0;
    $response['flagged_files'] = 0;
    $response['rank'] = 0;

    $stmt = $dbh->prepare("SELECT userid, COUNT(userid) AS total_files, SUM(problem > 0) AS flagged_files FROM qa WHERE userid = ? GROUP BY userid");
    $stmt->bindParam(1, $uid, PDO::PARAM_INT);
    $stmt->execute();
    if ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        // convert to integers
        $response['total_files'] = (int)$row['total_files'];
        $response['flagged_files'] = (int)$row['flagged_files'];
    }

    // get the rank (this should always succeed)
    $stmt = $dbh->prepare("SELECT COUNT(*)+1 as rank from (SELECT COUNT(userid) as total_files FROM qa GROUP BY userid) where total_files > ?");
    $stmt->bindParam(1, $response['total_files'], PDO::PARAM_INT);
    $stmt->execute();
    if ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $response['rank'] = (int)$row['rank'];
    }

    // set some more metadata     
    $response['userclass'] = userClass($response['total_files']);
    $response['missingfiles'] = missingFilesForNextClass($response['total_files'], $response['userclass']);
    if (function_exists('getUsername')) $response['username'] = getUsername();
    // for debugging
    $response['version'] = SQLite3::version();

    return $response;
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
