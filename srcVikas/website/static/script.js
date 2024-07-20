$(document).ready(function () {

  
  $("#uploadBtn").on("click", function (event) {
    event.preventDefault();
    var formData = new FormData(document.getElementById("uploadForm"));
    $("#metrics").attr("src", "");
    $("#yoloOutput").attr("src", "");
    $("#motionOutput").attr("src", "");

    $.ajax({
      url: "/upload",
      type: "POST",
      data: formData,
      contentType: false,
      processData: false,
      success: function (response) {
        if (response.error) {
          $("#output").html("<p>Error: " + response.error + "</p>");
        } else {
          $("#output").html(
            "<p>Video uploaded successfully. Processing...</p>"
          );
        }
      },
      error: function () {
        $("#output").html("<p>Error uploading video. Please try again.</p>");
      },
    });
  });

  var socket = io.connect();
  
  $("#stopBtn").on("click", function (event) {
    event.preventDefault();
    socket.emit("stop_stream");
  });


  socket.on("yolo_frame", function (data) {
    document.getElementById("yoloOutput").src = "data:image/jpg;base64," + data;
  });

  socket.on("motion_frame", function (data) {
    document.getElementById("motionOutput").src =
      "data:image/jpg;base64," + data;
  });

  socket.on("metrics", function (data) {
    $("#metrics").attr(
      "src",
      "http://localhost:5000/static/uploads/metrics.png"
    );
    $("#output").html("<p>Processing complete. Metrics generated.</p>");
  });
});
