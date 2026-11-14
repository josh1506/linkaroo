google.charts.setOnLoadCallback(drawTotalClicksChart);

function drawTotalClicksChart() {
    if (!document.getElementById('chart_div')) return;  // empty state rendered instead
    var data = google.visualization.arrayToDataTable(totalClicks);

    var options = {
        hAxis: {title: 'Date',  titleTextStyle: {color: '#333'}},
        vAxis: {minValue: 0}
    };

    var chart = new google.visualization.AreaChart(document.getElementById('chart_div'));
    chart.draw(data, options);
}
