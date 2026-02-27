const token = localStorage.getItem('token');
let currentUser = JSON.parse(localStorage.getItem('user'));
let isBalanceVisible = false;

if (!token) {
    window.location.href = '/';
}

document.addEventListener('DOMContentLoaded', () => {
    if (currentUser) {
        document.getElementById('welcomeText').textContent = `Welcome, ${currentUser.name}`;
        updateBalanceDisplay(currentUser.balance);
    }

    fetchBalance();
    fetchDisputeHistory();

    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });
});

function updateBalanceDisplay(bal) {
    const balanceElem = document.getElementById('userBalance');
    const eyeSlash = document.getElementById('eyeSlash');

    if (isBalanceVisible) {
        balanceElem.textContent = `₹ ${parseFloat(bal).toFixed(2)}`;
        eyeSlash.style.display = 'none'; // Hide the slash line (eye open)
    } else {
        balanceElem.textContent = '********';
        eyeSlash.style.display = 'block'; // Show the slash line (eye closed)
    }
}

function toggleBalanceVisibility() {
    isBalanceVisible = !isBalanceVisible;
    if (currentUser && currentUser.balance !== undefined) {
        updateBalanceDisplay(currentUser.balance);
    }
}

async function fetchBalance() {
    try {
        const res = await fetch('/api/user/balance', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            currentUser.balance = data.balance;
            localStorage.setItem('user', JSON.stringify(currentUser));
            updateBalanceDisplay(data.balance);
        } else if (res.status === 401) {
            localStorage.clear(); window.location.href = '/';
        }
    } catch (e) { console.error(e); }
}

// Modals
function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// Transactions
async function sendMoney() {
    const receiver = document.getElementById('sendReceiver').value;
    const amount = document.getElementById('sendAmount').value;
    if (!receiver || !amount) return alert('Enter all details');

    try {
        const res = await fetch('/api/transaction/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ receiver_upi: receiver, amount: amount })
        });

        if (res.status === 401) {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const data = await res.json();

        if (res.ok) {
            alert(`Transaction Processed!\nStatus: ${data.status}\nTxn ID: ${data.transaction_id}`);
            closeModal('sendMoneyModal');
            document.getElementById('sendReceiver').value = '';
            document.getElementById('sendAmount').value = '';
            fetchBalance();
        } else {
            alert(`Error: ${data.msg}`);
        }
    } catch (e) { console.error(e); }
}

async function fetchHistory() {
    const section = document.getElementById('txnHistorySection');
    const list = document.getElementById('txnList');
    section.style.display = 'block';
    list.innerHTML = '<li>Loading...</li>';

    try {
        const res = await fetch('/api/transaction/history', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        // No 401 check here as per instruction, but good practice would be to add it.
        const data = await res.json();

        list.innerHTML = '';
        if (data.length === 0) list.innerHTML = '<li>No recent transactions</li>';

        data.forEach(t => {
            const li = document.createElement('li');
            li.innerHTML = `
                <div>
                    <strong>To: ${t.receiver_upi}</strong><br>
                    <small style="color:var(--text-secondary)">ID: ${t.id}</small><br>
                    <small>${new Date(t.timestamp).toLocaleString()}</small>
                </div>
                <div style="text-align:right">
                    <strong>₹${t.amount.toFixed(2)}</strong><br>
                    <span class="status-tag status-${t.status.toLowerCase()}">${t.status}</span>
                </div>
            `;
            list.appendChild(li);
        });
    } catch (e) { console.error(e); }
}

// Dispute Resolution
async function checkTransactionStatus() {
    let txnId = document.getElementById('txnIdInput').value;
    txnId = txnId ? txnId.trim() : '';
    if (!txnId) return alert('Enter transaction ID');

    const resDiv = document.getElementById('resolutionResult');
    resDiv.innerHTML = '<p>Verifying with bank and merchant servers...</p>';

    try {
        const res = await fetch('/api/dispute/resolve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ transaction_id: txnId })
        });

        if (res.status === 401) {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const data = await res.json();

        if (res.ok) {
            resDiv.innerHTML = `
                <div class="glassmorphism" style="padding:20px; margin-top:15px; border-left: 4px solid var(--accent)">
                    <h4 style="margin-bottom:10px">Dispute Resolution Report</h4>
                    <p><strong>Final Status:</strong> <span class="status-tag status-${data.transaction_status.toLowerCase()}">${data.transaction_status}</span></p>
                    <p><strong>Agent Note:</strong> ${data.dispute_status}</p>
                    <p><small>Bank Report: Debited=${data.bank_info.debited}, Credited=${data.bank_info.credited}</small></p>
                    <p><small>Merchant Report: Received=${data.merchant_info.received}</small></p>
                </div>
            `;
            fetchDisputeHistory();
        } else {
            resDiv.innerHTML = `<p style="color:var(--danger)">${data.msg}</p>`;
        }
    } catch (e) { console.error(e); resDiv.innerHTML = 'Error verifying.'; }
}

async function fetchDisputeHistory() {
    try {
        const res = await fetch('/api/dispute/history', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        const tbody = document.querySelector('#disputeTable tbody');
        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">No disputes filed</td></tr>';
            return;
        }

        data.forEach(d => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><small>${d.merchant_txn_id}</small></td>
                <td><small>${d.receiver_txn_id}</small></td>
                <td>₹${d.original_amount.toFixed(2)}</td>
                <td>${d.dispute_status}</td>
                <td><small>${new Date(d.resolved_at).toLocaleString()}</small></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
}
