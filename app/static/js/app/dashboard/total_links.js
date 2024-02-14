function drawTotalLinksChart() {
    var data = google.visualization.arrayToDataTable([
        ["Year", "Count", { role: "style" } ],
        ...totalLinksData
    ]);

    var view = new google.visualization.DataView(data);
    view.setColumns([0, 1,
        {
            calc: "stringify",
            sourceColumn: 1,
            type: "string",
            role: "annotation"
        }, 2
    ]);

    var options = {bar: {groupWidth: "90%"}, legend: { position: "none" }};
    var chart = new google.visualization.ColumnChart(document.getElementById("total_links_chart"));

    chart.draw(view, options);
}

google.charts.setOnLoadCallback(drawTotalLinksChart);
