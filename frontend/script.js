/* script.js */

const API_URL = 'http://localhost:8000';

// Elementos HTML
const loginContainer = document.getElementById('login-container');
const dashboardContainer = document.getElementById('dashboard-container');
const loginForm = document.getElementById('login-form');
const errorMessage = document.getElementById('error-message');
const tableBody = document.querySelector('#metrics-table tbody');
const tableHeaders = document.querySelectorAll('#metrics-table th');
const startDateInput = document.getElementById('start_date');
const endDateInput = document.getElementById('end_date');
const applyFiltersBtn = document.getElementById('apply-filters-btn');
const prevPageBtn = document.getElementById('prev-page-btn');
const nextPageBtn = document.getElementById('next-page-btn');
const pageInfoSpan = document.getElementById('page-info');
const logoutBtn = document.getElementById('logout-btn');
const popupWrapper = document.getElementById("popup-wrapper");
const popupContent = document.getElementById("popup-content");
const popupTitle = document.getElementById("popup-title");
const popupMessage = document.getElementById("popup-message");
const clearFiltersBtn = document.getElementById('clear-filters-btn');

let token = null;
let userRole = null;
let currentPage = 1;
let sortColumn = 'date';
let sortOrder = 'desc';

// --- Funções de Pop-up ---
function showPopup(message, type = 'error') {
    popupMessage.textContent = message;
    popupTitle.textContent = type === 'success' ? 'Sucesso!' : 'Erro!';
    
    popupContent.classList.remove('success', 'error');
    popupContent.classList.add(type);
    
    popupWrapper.style.display = 'block';
}

function hidePopup() {
    popupWrapper.style.display = 'none';
}

// --- Funções Principais ---
async function fetchMetrics(source = 'apply') {
    if (!token) {
        showLogin();
        return;
    }

    const params = new URLSearchParams();
    params.append('page', currentPage);
    params.append('sort', sortColumn);
    params.append('order', sortOrder);

    if (startDateInput.value) {
        params.append('start_date', startDateInput.value);
    }
    if (endDateInput.value) {
        params.append('end_date', endDateInput.value);
    }

    try {
        const response = await fetch(`${API_URL}/metrics?${params.toString()}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            showLogin();
            return;
        }

        if (!response.ok) {
            const errorData = await response.json();
            showPopup(`Erro: ${errorData.detail}`, 'error');
            tableBody.innerHTML = '';
            return;
        }

        const data = await response.json();
        renderTable(data.data);
        updatePagination(data.page, data.total_items);
        
        // Decide qual pop-up mostrar com base na origem
        if (source === 'clear') {
            showPopup('Filtros retirados!', 'success');
        } else if (source === 'apply') {
            if (data.data.length > 0) {
                showPopup('Filtro aplicado com sucesso!', 'success');
            } else {
                showPopup('Nenhum dado encontrado para este filtro.', 'error');
            }
        }

    } catch (error) {
        showPopup('Erro de conexão com a API. Tente novamente mais tarde.', 'error');
        console.error('Failed to fetch:', error);
    }
}

function renderTable(metrics) {
    tableBody.innerHTML = '';
    const isCostVisible = userRole === 'admin';

    // Mostra/esconde a coluna de custo com base na role do usuário
    document.querySelectorAll('.admin-only').forEach(th => {
        th.style.display = isCostVisible ? '' : 'none';
    });
    
    metrics.forEach(metric => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${metric.account_id}</td>
            <td>${metric.campaign_id}</td>
            <td>${metric.clicks}</td>
            <td>${metric.conversions}</td>
            <td>${metric.impressions}</td>
            <td>${metric.interactions}</td>
            <td>${metric.date}</td>
            ${isCostVisible ? `<td>${metric.cost_micros}</td>` : ''}
        `;
        tableBody.appendChild(row);
    });
}

function updatePagination(page, totalItems) {
    pageInfoSpan.textContent = `Página ${page}`;
    prevPageBtn.disabled = page <= 1;
    nextPageBtn.disabled = false;
}

function showDashboard() {
    loginContainer.style.display = 'none';
    dashboardContainer.style.display = 'block';
    fetchMetrics(); 
}

function showLogin() {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    token = null;
    userRole = null;
    loginContainer.style.display = 'block';
    dashboardContainer.style.display = 'none';
}

function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    showLogin();
}

// --- Eventos ---

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            username: email,
            password: password
        })
    });

    if (response.ok) {
        const data = await response.json();
        token = data.access_token;
        userRole = data.role;
        localStorage.setItem('token', token);
        localStorage.setItem('userRole', userRole);
        errorMessage.textContent = '';
        showDashboard();
    } else {
        errorMessage.textContent = 'Credenciais inválidas. Tente novamente.';
    }
});

logoutBtn.addEventListener('click', handleLogout);

window.addEventListener('click', (e) => {
    if (e.target === popupWrapper) hidePopup();
});

clearFiltersBtn.addEventListener('click', () => {
    startDateInput.value = '';
    endDateInput.value = '';
    currentPage = 1;
    fetchMetrics('clear'); // Passa 'clear' como a origem
});

// Ordenação
tableHeaders.forEach(header => {
    header.addEventListener('click', () => {
        const newSortColumn = header.dataset.sort;
        if (newSortColumn === sortColumn) {
            sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            sortColumn = newSortColumn;
            sortOrder = 'asc';
        }
        currentPage = 1;
        fetchMetrics();
    });
});

// Paginação
prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        fetchMetrics();
    }
});

nextPageBtn.addEventListener('click', () => {
    currentPage++;
    fetchMetrics();
});

// Filtros
applyFiltersBtn.addEventListener('click', () => {
    if (!startDateInput.value || !endDateInput.value) {
        showPopup('Por favor, preencha as datas de início e fim para usar o filtro.', 'error');
        return; 
    }
    currentPage = 1;
    fetchMetrics('apply'); // Passa 'apply' como a origem
});

// --- Inicialização ---

document.addEventListener('DOMContentLoaded', () => {
    // Tenta carregar token e role do localStorage
    token = localStorage.getItem('token');
    userRole = localStorage.getItem('userRole');

    if (token && userRole) {
        showDashboard();
    } else {
        showLogin();
    }

    const container = document.querySelector(".table-container");
    const btnLeft = document.querySelector(".scroll-btn.left");
    const btnRight = document.querySelector(".scroll-btn.right");

    btnLeft.addEventListener("click", () => {
        container.scrollBy({ left: -150, behavior: "smooth" });
    });

    btnRight.addEventListener("click", () => {
        container.scrollBy({ left: 150, behavior: "smooth" });
    });
});