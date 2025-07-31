document.addEventListener('DOMContentLoaded', () => {

    const API_BASE_URL = 'http://127.0.0.1:8000/api';
    let allDepartments = []; // Cache for department data

    // --- DOM ELEMENTS ---
    const pageTitle = document.getElementById('page-title');
    const departmentsList = document.getElementById('departments-list');
    const productsListView = document.getElementById('products-list-view');
    const productDetailView = document.getElementById('product-detail-view');
    const productsGrid = document.getElementById('products-grid');
    const productDetailsContainer = document.getElementById('product-details');
    const backButton = document.getElementById('back-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');

    // --- API FUNCTIONS ---
    async function fetchDepartments() {
        try {
            const response = await fetch(`${API_BASE_URL}/departments`);
            if (!response.ok) throw new Error('Failed to fetch departments');
            allDepartments = await response.json();
            displayDepartments(allDepartments);
        } catch (error) {
            console.error('Fetch departments error:', error);
            departmentsList.innerHTML = '<li>Error loading departments.</li>';
        }
    }

    async function fetchData(url) {
        showLoading(true);
        hideError();
        try {
            const response = await fetch(url);
            if (!response.ok) {
                if (response.status === 404) return null; // Handle 404 gracefully
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            showError('Failed to fetch data. Please check the API server.');
            console.error('Fetch error:', error);
            return []; // Return empty array on error to clear grid
        } finally {
            showLoading(false);
        }
    }

    // --- RENDERING FUNCTIONS ---
    function displayDepartments(departments) {
        departmentsList.innerHTML = '<li><a href="#" class="active">All Products</a></li>'; // Add "All Products" link
        departments.forEach(dept => {
            const li = document.createElement('li');
            li.innerHTML = `
                <a href="#/departments/${dept.id}" data-id="${dept.id}">
                    <span>${dept.name}</span>
                    <span class="count">${dept.product_count}</span>
                </a>
            `;
            departmentsList.appendChild(li);
        });
    }

    function displayProducts(products) {
        productsGrid.innerHTML = ''; // Clear previous content
        if (!products || products.length === 0) {
            productsGrid.innerHTML = '<p>No products found.</p>';
            return;
        }
        products.forEach(product => {
            const productCard = document.createElement('a');
            productCard.href = `#/product/${product.id}`;
            productCard.className = 'product-card fade-in';
            productCard.innerHTML = `
                <h2>${product.name || 'Unnamed Product'}</h2>
                <p class="brand">by ${product.brand || 'Unknown Brand'}</p>
                <p class="price">$${product.retail_price.toFixed(2)}</p>
            `;
            productsGrid.appendChild(productCard);
        });
    }

    function displayProductDetail(product) {
        if (!product) {
            showError('Product not found.');
            showView('list'); // Go back to list if product is not found
            return;
        }
        productDetailsContainer.innerHTML = `
            <div class="product-detail-container">
                <div class="product-hero">
                    <h1>${product.name}</h1>
                    <p class="brand">by ${product.brand}</p>
                    <p class="price">$${product.retail_price.toFixed(2)}</p>
                </div>
                <div class="product-info">
                    <table class="product-info-table">
                        <tr><td>Category</td><td>${product.category || 'N/A'}</td></tr>
                        <tr><td>Department</td><td>${product.department.name}</td></tr>
                        <tr><td>SKU</td><td>${product.sku || 'N/A'}</td></tr>
                        <tr><td>Product ID</td><td>${product.id}</td></tr>
                    </table>
                </div>
            </div>
        `;
    }

    // --- UI HELPER FUNCTIONS ---
    function showView(view) {
        productsListView.classList.toggle('hidden', view !== 'list');
        productDetailView.classList.toggle('hidden', view !== 'detail');
    }

    function updateActiveDepartmentLink(departmentId) {
        document.querySelectorAll('#departments-list a').forEach(a => {
            a.classList.remove('active');
            if (a.dataset.id === departmentId || (departmentId === null && a.getAttribute('href') === '#')) {
                a.classList.add('active');
            }
        });
    }
    
    function updatePageHeader(title) {
        pageTitle.textContent = title;
    }

    function showLoading(isLoading) { loadingIndicator.classList.toggle('hidden', !isLoading); }
    function showError(message) { errorMessage.textContent = message; errorMessage.classList.remove('hidden'); }
    function hideError() { errorMessage.classList.add('hidden'); }

    // --- ROUTER & NAVIGATION ---
    async function router() {
        const hash = window.location.hash;
        
        const productRoute = hash.match(/^#\/product\/(\d+)$/);
        const departmentRoute = hash.match(/^#\/departments\/(\d+)$/);

        showView('list'); // Default to list view, show detail view only if needed

        if (productRoute) {
            const productId = productRoute[1];
            updatePageHeader('Product Details');
            updateActiveDepartmentLink(null); // No active department
            const product = await fetchData(`${API_BASE_URL}/products/${productId}`);
            displayProductDetail(product);
            showView('detail');
        } else if (departmentRoute) {
            const departmentId = departmentRoute[1];
            const products = await fetchData(`${API_BASE_URL}/departments/${departmentId}/products`);
            displayProducts(products);
            
            const department = allDepartments.find(d => d.id == departmentId);
            updatePageHeader(department ? `${department.name} (${department.product_count} Products)` : 'Department');
            updateActiveDepartmentLink(departmentId);
        } else {
            // Home page (All Products)
            const products = await fetchData(`${API_BASE_URL}/products?limit=50`);
            displayProducts(products);
            updatePageHeader('All Products');
            updateActiveDepartmentLink(null);
        }
    }

    // --- EVENT LISTENERS ---
    window.addEventListener('hashchange', router);
    backButton.addEventListener('click', () => {
        window.history.back(); // More natural than setting hash to ''
    });

    // --- INITIALIZATION ---
    async function init() {
        await fetchDepartments(); // Fetch departments for the sidebar first
        await router();           // Then, route to the correct page
    }

    init();
});