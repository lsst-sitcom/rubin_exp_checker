<?php

include "common.php.inc";
$dbh = getDBHandle();

if (isset($_GET['problem'])) {
    if (array_search($_GET['problem'], array_keys($config['problem_code'])) !== FALSE) {
        $code = $config['problem_code'][$_GET['problem']];
        $sql = 'SELECT qa.qaid as qa_id, expname, ccd, band, problem, x, y, detail FROM qa JOIN files ON (files.fileid=qa.fileid)';
        if (isset($_GET['short']))
            $sql = 'SELECT qa.qaid as qa_id, ccd, band, problem, x, y FROM qa JOIN files ON (files.fileid=qa.fileid)';
        $sql .= ' WHERE problem=' . $code . ' OR problem=-' . $code;
        $sql .= ' ORDER BY expname, ccd ASC';
        $stm = $dbh->prepare($sql);
        $stm->execute();
        $result = array();
        while($row = $stm->fetch(PDO::FETCH_ASSOC)) {
            $row['qa_id'] = intval($row['qa_id']);
            $row['ccd'] = $row['ccd'];
            $row['problem'] = intval($row['problem']);
            if ($row['problem'] != 0) { // good exposure don't have locations
                // correct for downsampling of factor 4
                //$row['x'] = intval($row['x'])*4;
                //$row['y'] = intval($row['y'])*4;
                // return raw pixel value
                $row['x'] = intval($row['x']);
                $row['y'] = intval($row['y']);
            }
            if (!isset($_GET['short'])) {
                $row['false_positive'] = FALSE;
                if ($row['problem'] < 0)
                    $row['false_positive'] = TRUE;
                $row['problem'] = $_GET['problem'];
                $row['release'] = $config['release'];
            }
            else
                unset($row['problem']);
            array_push($result, $row);
        }
        echo json_encode($result);
    }
    else {
        echo "Problem unknown!";
    }
}
?>
