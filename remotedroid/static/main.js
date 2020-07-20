console.log("hello remotedroid");

var screenshotWs = new WebSocket("ws://localhost:8080/ws/screenshots");
var controlWs = new WebSocket("ws://localhost:8080/ws/control");
var img = document.querySelector("img");

screenshotWs.addEventListener("open", function(event) {
  console.log("connected");
});

screenshotWs.addEventListener("message", function(msg) {
  console.log("got from server: ", msg.data);
  var blob = msg.data.slice(0, msg.data.size, "image/png");
  var url = URL.createObjectURL(blob);
  console.log("url: ", url);
  img.src = url;
  console.log("done");
});
