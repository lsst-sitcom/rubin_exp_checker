<?php

function download_file($file, $revalidate = False) { // $file = include path 
        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Transfer-Encoding: binary');
        if ($revalidate) {
                header('Expires: 0');
                header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
                header('Pragma: public');
        } else {
                header('Date: Thu, 03 Jul 2014 00:00:00 GMT');
                header('Cache-Control: max-age=31556926');
        }
        ob_clean();
        flush();
        readfile($file);
        exit;
}
include("common.php.inc");
// A newline is leaking in somewhere
ob_clean();
flush();
setRelease();

if (isset($_GET['type'])) {
   $dbh = getDBHandle();
   if ($_GET['type'] == "fov") {
     $path = str_replace("%e", $_GET['expname'], $config['fovpath'][$config['release']]);
	echo $path;
	download_file($path);
     //download_file("assets/fov_not_available.png");
   }

   if ($_GET['type'] == "dm") {
     $sql = 'SELECT name FROM files WHERE expname = ? and ccd = ?';
     $stmt = $dbh->prepare($sql);
     $stmt->bindParam(1, $_GET['expname'], PDO::PARAM_STR, 14);
     $stmt->bindParam(2, $_GET['ccd'], PDO::PARAM_STR, 14);
     $stmt->execute();
     $res = check_or_abort($stmt);
     $row = $res->fetch(PDO::FETCH_ASSOC);

     //echo "not available yet!";

     // This would use download_file
     //$path = 'https://'.$config['domain'].'/getImage.php?release='.$config['release'].'name='.$row['name'];

     // This provides the url
     $path = 'https://'.$config['domain'].$config['fitspath'][$config['release']].$row['name'];
     echo $path;
   }	  
}
else {
        $path = $config['fitspath'][$config['release']];
        download_file($path.$_GET['name'], True);
        // For debug, comment out previous line and uncomment following lines
        //$response = array();
	//$response['file'] = $path.$_GET['name'];
	//echo json_encode($response);
}
?>
