document.addEventListener('DOMContentLoaded', () => {

    const API_BASE_URL = 'http://127.0.0.1:8000/api';

    const productsListView = document.getElementById('products-list-view');
    const productDetailView = document.getElementById('product-detail-view');
    const productsGrid = document.getElementById('products-grid');
    const productDetailsContainer = document.getElementById('product-details');
    const backButton = document.getElementById('back-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');

    async function fetchProducts() {
        showLoading(true);
        hideError();
        try {
            const response = await fetch(`${API_BASE_URL}/products?limit=50`);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const products = await response.json();
            displayProducts(products);
        } catch (error) {
            showError('Failed to fetch products. The API server may be down.');
            console.error('Fetch products error:', error);
        } finally {
            showLoading(false);
        }
    }

    async function fetchProductById(id) {
        showLoading(true);
        hideError();
        try {
            const response = await fetch(`${API_BASE_URL}/products/${id}`);
            if (response.status === 404) {
                showError(`Product with ID ${id} not found.`);
                return null;
            }
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            showError('Failed to fetch product details.');
            console.error(`Fetch product by ID error for ID ${id}:`, error);
            return null;
        } finally {
            showLoading(false);
        }
    }

    function displayProducts(products) {
        productsGrid.innerHTML = '';
        products.forEach(product => {
            const productCard = document.createElement('a');
            productCard.href = `#/product/${product.id}`;
            productCard.className = 'product-card';
            productCard.innerHTML = `
                <h2>${product.name}</h2>
                <p class="brand">by ${product.brand}</p>
                <p class="price">$${product.retail_price.toFixed(2)}</p>
            `;
            productsGrid.appendChild(productCard);
        });
    }

    function displayProductDetail(product) {
        productDetailsContainer.innerHTML = `
            <div class="product-detail-container">
                <div class="product-hero">
                    <h1>${product.name}</h1>
                    <p class="brand">by ${product.brand}</p>
                    <p class="price">$${product.retail_price.toFixed(2)}</p>
                </div>
                <div class="product-info">
                    <table class="product-info-table">
                        <tr><td>Category</td><td>${product.category}</td></tr>
                        <tr><td>Department</td><td>${product.department}</td></tr>
                        <tr><td>SKU</td><td>${product.sku}</td></tr>
                        <tr><td>Product ID</td><td>${product.id}</td></tr>
                    </table>
                </div>
            </div>
        `;
    }

    function showView(view) {
        // Hide all main views initially
        productsListView.classList.add('hidden');
        productDetailView.classList.add('hidden');
        
        // Remove fade-in class to reset animation
        productsListView.classList.remove('fade-in');
        productDetailView.classList.remove('fade-in');

        // Show the correct view and trigger animation
        if (view === 'list') {
            productsListView.classList.remove('hidden');
            productsListView.classList.add('fade-in');
        } else if (view === 'detail') {
            productDetailView.classList.remove('hidden');
            productDetailView.classList.add('fade-in');
        }
    }
    
    function showLoading(isLoading) {
        loadingIndicator.classList.toggle('hidden', !isLoading);
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
    }

    async function router() {
        const hash = window.location.hash;
        const productRouteMatch = hash.match(/^#\/product\/(\d+)$/);

        hideError();

        if (productRouteMatch) {
            const productId = productRouteMatch[1];
            const product = await fetchProductById(productId);
            if (product) {
                displayProductDetail(product);
                showView('detail');
            } else {
                // If product not found, stay on detail view to show error
                showView('detail'); 
                productDetailsContainer.innerHTML = ''; // Clear stale data
            }
        } else {
            showView('list');
            fetchProducts();
        }
    }

    window.addEventListener('hashchange', router);
    backButton.addEventListener('click', () => window.location.hash = '');
    
    // Initial page load
    router();
});