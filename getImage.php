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
setRelease();

if (isset($_GET['type'])) {
   $dbh = getDBHandle();
   if ( True ) {
      if ($_GET['type'] == "fov") {
        $path = str_replace("%e", $_GET['expname'], $config['fovpath'][$config['release']]);
	echo $path;
	download_file($path);
        //download_file("assets/fov_not_available.png");
      }

     if ($_GET['type'] == "dm")
       echo "not available yet!";
   }
   else {
     if ($_GET['type'] == "dm")
       echo "not available yet!";
     if ($_GET['type'] == "fov")
       download_file("assets/fov_not_available.png");
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
