// User Activity Chart (Bar Chart)
const userCtx = document.getElementById('userChart').getContext('2d');
const userChart = new Chart(userCtx, {
    type: 'bar',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'New Users',
            data: [12, 19, 3, 5, 2, 3],
            backgroundColor: '#FFC107',
            borderColor: '#FFB300',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Monthly User Signups' }
        },
        scales: {
            y: { beginAtZero: true }
        }
    }
});

// Document Uploads Chart (Line Chart)
const docCtx = document.getElementById('documentChart').getContext('2d');
const documentChart = new Chart(docCtx, {
    type: 'line',
    data: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{
            label: 'Documents Uploaded',
            data: [5, 10, 7, 12],
            borderColor: '#007BFF',
            backgroundColor: 'rgba(0,123,255,0.2)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Weekly Document Uploads' }
        },
        scales: {
            y: { beginAtZero: true }
        }
    }
});
