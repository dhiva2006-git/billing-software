// Dashboard Charts for ShopBill Pro
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/dashboard/');
        if (!response.ok) return;
        const data = await response.json();

        // Common Chart.js styling defaults
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', sans-serif";

        // 1. Weekly Sales Chart (Bar)
        const weeklyCtx = document.getElementById('weeklyChart');
        if (weeklyCtx && data.weekly) {
            new Chart(weeklyCtx, {
                type: 'bar',
                data: {
                    labels: data.weekly.map(d => d.day),
                    datasets: [{
                        label: 'Sales (₹)',
                        data: data.weekly.map(d => d.total),
                        backgroundColor: 'rgba(0, 212, 170, 0.4)',
                        borderColor: '#00d4aa',
                        borderWidth: 2,
                        borderRadius: 6,
                        hoverBackgroundColor: '#00d4aa'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` Sales: ₹${ctx.parsed.y.toLocaleString('en-IN')}`
                            }
                        }
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: {
                                callback: val => '₹' + val.toLocaleString('en-IN')
                            }
                        }
                    }
                }
            });
        }

        // 2. Monthly Revenue Trend Chart (Line)
        const monthlyCtx = document.getElementById('monthlyChart');
        if (monthlyCtx && data.monthly) {
            new Chart(monthlyCtx, {
                type: 'line',
                data: {
                    labels: data.monthly.map(d => d.month),
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: data.monthly.map(d => d.total),
                        borderColor: '#00b4d8',
                        backgroundColor: 'rgba(0, 180, 216, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#00b4d8',
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
                            ticks: {
                                callback: val => '₹' + val.toLocaleString('en-IN')
                            }
                        }
                    }
                }
            });
        }

        // 3. Top Products Doughnut Chart
        const topCtx = document.getElementById('topProductsChart');
        if (topCtx && data.top_products && data.top_products.length > 0) {
            const colors = ['#00d4aa', '#00b4d8', '#38bdf8', '#8b5cf6', '#f59e0b', '#f43f5e'];
            new Chart(topCtx, {
                type: 'doughnut',
                data: {
                    labels: data.top_products.map(p => p.product_name),
                    datasets: [{
                        data: data.top_products.map(p => p.total_revenue),
                        backgroundColor: colors.slice(0, data.top_products.length),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { boxWidth: 12, padding: 12 }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` ₹${ctx.parsed.toLocaleString('en-IN')}`
                            }
                        }
                    },
                    cutout: '68%'
                }
            });
        }
    } catch (err) {
        console.error('Error fetching dashboard chart data:', err);
    }
});
