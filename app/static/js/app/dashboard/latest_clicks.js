google.charts.setOnLoadCallback(drawChart3);

function drawChart3() {
    var data = google.visualization.arrayToDataTable([['Dinosaur', 'Length'], ...totalLinksData.recent_7_days_created]);

    var options = {
    // title: 'Lengths of dinosaurs, in meters',
    legend: { position: 'none' },
    };

    var chart = new google.visualization.Histogram(document.getElementById('chart_div1'));
    chart.draw(data, options);
}
