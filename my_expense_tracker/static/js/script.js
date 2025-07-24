document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element Selectors ---
    const addExpenseForm = document.getElementById('add-expense-form');
    const smsParserForm = document.getElementById('sms-parser-form');
    const expensesTableBody = document.querySelector('#expenses-table tbody');
    const summaryTableBody = document.querySelector('#summary-table tbody');
    const monthPicker = document.getElementById('month-picker');
    const getInsightsBtn = document.getElementById('get-insights-btn');
    const insightsContainer = document.getElementById('insights-container');
    const prevPageBtn = document.getElementById('prev-page-btn');
    const nextPageBtn = document.getElementById('next-page-btn');
    const pageInfo = document.getElementById('page-info');

    let currentPage = 1;

    // --- API Helper Function ---
    async function apiFetch(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json();
            }
            // Handle cases like 201 Created which might not return JSON
            return response.text().then(text => ({ message: text }));
        } catch (error) {
            console.error('API Fetch Error:', error);
            alert(`An error occurred: ${error.message}`);
            return null;
        }
    }

    // --- Data Loading Functions ---

    const fetchAndDisplayExpenses = async (page = 1) => {
        const data = await apiFetch(`/api/expenses?page=${page}`);
        if (!data) return;

        const { expenses, total_records, limit } = data;

        expensesTableBody.innerHTML = ''; // Clear existing rows
        expenses.forEach(exp => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${exp.date}</td>
                <td>${exp.category}</td>
                <td>${exp.description}</td>
                <td>${exp.amount.toFixed(2)}</td>
                <td>${exp.total_outflow.toFixed(2)}</td>
            `;
            expensesTableBody.appendChild(row);
        });

        // Update pagination controls
        currentPage = data.page;
        const totalPages = Math.ceil(total_records / limit);
        pageInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;

        prevPageBtn.disabled = currentPage <= 1;
        nextPageBtn.disabled = currentPage >= totalPages;
    };

    const fetchAndDisplaySummary = async (yearMonth) => {
        if (!yearMonth) return;
        const summary = await apiFetch(`/api/summary?year_month=${yearMonth}`);
        if (!summary) return;

        summaryTableBody.innerHTML = ''; // Clear existing rows
        summary.forEach(item => {
            const row = document.createElement('tr');
            const remaining = item.remaining;
            const remainingClass = remaining < 0 ? 'error-message' : '';
            row.innerHTML = `
                <td>${item.category}</td>
                <td>${item.total_spent.toFixed(2)}</td>
                <td>${item.budgeted.toFixed(2)}</td>
                <td class="${remainingClass}">${remaining.toFixed(2)}</td>
            `;
            summaryTableBody.appendChild(row);
        });
    };

    // --- Event Handlers ---

    // Handle Add Expense Form Submission
    addExpenseForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formSuccess = document.getElementById('form-success');
        formSuccess.textContent = '';

        const expenseData = {
            date: document.getElementById('date').value,
            description: document.getElementById('description').value,
            category: document.getElementById('category').value,
            amount: parseFloat(document.getElementById('amount').value),
            payment_method: document.getElementById('payment-method').value,
            mpesa_charge: parseFloat(document.getElementById('mpesa-charge').value) || 0,
        };

        const result = await apiFetch('/api/expenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(expenseData),
        });

        if (result) {
            formSuccess.textContent = result.message || "Expense added successfully!";
            addExpenseForm.reset();
            // Set date back to today after reset
            document.getElementById('date').valueAsDate = new Date();
            // Refresh data on screen
            fetchAndDisplayExpenses();
            fetchAndDisplaySummary(monthPicker.value);
            setTimeout(() => formSuccess.textContent = '', 3000);
        }
    });

    // Handle SMS Parser Form Submission
    smsParserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const smsError = document.getElementById('sms-error');
        smsError.textContent = '';

        const smsMessage = document.getElementById('sms-message').value;
        if (!smsMessage.trim()) {
            smsError.textContent = 'SMS message cannot be empty.';
            return;
        }

        const parsedData = await apiFetch('/api/parse-sms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sms_message: smsMessage }),
        });

        if (parsedData) {
            if (parsedData.error) {
                smsError.textContent = parsedData.error;
            } else {
                // Pre-fill the add expense form
                document.getElementById('date').value = parsedData.date;
                document.getElementById('description').value = parsedData.description;
                document.getElementById('category').value = parsedData.suggested_category || '';
                document.getElementById('amount').value = parsedData.amount;
                document.getElementById('payment-method').value = 'MPESA';
                document.getElementById('mpesa-charge').value = parsedData.transaction_cost || 0;
                document.getElementById('sms-message').value = ''; // Clear the textarea
            }
        }
    });

    // Handle Month Picker Change
    monthPicker.addEventListener('change', () => {
        fetchAndDisplaySummary(monthPicker.value);
    });

    // Handle Get Insights Button Click
    getInsightsBtn.addEventListener('click', async () => {
        insightsContainer.innerHTML = '<p>Analyzing your data...</p>';
        const data = await apiFetch('/api/insights');
        if (data && data.insights) {
            // Replace newlines with <br> and wrap each insight in a <p> tag
            insightsContainer.innerHTML = data.insights
                .map(insight => `<p>${insight.replace(/\n/g, '<br>')}</p>`)
                .join('');
        } else {
            insightsContainer.innerHTML = `<p class="error-message">${data.error || 'Could not fetch insights.'}</p>`;
        }
    });

    // Handle Pagination Button Clicks
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            fetchAndDisplayExpenses(currentPage - 1);
        }
    });

    nextPageBtn.addEventListener('click', () => {
        fetchAndDisplayExpenses(currentPage + 1);
    });

    // --- Initial Page Load ---
    const init = () => {
        // Set default date for expense form to today
        document.getElementById('date').valueAsDate = new Date();

        // Set default month for summary to current month
        const today = new Date();
        const year = today.getFullYear();
        const month = (today.getMonth() + 1).toString().padStart(2, '0');
        const currentMonth = `${year}-${month}`;
        monthPicker.value = currentMonth;

        // Load initial data
        fetchAndDisplayExpenses();
        fetchAndDisplaySummary(currentMonth);
    };

    init();
});