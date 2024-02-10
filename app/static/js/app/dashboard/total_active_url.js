google.charts.setOnLoadCallback(drawChart);

function drawChart() {
    var data = google.visualization.arrayToDataTable([
        ['Task', 'Hours per Day'],
        ...totalActiveUrl
    ]);

    var options = {
        pieHole: 0.4,
    };

    var chart = new google.visualization.PieChart(document.getElementById('total-active-url-chart'));
    chart.draw(data, options);
}