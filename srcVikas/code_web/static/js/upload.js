$(document).ready(function () {
  $("#uploadBtn").on("click", function (event) {
    event.preventDefault();
    var formData = new FormData(document.getElementById("uploadForm"));

    $("stableFrames").attr("src", "");

    $.ajax({
      url: "/upload",
      type: "POST",
      data: formData,
      contentType: false,
      processData: false,
      success: function (response) {
        if (response.error) {
          $("#videoFrames").html("<p>Error: " + response.error + "</p>");
        } else {
          $("#videoFrames").html("<p>" + response.result + "</p>");
        }

        // Is there any better way of refreshing the socket connection!
        setTimeout(function () {
          location.reload();
        }, 2000);
      },
      error: function () {
        $("#videoFrames").html(
          "<p>Error uploading video. Please try again.</p>"
        );

        // Is there any better way of refreshing the socket connection!
        setTimeout(function () {
          location.reload();
        }, 2000);
      },
    });
  });

  var socket = io.connect();

  $("#stopBtn").on("click", function (event) {
    event.preventDefault();
    socket.emit("stop_processing");

    // Is there any better way of refreshing the socket connection!
    setTimeout(function () {
      location.reload();
    }, 2000);
  });

  socket.on("stable_update", function (data) {
    $("#stableFrames").attr("src", "data:image/png;base64," + data);
  });

  socket.on("yolo_update", function (data) {
    $("#yoloFrames").attr("src", "data:image/png;base64," + data);
  });

  socket.on("metrics", function (data) {
    $("#metrics").attr(
      "src",
      "http://localhost:5000/static/uploads/metrics.png"
    );
    $("#output").html("<p>Processing complete. Metrics generated.</p>");
  });
});
