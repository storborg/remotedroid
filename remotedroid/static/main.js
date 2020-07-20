console.log("hello remotedroid");

var screenshotWs = new WebSocket("ws://localhost:8080/ws/screenshots");
var controlWs = new WebSocket("ws://localhost:8080/ws/control");
var img = document.querySelector("img");

screenshotWs.addEventListener("open", function(event) {
  console.log("connected");
});

screenshotWs.addEventListener("message", function(msg) {
  var blob = msg.data.slice(0, msg.data.size, "image/png");
  var url = URL.createObjectURL(blob);
  img.src = url;
});

img.addEventListener("click", function(event) {
  var x = (event.offsetX / img.width) * img.naturalWidth;
  var y = (event.offsetY / img.height) * img.naturalHeight;
  console.log("got a click on the image", x, y);
  controlWs.send(JSON.stringify({
    type: "tap",
    x: x,
    y: y,
  }));
});
