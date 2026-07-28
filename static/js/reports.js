// Reports Page Chart Rendering
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const fromDate = typeof REPORT_DATE_FROM !== 'undefined' ? REPORT_DATE_FROM : '';
        const toDate = typeof REPORT_DATE_TO !== 'undefined' ? REPORT_DATE_TO : '';

        const response = await fetch(`/api/reports/?from=${encodeURIComponent(fromDate)}&to=${encodeURIComponent(toDate)}`);
        if (!response.ok) return;
        const data = await response.json();

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', sans-serif";

        // 1. Daily Sales Line Chart
        const dailyCtx = document.getElementById('dailySalesChart');
        if (dailyCtx && data.daily && data.daily.length > 0) {
            new Chart(dailyCtx, {
                type: 'line',
                data: {
                    labels: data.daily.map(d => d.date),
                    datasets: [{
                        label: 'Daily Revenue (₹)',
                        data: data.daily.map(d => d.total),
                        borderColor: '#00d4aa',
                        backgroundColor: 'rgba(0, 212, 170, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#00d4aa',
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` Revenue: ₹${ctx.parsed.y.toLocaleString('en-IN')}`
                            }
                        }
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { callback: val => '₹' + val.toLocaleString('en-IN') }
                        }
                    }
                }
            });
        }

        // 2. Product Revenue Bar Chart
        const productCtx = document.getElementById('productRevenueChart');
        if (productCtx && data.top_products && data.top_products.length > 0) {
            new Chart(productCtx, {
                type: 'bar',
                data: {
                    labels: data.top_products.map(p => p.product_name),
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: data.top_products.map(p => p.total_revenue),
                        backgroundColor: 'rgba(56, 189, 248, 0.4)',
                        borderColor: '#38bdf8',
                        borderWidth: 2,
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` Revenue: ₹${ctx.parsed.x.toLocaleString('en-IN')}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { callback: val => '₹' + val.toLocaleString('en-IN') }
                        },
                        y: { grid: { display: false } }
                    }
                }
            });
        }

        // 3. Payment Method Doughnut Chart
        const paymentCtx = document.getElementById('paymentChart');
        if (paymentCtx && data.payments && data.payments.length > 0) {
            const colors = { cash: '#10b981', upi: '#38bdf8', card: '#f59e0b', other: '#8b5cf6' };
            new Chart(paymentCtx, {
                type: 'doughnut',
                data: {
                    labels: data.payments.map(p => p.payment_method.toUpperCase()),
                    datasets: [{
                        data: data.payments.map(p => p.total),
                        backgroundColor: data.payments.map(p => colors[p.payment_method] || '#94a3b8'),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right' },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` ₹${ctx.parsed.toLocaleString('en-IN')}`
                            }
                        }
                    },
                    cutout: '65%'
                }
            });
        }
    } catch (err) {
        console.error('Error rendering report charts:', err);
    }
});
