function drawLatestClicksChart() {
    var data = google.visualization.arrayToDataTable(latestTotalClicks);
    var options = {curveType: 'function', legend: { position: 'bottom' }};
    var chart = new google.visualization.LineChart(document.getElementById('latest_total_clicks_chart'));

    chart.draw(data, options);
}

google.charts.setOnLoadCallback(drawLatestClicksChart);
