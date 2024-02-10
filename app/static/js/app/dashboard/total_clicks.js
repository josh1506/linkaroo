google.charts.setOnLoadCallback(drawTotalClicksChart);

function drawTotalClicksChart() {
    var data = google.visualization.arrayToDataTable([
        ['Year', 'Sales', 'Expenses', 'Sample'],
        ...totalClicks.recent_7_days_created
    ]);

    var options = {
        // title: 'Company Performance',
        hAxis: {title: 'Year',  titleTextStyle: {color: '#333'}},
        vAxis: {minValue: 0}
    };

    var chart = new google.visualization.AreaChart(document.getElementById('chart_div'));
    chart.draw(data, options);
}
