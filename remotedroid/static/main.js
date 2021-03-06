console.log("hello remotedroid");

function qualifyWebSocketURL(path) {
  url = new URL(window.location.href);
  var protocol;
  if (url.protocol === "http:") {
    protocol = "ws:";
  } else {
    protocol = "wss:";
  }

  var apiBase = protocol + "//" + url.host + url.pathname;
  return new String(new URL(path, apiBase));
}

var screenshotWs = new WebSocket(qualifyWebSocketURL("/ws/screenshots"));
var controlWs = new WebSocket(qualifyWebSocketURL("/ws/control"));
var img = document.querySelector("img");
var body = document.body;

screenshotWs.addEventListener("open", function(event) {
  console.log("connected");
});

screenshotWs.addEventListener("message", function(msg) {
  var blob = msg.data.slice(0, msg.data.size, "image/jpeg");
  var url = URL.createObjectURL(blob);
  img.src = url;
});

function scaleX(offsetX) {
  return Math.round((offsetX / img.width) * 1440);
}

function scaleY(offsetY) {
  return Math.round((offsetY / img.height) * 2960);
}

window.lastMouseDownOffsetX = null;
window.lastMouseDownOffsetY = null;
window.lastMouseDownTime = null;

img.addEventListener("mousedown", function(event) {
  window.lastMouseDownOffsetX = event.offsetX;
  window.lastMouseDownOffsetY = event.offsetY;
  window.lastMouseDownTime = new Date().getTime();
});

body.addEventListener("mouseup", function(event) {
  window.lastMouseDownOffsetX = null;
  window.lastMouseDownOffsetY = null;
  window.lastMouseDownTime = null;
});

var swipeThreshold = 2;

img.addEventListener("mouseup", function(event) {
  if (window.lastMouseDownTime === null) {
    return;
  }
  var elapsed = new Date().getTime() - window.lastMouseDownTime;
  var x1 = scaleX(window.lastMouseDownOffsetX);
  var y1 = scaleY(window.lastMouseDownOffsetY);
  var x2 = scaleX(event.offsetX);
  var y2 = scaleY(event.offsetY);

  window.lastMouseDownOffsetX = null;
  window.lastMouseDownOffsetY = null;
  window.lastMouseDownTime = null;

  var moveX = Math.abs(x2 - x1);
  var moveY = Math.abs(y2 - y1);
  console.log("mouse " + x1 + " -> " + x2 + ", " + y1 + " -> " + y2);

  var msg = {};
  if ((moveX > swipeThreshold) || (moveY > swipeThreshold)) {
    console.log("swipe duration " + elapsed);
    msg.type = "swipe";
    msg.x1 = x1;
    msg.y1 = y1;
    msg.x2 = x2;
    msg.y2 = y2;
    msg.duration = elapsed;
  } else {
    console.log("tap");
    msg.type = "tap";
    msg.x = x2;
    msg.y = y2;
  }
  controlWs.send(JSON.stringify(msg));
});

document.querySelector(".btn-unlock").addEventListener("click", function(event) {
  console.log("unlock");
  controlWs.send(JSON.stringify({"type": "unlock"}));
});
