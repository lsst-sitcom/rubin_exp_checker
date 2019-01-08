<?php

include "common.php.inc";
$dbh = getDBHandle();

$query = 'SELECT userid, total_files, flagged_files FROM submissions WHERE total_files > 0 ORDER BY total_files DESC';
if (isset($_GET['limit'])) {
  if (is_numeric($_GET['limit'])) {
    $query .= ' LIMIT ?';
    $stmt = $dbh->prepare($query);
    $stmt->bindParam(1, $_GET['limit'], PDO::PARAM_INT);
  }
} else {
  $stmt = $dbh->prepare($query);
}
$stmt->execute();
check_or_abort($stmt);
$response = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo json_encode($response);
?>
