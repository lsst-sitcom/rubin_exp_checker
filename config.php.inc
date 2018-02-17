<?php
//ADW: Let's see...
ini_set('display_errors', 1); 

$config = array(
    "adminemail" => "yymao.astro@gmail.com",
    "adminname" => "exposure checker",
    "domain" => "portal.nersc.gov/projecta/lsst/desc-exp-checker",
    "userdb" => ".db/users.DC2-test.db",
    "filedb" => array("DC2" => ".db/files.DC2-test.db"),
    
    //"userdb" => "exclusive/users.db",
    //"filedb" => array("SVA1" => "exclusive/files.SVA1.db",
    //                  "Y1A1" => "exclusive/files.Y1A1.db",
    //                  "Y2T2" => "exclusive/files.Y2T2.db",
    //                  "Y2T4" => "exclusive/files.Y2T4.db"),
    // 
    "dmpath" => array("DC2" => "https://desar2.cosmology.illinois.edu/DESFiles/desardata/OPS/red/%r/red/%e/%e_%c.fits.fz"),
    "fitspath" => array("DC2" => "https://portal.nersc.gov/projecta/lsst/desc-exp-checker/exclusive/"),
    "fovpath" => array("DC2" => "https://portal.nersc.gov/projecta/lsst/desc-exp-checker/exclusive/focalplane_summary/%e-focalplane-summary.png"),

//https://expchecker:ySLZR2pKAZ@desar2.cosmology.illinois.edu/DESFiles/desardata/QA/se_pngs/Y1A1/%r/%e/%e_proj_TN.png"),

    "releases" => array("DC2"),
    "release" => NULL, # set by client
    "images_per_fp" => 394,
    "problem_code" => array(
      "OK" => 0,

      // Instrument
      "Guiding" => 11,
      "Shutter" => 12,
      "Readout" => 13,
      "Haze" => 14,

      // Flat fielding
      "A/B jump" => 21,
      "Fringing" => 22,
      "Tape bump" => 23,
      "Tree rings" => 24,
      "Vertical jump" => 25,
      "Vertical stripes" => 26,

      // Reflections
      "Ghost" => 32,
      "Bright spray" => 31,
      "Brush strokes" => 33,
      "Bright arc" => 34,

      // Tracks
      "Satellite" => 41,
      "Airplane" => 42,

      // Masking
      "Column mask" => 51,
      "Excessive mask" => 53,
      "Cosmic ray" => 54,
      "Cross-talk" => 55,
      "Edge-bleed" => 56,

      // Sky estimation
      "Dark rim" => 61,
      "Dark halo" => 62,
      "Quilted sky" => 63,
      "Wavy sky" => 64,
      "Anti-bleed" => 65,

      "Other..." => 255,
      "Awesome!" => 1000,
    )
);
?>
