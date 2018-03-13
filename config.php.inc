<?php
//ADW: Let's see...
//ini_set('display_errors', 1); 

$config = array(
    "adminemail" => "kadrlica@fnal.gov",
    "adminname" => "exposure checker",
    "domain" => "portal.nersc.gov/projecta/lsst/desc-exp-checker",
    "userdb" => ".db/users.DC2-test.db",
    "filedb" => array("DC2" => ".db/files.DC2-test.db",
                      "r1.1" => ".db/files.r1.1-test.db"),
    
    //"userdb" => "exclusive/users.db",
    //"filedb" => array("SVA1" => "exclusive/files.SVA1.db",
    //                  "Y1A1" => "exclusive/files.Y1A1.db",
    //                  "Y2T2" => "exclusive/files.Y2T2.db",
    //                  "Y2T4" => "exclusive/files.Y2T4.db"),
    // 
    "dmpath" => array("DC2" => "/global/projecta/projectdirs/lsst/groups/SSim/DC2/eyeball/full_fp_data/test_out/%e/%r/%s_%h.fits",
                      "r1.1" => "./exclusive/full_fp_data/"),

    "fitspath" => array("DC2" => "https://portal.nersc.gov/projecta/lsst/desc-exp-checker/exclusive/binned_sensor_halves/",
                        "r1.1" => "./exclusive/binned_sensor_halves/"),

    "fovpath" => array("DC2" => "https://portal.nersc.gov/projecta/lsst/desc-exp-checker/exclusive/focalplane_summary/%e-focalplane-summary.png",
                       "r1.1" => "./exclusive/focalplane_summary/%e-focalplane-summary.png"),

    "releases" => array("DC2",
                        "r1.1"),
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

      // Simulation
      "Speckling" => 71,
      "Cosmic" => 72,
      "Star" => 73,
      "Galaxy" => 74,
      "Sky background" => 75,
      "Instrument" => 76,

      "Other..." => 255,
      "Awesome!" => 1000,
    )
);
?>
