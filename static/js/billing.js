// POS Billing System Logic
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('bill-product-search');
    const searchResults = document.getElementById('searchResults');
    const billItemsContainer = document.getElementById('billItems');
    const emptyBillState = document.getElementById('emptyBillState');
    const itemCountBadge = document.getElementById('itemCount');

    const subtotalEl = document.getElementById('billSubtotal');
    const discountInput = document.getElementById('billDiscount');
    const taxEl = document.getElementById('billTax');
    const grandTotalEl = document.getElementById('billGrandTotal');
    const createBillBtn = document.getElementById('createBillBtn');

    let items = []; // Array of { id, name, price, stock, unit, qty, total }

    // Search Products
    let debounceTimer;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const query = searchInput.value.trim();
            if (query.length < 1) {
                searchResults.classList.remove('show');
                return;
            }
            debounceTimer = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/products/search/?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    renderSearchResults(data.products || []);
                } catch (e) {
                    console.error('Product search failed', e);
                }
            }, 250);
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.remove('show');
            }
        });
    }

    function renderSearchResults(products) {
        if (products.length === 0) {
            searchResults.innerHTML = `<div style="padding: 12px; text-align: center; color: var(--text-muted); font-size: 13px;">No matching active products with available stock found.</div>`;
            searchResults.classList.add('show');
            return;
        }

        searchResults.innerHTML = products.map(p => `
            <div class="search-result-item" data-id="${p.id}" data-name="${escapeHtml(p.name)}" data-price="${p.price}" data-stock="${p.stock}" data-unit="${p.unit}">
                <div>
                    <div class="search-result-name">${escapeHtml(p.name)}</div>
                    <div class="search-result-meta">Stock: ${p.stock} ${p.unit} | SKU: ${p.sku}</div>
                </div>
                <div class="search-result-price">₹${p.price.toFixed(2)}</div>
            </div>
        `).join('');

        searchResults.classList.add('show');

        // Add click listener to each result
        searchResults.querySelectorAll('.search-result-item').forEach(el => {
            el.addEventListener('click', () => {
                const id = parseInt(el.dataset.id);
                const name = el.dataset.name;
                const price = parseFloat(el.dataset.price);
                const stock = parseInt(el.dataset.stock);
                const unit = el.dataset.unit;

                addProductToBill({ id, name, price, stock, unit });
                searchInput.value = '';
                searchResults.classList.remove('show');
            });
        });
    }

    function addProductToBill(product) {
        const existing = items.find(i => i.id === product.id);
        if (existing) {
            if (existing.qty < product.stock) {
                existing.qty += 1;
                existing.total = existing.qty * existing.price;
            } else {
                alert(`Cannot add more. Max available stock is ${product.stock}`);
            }
        } else {
            items.push({
                id: product.id,
                name: product.name,
                price: product.price,
                stock: product.stock,
                unit: product.unit,
                qty: 1,
                total: product.price
            });
        }
        renderBillItems();
    }

    function renderBillItems() {
        if (items.length === 0) {
            billItemsContainer.innerHTML = '';
            emptyBillState.style.display = 'block';
            createBillBtn.disabled = true;
            itemCountBadge.textContent = '0 items';
            updateTotals();
            return;
        }

        emptyBillState.style.display = 'none';
        createBillBtn.disabled = false;

        let totalQtyCount = 0;

        billItemsContainer.innerHTML = items.map((item, index) => {
            totalQtyCount += item.qty;
            return `
                <div class="bill-item-row" data-index="${index}">
                    <div>
                        <div class="fw-600" style="color: var(--text-primary); font-size: 14px;">${escapeHtml(item.name)}</div>
                        <div class="text-xs text-muted">Stock: ${item.stock} ${item.unit}</div>
                    </div>
                    <div>
                        <input type="number" class="qty-input" min="1" max="${item.stock}" value="${item.qty}" data-index="${index}">
                    </div>
                    <div class="text-center" style="font-size: 14px;">₹${item.price.toFixed(2)}</div>
                    <div class="text-center fw-600" style="color: var(--accent-primary); font-size: 14px;">₹${item.total.toFixed(2)}</div>
                    <div>
                        <button class="remove-item" data-index="${index}" title="Remove"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            `;
        }).join('');

        itemCountBadge.textContent = `${items.length} items (${totalQtyCount} qty)`;

        // Add event listeners for qty inputs and remove buttons
        billItemsContainer.querySelectorAll('.qty-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const idx = parseInt(e.target.dataset.index);
                let val = parseInt(e.target.value);
                if (isNaN(val) || val < 1) val = 1;
                if (val > items[idx].stock) {
                    alert(`Maximum available stock is ${items[idx].stock}`);
                    val = items[idx].stock;
                }
                items[idx].qty = val;
                items[idx].total = val * items[idx].price;
                renderBillItems();
            });
        });

        billItemsContainer.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(btn.closest('.remove-item').dataset.index);
                items.splice(idx, 1);
                renderBillItems();
            });
        });

        updateTotals();
    }

    function updateTotals() {
        const subtotal = items.reduce((sum, item) => sum + item.total, 0);
        const discount = parseFloat(discountInput.value) || 0;
        const taxableAmount = Math.max(0, subtotal - discount);
        const tax = taxableAmount * (TAX_RATE / 100);
        const grandTotal = taxableAmount + tax;

        subtotalEl.textContent = `₹${subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        taxEl.textContent = `₹${tax.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        grandTotalEl.textContent = `₹${grandTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    if (discountInput) {
        discountInput.addEventListener('input', updateTotals);
    }

    // Radio button styling for payment method
    document.querySelectorAll('input[name="payment"]').forEach(radio => {
        radio.addEventListener('change', () => {
            document.querySelectorAll('input[name="payment"]').forEach(r => {
                const label = document.getElementById(`pay-${r.value}-label`);
                if (label) {
                    if (r.checked) {
                        label.classList.remove('btn-secondary');
                        label.classList.add('btn-primary');
                    } else {
                        label.classList.remove('btn-primary');
                        label.classList.add('btn-secondary');
                    }
                }
            });
        });
    });

    // Create Bill AJAX Submit
    if (createBillBtn) {
        createBillBtn.addEventListener('click', async () => {
            if (items.length === 0) return;

            const customerName = document.getElementById('customer-name').value.trim() || 'Walk-in Customer';
            const customerPhone = document.getElementById('customer-phone').value.trim();
            const discount = parseFloat(discountInput.value) || 0;
            const paymentMethod = document.querySelector('input[name="payment"]:checked')?.value || 'cash';
            const notes = document.getElementById('bill-notes').value.trim();

            const payload = {
                customer_name: customerName,
                customer_phone: customerPhone,
                discount: discount,
                payment_method: paymentMethod,
                notes: notes,
                items: items.map(i => ({
                    product_id: i.id,
                    quantity: i.qty
                }))
            };

            createBillBtn.disabled = true;
            createBillBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing...`;

            try {
                const res = await fetch('/billing/new/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN
                    },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                if (res.ok && data.success) {
                    // Redirect to printed invoice page
                    window.location.href = `/billing/${data.bill_id}/`;
                } else {
                    alert(data.error || 'Failed to create bill');
                    createBillBtn.disabled = false;
                    createBillBtn.innerHTML = `<i class="fas fa-check-circle"></i> Create Bill`;
                }
            } catch (err) {
                console.error(err);
                alert('Network error while creating bill');
                createBillBtn.disabled = false;
                createBillBtn.innerHTML = `<i class="fas fa-check-circle"></i> Create Bill`;
            }
        });
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
});
