$(document).ready(function () {
  window.sortTable = function (columnIndex) {
    var table = document.getElementById("modelTable");
    var rows = Array.from(table.rows).slice(1);
    var sortedRows = rows.sort((a, b) => {
      var cellA = parseFloat(a.cells[columnIndex].innerText) || 0;
      var cellB = parseFloat(b.cells[columnIndex].innerText) || 0;
      return cellA - cellB;
    });
    sortedRows.forEach((row) => table.appendChild(row));
  };

  $.getJSON(modelDataUrl, function (data) {
    var tableBody = $("#modelTable tbody");
    data.forEach(function (item) {
      var row =
        "<tr>" +
        "<td>" +
        item.model +
        "</td>" +
        "<td>" +
        item.precision +
        "</td>" +
        "<td>" +
        item.recall +
        "</td>" +
        "<td>" +
        item.map50 +
        "</td>" +
        "<td>" +
        item.map50_95 +
        "</td>" +
        "<td>" +
        item.iou +
        "</td>" +
        "<td>" +
        item.epochs +
        "</td>" +
        "</tr>";
      tableBody.append(row);
    });
  });

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
      },
      error: function () {
        $("#videoFrames").html(
          "<p>Error uploading video. Please try again.</p>"
        );
      },
    });
  });

  var socket = io.connect();

  $("#stopBtn").on("click", function (event) {
    event.preventDefault();
    socket.emit("stop_processing");
  });

  socket.on("stable_update", function (data) {
    $("#stableFrames").attr("src", "data:image/png;base64," + data);
  });

  socket.on("metrics", function (data) {
    $("#metrics").attr(
      "src",
      "http://localhost:5000/static/uploads/metrics.png"
    );
    $("#output").html("<p>Processing complete. Metrics generated.</p>");
  });
});
