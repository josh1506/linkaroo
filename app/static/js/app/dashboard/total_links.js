function drawTotalLinksChart() {
    var data = google.visualization.arrayToDataTable(latestTotalClicks);
    var options = {curveType: 'function', legend: { position: 'bottom' }};
    var chart = new google.visualization.LineChart(document.getElementById('total_links_chart'));

    chart.draw(data, options);
}

google.charts.setOnLoadCallback(drawTotalLinksChart);
