google.charts.setOnLoadCallback(drawTotalLinksChart);

function drawTotalLinksChart() {
    var data = google.visualization.arrayToDataTable([
        ['Year', 'Sales', 'Expenses'],
        ...latestTotalClicks
    ]);

    var options = {
        // title: 'Company Performance',
        curveType: 'function',
        legend: { position: 'bottom' }
    };

    var chart = new google.visualization.LineChart(document.getElementById('total_links_chart'));

    chart.draw(data, options);
}
