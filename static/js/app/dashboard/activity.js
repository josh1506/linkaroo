// Click activity (30-day trend, weekday and hour patterns) and enabled/disabled links. Data from init.js.
function drawActivityCharts() {
    const draw = (id, rows, Chart, options) => {
        const el = document.getElementById(id);
        if (!el) return;  // empty state rendered instead
        new Chart(el).draw(google.visualization.arrayToDataTable(rows), options);
    };
    const bars = {legend: {position: 'none'}, vAxis: {minValue: 0, format: '0'}};

    draw('clicks-per-day-chart', activity.per_day, google.visualization.LineChart, bars);
    draw('clicks-by-weekday-chart', activity.per_weekday, google.visualization.ColumnChart, bars);
    draw('clicks-by-hour-chart', activity.per_hour, google.visualization.ColumnChart, {...bars, hAxis: {showTextEvery: 3}});
    draw('enabled-disabled-chart', enabledDisabled, google.visualization.PieChart, {pieHole: 0.3});
}

google.charts.setOnLoadCallback(drawActivityCharts);
