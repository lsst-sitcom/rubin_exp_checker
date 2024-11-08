var release = null;

function setRelease(release_, attach_listener) {
  console.debug("setRelease");
  if (release_ != null) {
    // check if release is still present in the list
    var found = false;
    $('#release-switch').find('.release-button').each(function() {
      if (release_ == this.id.split("-").pop()) {
	found = true;
      }
    });
    if (found)
      release = release_;
    else
      release = null;
  }
  
  if (release == null) {
    var node = $('#release-switch').find('.release-button').last()[0];
    release = node.id.split("-").pop();
  }

  $.cookie('default-release', release, {expires: 365});
  $('.release_name').html(release);
  if (attach_listener === undefined) {
    $('a[class*="release-button"]').on('click', function(evt) {
      setRelease(this.id.split("-").pop());
      window.location.reload(true);
    });
  }
}

function checkSessionCookie() {
  console.debug("checkSessionCookie");
  var auth = false;
  $.ajax({
    type: "GET",
    url: "/auth",
    async: false,
    success: res => { auth = $.parseJSON(res)["auth"]; }
  });
  console.debug("authorized: " + auth);
  return auth;
}

function uid2username(uid) {
  // This should match code in common.py
  var arr = [];
  while (uid > 0){
      arr.push(uid % 49 + 47);
      uid = Math.floor(uid / 49);
  }
  return String.fromCharCode.apply(null, arr).toLowerCase();
}

