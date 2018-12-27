var webfits = null;
var stretch = "arcsinh";
var spinner;
var marks = [];
var problem = null;
var fileid = null;
var expname = null;
var ccd = null;
var problem_default = null;
var has_reported_problems = false;

function addMark(prob, ctx) {
  var color = '#FFFF00';
  if (ctx === undefined)
    ctx = webfits.overlayCtx;
  else
    color = '#FFA500';
  ctx.beginPath();
  if (prob.problem[0] == "-") {
    ctx.moveTo(prob.x-28, prob.y-28);
    ctx.lineTo(prob.x+28, prob.y+28);
    ctx.moveTo(prob.x-28, prob.y+28);
    ctx.lineTo(prob.x+28, prob.y-28);
  }
  else
    ctx.arc(prob.x, prob.y, 40, 0, 2*Math.PI, true);
  ctx.lineWidth=2;
  ctx.strokeStyle=color;
  ctx.shadowColor = '#000000';
  ctx.shadowBlur = 10;
  ctx.shadowOffsetX = 6;
  ctx.shadowOffsetY = 3;
  ctx.stroke();

  ctx.font = '14px Helvetica';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = color;
  ctx.shadowColor = '#000000';
  ctx.shadowBlur = 3;
  ctx.shadowOffsetX = 2;
  ctx.shadowOffsetY = 1;
  ctx.fillText(prob.problem, prob.x, prob.y);
}

function overlayCallback(_this, opts, evt) {
  if (problem !== null) {
    // add circle around dbl-clicked location
    var rect = _this.canvas.getBoundingClientRect();
    var negative = '';
    if ($('#negative-button').hasClass('active'))
      negative = '-';
    var prob = {
      x: (evt.clientX - rect.left + 0.5), // for unknown reasons, there is a 0.5 pixel shift in rect.left/right
      y: (evt.clientY - rect.top),
      problem: negative + problem,
      detail: $('#problem-text').val() == "" ? null : $('#problem-text').val()
    };
    marks.push(prob);
    addMark(prob);
    
    // show the clear button
    $('#clear-button').show();
  }
}

function clearMarks(ctx) {
  if (ctx === undefined) {
    ctx = webfits.overlayCtx;
    marks = [];
  }
  ctx.clearRect(0,0,webfits.canvas.width, webfits.canvas.height);
}

function clearLastMark() {
  marks.pop();
  webfits.overlayCtx.clearRect(0,0,webfits.canvas.width, webfits.canvas.height);
  for (var i=0; i < marks.length; i++) {
    addMark(marks[i]);
  }
}

// Define callback to be executed after image is received from the server
function getImage(f, opts) {
  // Get image data unit (ADW: Can the HDU indices be set in config?)
  var hdu = 1;
  console.log('Loading IMAGE data from HDU: ' + hdu);
  var dataunit = f.getDataUnit(hdu);
  // Set options to pass to the next callback
  opts["dataunit"] = dataunit;
  opts["f"] = f;
  // Asynchronously get pixels representing the image passing a callback and options
  // First argument is the frame to load the image into
  dataunit.getFrameAsync(0, createVisualization, opts);
}

// Define callback for when pixels have been read from file
function createVisualization(arr, opts) {
  // Load the image into web elements
  var dataunit = opts.dataunit;
  var width = dataunit.width;
  var height = dataunit.height;
      
  // Get the DOM element
  var el = $('#wicked-science-visualization').get(0);
  
  var callbacks = {
    onclick: overlayCallback
  };
  // Initialize the WebFITS context with a viewer of size width
  if (webfits === null) {
    webfits = new astro.WebFITS(el, width, height);
    webfits.setupControls(callbacks, opts);
  }
  
  // Load array representation of image
  webfits.loadImage('exposure', arr, width, height);

  // Set the intensity range and stretch
  if (opts.release != "Y1A1" && opts.release != "SVA1" && opts.release != "DC2")
      webfits.setRescaling(4.);	
  webfits.setExtent(-1, 1000);  // to prevent crazy values in min/max
  webfits.setStretch(stretch);

  // add weight/bad-pixel map (ADW: Again, should be set in config)
  var hdu = 2;
  console.log('Loading MASK data from HDU: '+hdu);
  var dataunit = opts.f.getDataUnit(hdu);
  // Set options to pass to the next callback
  opts["dataunit"] = dataunit;
  // Asynchronously get pixels representing the image passing a callback and options
  dataunit.getFrameAsync(0, addMaskLayer, opts);
}

function addMaskLayer(arr, opts) {
  var dataunit = opts.dataunit;
  var width = dataunit.width;
  var height = dataunit.height;
  
  webfits.loadImage('bpm', arr, width, height);
  webfits.draw();
  completeVisualization(opts);
}

// to be done once all elements of webfits are in place
function completeVisualization(response) {
  // add marks if present in response
  if (response.marks !== undefined) {
    for (var i=0; i < response.marks.length; i++) {
      addMark(response.marks[i], webfits.reportCtx);
    }
    has_reported_problems = true;
  }
  // set file-dependent information
  fileid = response.fileid;
  expname = response.expname;
  ccd = response.ccd;
  release = response.release; // locally overwrite the default release to make sure it's from this file

  // the image label, colored badge for Y-band
  if (response.band == 'Y')
    $('#image_name').html(release + ", " + expname + ', CCD ' + ccd + ", <span class='badge badge-important'>" + response.band + "-band</span>");
  else
    $('#image_name').html(release + ", " + expname + ', CCD ' + ccd + ", " + response.band + "-band");

  // update browser url field
  var newurl=window.location.pathname + '?release=' + release + '&expname=' + expname + '&ccd=' + ccd;
  window.history.replaceState(null, "Title", newurl);
  $('#share-url').val('http://' + window.location.host + newurl);

  // after both image and mask are drawn: remove loading spinner
  $('#loading').hide();
  $('#wicked-science-visualization').find('canvas').fadeTo(200, 1);
}

function setNextImage(response) {
  if (response.error === undefined) { 
    console.log('creating astro.FITS.File: '+response.name);
    var f = new astro.FITS.File(response.name, getImage, response);
  }
  else {
    $('#message_header').html(response.error);
    $('#message_text').html(response.message);
    $('#message_details').html(response.description);
    $('#message-modal').modal('show');
    $('#loading').hide();
  }
}

function userClass(uc) {
  // frequent users: color badge acording to # of focal planes done
  // http://getbootstrap.com/2.3.2/components.html#labels-badges
  // See common.php.inc for number of images per level
  switch (uc) {
    case 1: return {class: 1, style: 'badge-success', title: 'Rookie'}; break;
    case 2: return {class: 2, style: 'badge-warning', title: 'Novice'}; break;
    case 3: return {class: 3, style: 'badge-important', title: 'Frequent Checker'}; break;
    case 4: return {class: 4, style: 'badge-info', title: 'Veteran'}; break;
    case 5: return {class: 5, style: 'badge-inverse', title: 'Chief Inspector'}; break;
    // Should do default badge (silver)
    case 6: return {class: 6, style: '', title: 'Inspector General'}; break;
    case 7: return {class: 7, style: '', title: 'Night Inspector'}; break;
    case 8: return {class: 8, style: '', title: 'Season Inspector'}; break;
    default: return {class: 0}; break;
  }
}

function showCongrats(congrats) {
  $('#congrats_text').html(congrats.text);
  if (congrats.detail !== undefined) {
    $('#congrats_details').html(congrats.detail);
    if (congrats.userclass !== undefined) {
      var uc = userClass(congrats.userclass);
      $('#status_class').addClass(uc.style);
      $('#status_class').html(uc.title);
      $('#userrank').removeClass();
      $('#userrank').addClass("badge");
      $('#userrank').addClass(uc.style); // set the badge color
    }
  }
  else
    $('#congrats_details').html();
  $('#congrats-modal').modal('show');
}

function clearUI() {
  $('#mark-buttons').hide();
  $('#clear-button').hide();
  $('#problem-text').val('');
  $('#problem-name').html(problem_default);
  if (marks.length)
    clearMarks();
  if (has_reported_problems) {
    clearMarks(webfits.reportCtx);
    has_reported_problems = false;
  }
  problem = null;
}

function sendResponse(image_props) {
  //console.debug('sendResponse');
  if (image_props === undefined)
    image_props = {'release': release};
  image_props['fileid'] = fileid;
  image_props['problems'] = marks;
  getNextImage(image_props);
  
  // update image counters
  if (checkSessionCookie()) {
    var number = parseInt($('#total-files').html());
    number += 1;
    $('#total-files').html(number);
  }
}

function getNextImage(image_props) {
  //console.debug('getNextImage');
  // show spinner
  $('#loading').show();
  $('#wicked-science-visualization').find('canvas').fadeTo(400, 0.05);

  // send to DB
  var params = {'release': release};
  if (image_props !== undefined) {
    for (var attr in image_props)
      params[attr] = image_props[attr];
  }
  //console.debug('params',params);
  $.post('db.php', params,
    function(response) {
      if (response.congrats !== undefined) {
        showCongrats(response.congrats);
      }
      setNextImage(response);
    }, 'json')
    .fail(function(jqXHR, status) {
      console.log('failure: ',status);
      console.log(jqXHR);
      alert('Failure when saving response');
  });
  clearUI();
}

function getMyData() {
  $.get('mydata.php', {'release': release}, function(response) {
    // initial call: create typeahead
    if ($('#total_files').html() == "")
      $('#problem-text').typeahead({source: response.problems});
    else // just update array afterwards
      $('#problem-text').typeahead().data('typeahead').source = response.problems;
    
    $('#username').html(response.username);
    $('.userrank').html("#"+response.rank);
    var uc = userClass(response.userclass);
    if (uc.class > 0)
      $('.badge').addClass(uc.style);
    $('#total-files').html(response.total_files);
    $('#flagged-files').html(response.flagged_files);
    $('#user-menu').removeClass('hide');
    
    var rankDetails = "";
    if (uc.class > 0) 
      rankDetails += "You have the rank of <span class='badge " + uc.style + "'>" + uc.title + "</span>.<br />";
    if (uc.class < 5) {
      var next_uc = userClass(uc.class + 1);
      rankDetails += "You need another <strong>" + response.missingfiles + "</strong> images to reach the rank of <span class='badge " + next_uc.style + "'>" + next_uc.title + "</span>.";
    }
    $('#user_rank_details').html(rankDetails);

  }, 'json');
}

function getLeaderboard() {
  $.get('ranking.php', {'release': release}, function(response) {
    var html = "<table class='table table-condensed table-striped'><thead><tr><th>Rank</th><th>Username</th><th>Problematic/Total</th><th># Files</th></tr></thead><tbody>";
    var total = null, counter = 1, width_flagged, width_total;
    var username = $('#username').html();
    for (var i=0; i < response.length; i++) {
      if (total == null)
        total = response[i]['total_files'];
      width_flagged = (100*response[i]['flagged_files']/total) + "%";
      width_total = (100*(response[i]['total_files']-response[i]['flagged_files'])/total) + "%";
      html += "<tr><td># "+ counter +"</td><td><span class='namecol'>" + uid2username(response[i]['userid']) + "</span></td>";
      html += "<td><div class='ratingcol'><span class='ratingbar bad' style='width:" + width_flagged +"'></span>";
      html += "<span class='ratingbar good' style='left:" + width_flagged +"; width:" + width_total +"'></span></div></td>";
      html += "<td>" + response[i]['total_files'] + "</td></tr>";
      // get rank update if the username matches
      if (response[i]['username'] == username)
	$('.userrank').html("#"+counter);
      counter++ ;
    }
    html += "</tbody></table>";
    $('#leaderboard').html(html);
    $('#rank-modal').find('[class*="modal-body"]').html(html);
  }, 'json');
}

function closeProblemModal() {
  $('#problem-modal').modal('hide');
  $('#problem-name').html(problem_default);
  problem = null;
}

function setDECamChipLayout() {
  var WIDTH = 530., HEIGHT = 479.;
  var GAP = [1.25, 2.];
  var PAD = [14., 12.];
  var ROWS = [[3,2,1], // chips per row
              [7,6,5,4], 
              [12,11,10,9,8], 
              [18,17,16,15,14,13],
              [24,23,22,21,20,19],
              [31,30,29,28,27,26,25],
              [38,37,36,35,34,33,32],
              [44,43,42,41,40,39],
              [50,49,48,47,46,45],
              [55,54,53,52,51],
              [59,58,57,56],
              [62,61,60]];
  var NROWS = ROWS.length;
  var NCCDS = [3, 4, 5, 6, 6, 7, 7, 6, 6, 5, 4, 3];
  var i, j, xpad, ypad;
  if (release == "SVA1") {
    HEIGHT = 454.;
    GAP = [0.5,0.5];
    PAD = [1.,0.];
    ROWS.reverse();
    for (i = 0; i < NROWS; i++)
      ROWS[i].reverse();
  }
  var CCD_SIZE = [(WIDTH-6*GAP[0]-2*PAD[0])/7, (HEIGHT-11*GAP[1]-2*PAD[1])/NROWS];
  
  var html = "<style> .ccdshape { width: " + Math.round(CCD_SIZE[0]-2) + "px; height: " + Math.round(CCD_SIZE[1]-2) + "px; }</style>";
  var xmin, ymax;
  for (i=0; i < NROWS; i++) {
    var ccds = ROWS[i];
    for (j=0; j < ccds.length; j++) {
      xmin = Math.round(PAD[0] + j*(GAP[0] + CCD_SIZE[0]) + (WIDTH - 2*PAD[0] - ccds.length*(CCD_SIZE[0]+GAP[0]))/2);
      ymax = Math.round((PAD[1] + i*(GAP[1] + CCD_SIZE[1])));
      html += "<div class='ccdshape' style='left:" + xmin + "px; top:" + ymax + "px' title='CCD " + ccds[j] + "'></div>";
    }
  }
  $('#ccdmap').html(html);
  // Connect the ccd outline in FoV image to image loading
  $('#ccdmap').children('.ccdshape').on('click', function(evt) {
    var ccdnum = evt.target.title.split(" ").pop();
    var new_image = {'release': release, 'expname': expname, 'ccd': ccdnum};
    if (marks.length)
      sendResponse(new_image);
    else
      getNextImage(new_image);
    $('#fov-modal').modal('hide');
  });
}


function setLSSTChipLayout() {
  var WIDTH = 530., HEIGHT = 530.;
  var GAP = [1., 1.]; // Gaps between CCDs
  var PAD = [3.5, 3.5]; // Gaps at the edge of the FoV

  /*
  // LSST raft/sensor layout from here:
  // https://confluence.lsstcorp.org/display/LSWUG/Representation+of+a+Camera
  // Note: The FoV image is y-axis inverted compared to the above link
  // Note: This is only valid for eimages, and will hopefully be updated.
  var ROWS = [// chips per row
      // First row of rafts
      ['14-02-A','14-12-A','14-22-A', '24-02-A','24-12-A','24-22-A', '34-02-A','34-12-A','34-22-A' ], 
      ['14-02-B','14-12-B','14-22-B', '24-02-B','24-12-B','24-22-B', '34-02-B','34-12-B','34-22-B' ], 
      ['14-01-A','14-11-A','14-21-A', '24-01-A','24-11-A','24-21-A', '34-01-A','34-11-A','34-21-A' ], 
      ['14-01-B','14-11-B','14-21-B', '24-01-B','24-11-B','24-21-B', '34-01-B','34-11-B','34-21-B' ], 
      ['14-00-A','14-10-A','14-20-A', '24-00-A','24-10-A','24-20-A', '34-00-A','34-10-A','34-20-A' ], 
      ['14-00-B','14-10-B','14-20-B', '24-00-B','24-10-B','24-20-B', '34-00-B','34-10-B','34-20-B' ], 
      // Last row of rafts
      ['03-02-A','03-12-A','03-22-A', '13-02-A','13-12-A','13-22-A', '23-02-A','23-12-A','23-22-A', '33-02-A','33-12-A','33-22-A', '43-02-A','43-12-A','43-22-A' ], 
      ['03-02-B','03-12-B','03-22-B', '13-02-B','13-12-B','13-22-B', '23-02-B','23-12-B','23-22-B', '33-02-B','33-12-B','33-22-B', '43-02-B','43-12-B','43-22-B' ], 
      ['03-01-A','03-11-A','03-21-A', '13-01-A','13-11-A','13-21-A', '23-01-A','23-11-A','23-21-A', '33-01-A','33-11-A','33-21-A', '43-01-A','43-11-A','43-21-A' ], 
      ['03-01-B','03-11-B','03-21-B', '13-01-B','13-11-B','13-21-B', '23-01-B','23-11-B','23-21-B', '33-01-B','33-11-B','33-21-B', '43-01-B','43-11-B','43-21-B' ], 
      ['03-00-A','03-10-A','03-20-A', '13-00-A','13-10-A','13-20-A', '23-00-A','23-10-A','23-20-A', '33-00-A','33-10-A','33-20-A', '43-00-A','43-10-A','43-20-A' ], 
      ['03-00-B','03-10-B','03-20-B', '13-00-B','13-10-B','13-20-B', '23-00-B','23-10-B','23-20-B', '33-00-B','33-10-B','33-20-B', '43-00-B','43-10-B','43-20-B' ], 
      // Fourth row of rafts
      ['02-02-A','02-12-A','02-22-A', '12-02-A','12-12-A','12-22-A', '22-02-A','22-12-A','22-22-A', '32-02-A','32-12-A','32-22-A', '42-02-A','42-12-A','42-22-A' ], 
      ['02-02-B','02-12-B','02-22-B', '12-02-B','12-12-B','12-22-B', '22-02-B','22-12-B','22-22-B', '32-02-B','32-12-B','32-22-B', '42-02-B','42-12-B','42-22-B' ], 
      ['02-01-A','02-11-A','02-21-A', '12-01-A','12-11-A','12-21-A', '22-01-A','22-11-A','22-21-A', '32-01-A','32-11-A','32-21-A', '42-01-A','42-11-A','42-21-A' ], 
      ['02-01-B','02-11-B','02-21-B', '12-01-B','12-11-B','12-21-B', '22-01-B','22-11-B','22-21-B', '32-01-B','32-11-B','32-21-B', '42-01-B','42-11-B','42-21-B' ], 
      ['02-00-A','02-10-A','02-20-A', '12-00-A','12-10-A','12-20-A', '22-00-A','22-10-A','22-20-A', '32-00-A','32-10-A','32-20-A', '42-00-A','42-10-A','42-20-A' ], 
      ['02-00-B','02-10-B','02-20-B', '12-00-B','12-10-B','12-20-B', '22-00-B','22-10-B','22-20-B', '32-00-B','32-10-B','32-20-B', '42-00-B','42-10-B','42-20-B' ], 
      // Third row of rafts
      ['01-02-A','01-12-A','01-22-A', '11-02-A','11-12-A','11-22-A', '21-02-A','21-12-A','21-22-A', '31-02-A','31-12-A','31-22-A', '41-02-A','41-12-A','41-22-A' ], 
      ['01-02-B','01-12-B','01-22-B', '11-02-B','11-12-B','11-22-B', '21-02-B','21-12-B','21-22-B', '31-02-B','31-12-B','31-22-B', '41-02-B','41-12-B','41-22-B' ], 
      ['01-01-A','01-11-A','01-21-A', '11-01-A','11-11-A','11-21-A', '21-01-A','21-11-A','21-21-A', '31-01-A','31-11-A','31-21-A', '41-01-A','41-11-A','41-21-A' ], 
      ['01-01-B','01-11-B','01-21-B', '11-01-B','11-11-B','11-21-B', '21-01-B','21-11-B','21-21-B', '31-01-B','31-11-B','31-21-B', '41-01-B','41-11-B','41-21-B' ], 
      ['01-00-A','01-10-A','01-20-A', '11-00-A','11-10-A','11-20-A', '21-00-A','21-10-A','21-20-A', '31-00-A','31-10-A','31-20-A', '41-00-A','41-10-A','41-20-A' ], 
      ['01-00-B','01-10-B','01-20-B', '11-00-B','11-10-B','11-20-B', '21-00-B','21-10-B','21-20-B', '31-00-B','31-10-B','31-20-B', '41-00-B','41-10-B','41-20-B' ], 
      // Second row of rafts
      ['10-02-A','10-12-A','10-22-A', '20-02-A','20-12-A','20-22-A', '30-02-A','30-12-A','30-22-A' ], 
      ['10-02-B','10-12-B','10-22-B', '20-02-B','20-12-B','20-22-B', '30-02-B','30-12-B','30-22-B' ], 
      ['10-01-A','10-11-A','10-21-A', '20-01-A','20-11-A','20-21-A', '30-01-A','30-11-A','30-21-A' ], 
      ['10-01-B','10-11-B','10-21-B', '20-01-B','20-11-B','20-21-B', '30-01-B','30-11-B','30-21-B' ], 
      ['10-00-A','10-10-A','10-20-A', '20-00-A','20-10-A','20-20-A', '30-00-A','30-10-A','30-20-A' ], 
      ['10-00-B','10-10-B','10-20-B', '20-00-B','20-10-B','20-20-B', '30-00-B','30-10-B','30-20-B' ], 
  ];
  */

  // This is the focal plane layout for calexps generated with:
  // import lsst.afw.cameraGeom.utils as cgUtils
  // camera = butler.get('camera')
  // cgUtils.plotFocalPlane(camera)
  // It should match this image from rhl:
  // https://lsstc.slack.com/archives/C932BQ550/p1534428357000100
  var ROWS = [// chips per row
      // First row of rafts
      ['41-20-A','41-21-A','41-22-A', '42-20-A','42-21-A','42-22-A', '43-20-A','43-21-A','43-22-A' ], 
      ['41-20-B','41-21-B','41-22-B', '42-20-B','42-21-B','42-22-B', '43-20-B','43-21-B','43-22-B' ], 
      ['41-10-A','41-11-A','41-12-A', '42-10-A','42-11-A','42-12-A', '43-10-A','43-11-A','43-12-A' ], 
      ['41-10-B','41-11-B','41-12-B', '42-10-B','42-11-B','42-12-B', '43-10-B','43-11-B','43-12-B' ], 
      ['41-00-A','41-01-A','41-02-A', '42-00-A','42-01-A','42-02-A', '43-00-A','43-01-A','43-02-A' ], 
      ['41-00-B','41-01-B','41-02-B', '42-00-B','42-01-B','42-02-B', '43-00-B','43-01-B','43-02-B' ], 
      // Last row of rafts
      ['30-20-A','30-21-A','30-22-A', '31-20-A','31-21-A','31-22-A', '32-20-A','32-21-A','32-22-A', '33-20-A','33-21-A','33-22-A', '34-20-A','34-21-A','34-22-A' ], 
      ['30-20-B','30-21-B','30-22-B', '31-20-B','31-21-B','31-22-B', '32-20-B','32-21-B','32-22-B', '33-20-B','33-21-B','33-22-B', '34-20-B','34-21-B','34-22-B' ], 
      ['30-10-A','30-11-A','30-12-A', '31-10-A','31-11-A','31-12-A', '32-10-A','32-11-A','32-12-A', '33-10-A','33-11-A','33-12-A', '34-10-A','34-11-A','34-12-A' ], 
      ['30-10-B','30-11-B','30-12-B', '31-10-B','31-11-B','31-12-B', '32-10-B','32-11-B','32-12-B', '33-10-B','33-11-B','33-12-B', '34-10-B','34-11-B','34-12-B' ], 
      ['30-00-A','30-01-A','30-02-A', '31-00-A','31-01-A','31-02-A', '32-00-A','32-01-A','32-02-A', '33-00-A','33-01-A','33-02-A', '34-00-A','34-01-A','34-02-A' ], 
      ['30-00-B','30-01-B','30-02-B', '31-00-B','31-01-B','31-02-B', '32-00-B','32-01-B','32-02-B', '33-00-B','33-01-B','33-02-B', '34-00-B','34-01-B','34-02-B' ], 
      // Fourth row of rafts
      ['20-20-A','20-21-A','20-22-A', '21-20-A','21-21-A','21-22-A', '22-20-A','22-21-A','22-22-A', '23-20-A','23-21-A','23-22-A', '24-20-A','24-21-A','24-22-A' ], 
      ['20-20-B','20-21-B','20-22-B', '21-20-B','21-21-B','21-22-B', '22-20-B','22-21-B','22-22-B', '23-20-B','23-21-B','23-22-B', '24-20-B','24-21-B','24-22-B' ], 
      ['20-10-A','20-11-A','20-12-A', '21-10-A','21-11-A','21-12-A', '22-10-A','22-11-A','22-12-A', '23-10-A','23-11-A','23-12-A', '24-10-A','24-11-A','24-12-A' ], 
      ['20-10-B','20-11-B','20-12-B', '21-10-B','21-11-B','21-12-B', '22-10-B','22-11-B','22-12-B', '23-10-B','23-11-B','23-12-B', '24-10-B','24-11-B','24-12-B' ], 
      ['20-00-A','20-01-A','20-02-A', '21-00-A','21-01-A','21-02-A', '22-00-A','22-01-A','22-02-A', '23-00-A','23-01-A','23-02-A', '24-00-A','24-01-A','24-02-A' ], 
      ['20-00-B','20-01-B','20-02-B', '21-00-B','21-01-B','21-02-B', '22-00-B','22-01-B','22-02-B', '23-00-B','23-01-B','23-02-B', '24-00-B','24-01-B','24-02-B' ], 
      // Third row of rafts
      ['10-20-A','10-21-A','10-22-A', '11-20-A','11-21-A','11-22-A', '12-20-A','12-21-A','12-22-A', '13-20-A','13-21-A','13-22-A', '14-20-A','14-21-A','14-22-A' ], 
      ['10-20-B','10-21-B','10-22-B', '11-20-B','11-21-B','11-22-B', '12-20-B','12-21-B','12-22-B', '13-20-B','13-21-B','13-22-B', '14-20-B','14-21-B','14-22-B' ], 
      ['10-10-A','10-11-A','10-12-A', '11-10-A','11-11-A','11-12-A', '12-10-A','12-11-A','12-12-A', '13-10-A','13-11-A','13-12-A', '14-10-A','14-11-A','14-12-A' ], 
      ['10-10-B','10-11-B','10-12-B', '11-10-B','11-11-B','11-12-B', '12-10-B','12-11-B','12-12-B', '13-10-B','13-11-B','13-12-B', '14-10-B','14-11-B','14-12-B' ], 
      ['10-00-A','10-01-A','10-02-A', '11-00-A','11-01-A','11-02-A', '12-00-A','12-01-A','12-02-A', '13-00-A','13-01-A','13-02-A', '14-00-A','14-01-A','14-02-A' ], 
      ['10-00-B','10-01-B','10-02-B', '11-00-B','11-01-B','11-02-B', '12-00-B','12-01-B','12-02-B', '13-00-B','13-01-B','13-02-B', '14-00-B','14-01-B','14-02-B' ], 
      // Second row of rafts
      ['01-20-A','01-21-A','01-22-A', '02-20-A','02-21-A','02-22-A', '03-20-A','03-21-A','03-22-A' ], 
      ['01-20-B','01-21-B','01-22-B', '02-20-B','02-21-B','02-22-B', '03-20-B','03-21-B','03-22-B' ], 
      ['01-10-A','01-11-A','01-12-A', '02-10-A','02-11-A','02-12-A', '03-10-A','03-11-A','03-12-A' ], 
      ['01-10-B','01-11-B','01-12-B', '02-10-B','02-11-B','02-12-B', '03-10-B','03-11-B','03-12-B' ], 
      ['01-00-A','01-01-A','01-02-A', '02-00-A','02-01-A','02-02-A', '03-00-A','03-01-A','03-02-A' ], 
      ['01-00-B','01-01-B','01-02-B', '02-00-B','02-01-B','02-02-B', '03-00-B','03-01-B','03-02-B' ], 
  ];

  var NROWS = ROWS.length;
  var MAXCCDS = 15; // Maximum number of CCDs in any row
  var i, j, xpad, ypad;
  var CCD_SIZE = [(WIDTH-MAXCCDS*GAP[0]-2*PAD[0])/MAXCCDS, (HEIGHT-NROWS*GAP[1]-2*PAD[1])/NROWS];
  
  var html = "<style> .ccdshape { width: " + Math.round(CCD_SIZE[0]-2) + "px; height: " + Math.round(CCD_SIZE[1]-2) + "px; }</style>";
  var xmin, ymax;
  for (i=0; i < NROWS; i++) {
    var ccds = ROWS[i];
    for (j=0; j < ccds.length; j++) {
      xmin = Math.round(PAD[0] + j*(GAP[0] + CCD_SIZE[0]) + (WIDTH - 2*PAD[0] - ccds.length*(CCD_SIZE[0]+GAP[0]))/2);
      ymax = Math.round((PAD[1] + i*(GAP[1] + CCD_SIZE[1])));
      html += "<div class='ccdshape' style='left:" + xmin + "px; top:" + ymax + "px' title='CCD " + ccds[j] + "'></div>";
    }
  }
  $('#ccdmap').html(html);
  // Connect the ccd outline in FoV image to image loading
  $('#ccdmap').children('.ccdshape').on('click', function(evt) {
    var ccdnum = evt.target.title.split(" ").pop();
    var new_image = {'release': release, 'expname': expname, 'ccd': ccdnum};
    if (marks.length)
      sendResponse(new_image);
    else
      getNextImage(new_image);
    $('#fov-modal').modal('hide');
  });
}

function setChipLayout() {
    setLSSTChipLayout();
}
