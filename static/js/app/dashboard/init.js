// Chart data comes from <script type="application/json"> blocks rendered with Django's |json_script,
// so the page needs no inline JavaScript (Content-Security-Policy friendly).
const readChartData = (id) => JSON.parse(document.getElementById(id).textContent);

const latestTotalClicks = readChartData('latest-total-clicks-data');
const totalClicks = readChartData('total-clicks-data');
const totalLinksData = readChartData('total-links-data');
const totalActiveUrl = readChartData('total-active-url-data');
const activity = readChartData('activity-data');
const enabledDisabled = readChartData('enabled-disabled-data');

google.charts.load('current', {'packages': ['corechart']});
