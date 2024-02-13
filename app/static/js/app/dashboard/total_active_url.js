function drawTotalActiveUrlChart() {
    var data = google.visualization.arrayToDataTable(totalActiveUrl);
    var options = {pieHole: 0.3};
    var chart = new google.visualization.PieChart(document.getElementById('total-active-url-chart'));

    chart.draw(data, options);
}

google.charts.setOnLoadCallback(drawTotalActiveUrlChart);
