// static/js/expense-tracker.js

document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('expensesChart').getContext('2d');

    // This assumes you're passing the data from Flask to your template
    const chartCategories = JSON.parse(document.getElementById('chart-categories').textContent);
    const chartData = JSON.parse(document.getElementById('chart-data').textContent);

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: chartCategories,
            datasets: [{
                data: chartData,
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: {
                    display: true,
                    text: 'Expenses by Category'
                }
            }
        }
    });
});