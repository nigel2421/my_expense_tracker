// c:\Users\USER\Documents\wewe\js\cart.js

const whatsappNumber = '254721202052'; // WhatsApp number without '+'
let cart = JSON.parse(localStorage.getItem('cityHardwareCart')) || [];

// DOM elements (these might not exist on all pages, so check for them)
const cartModal = document.getElementById('cartModal');
const closeButton = cartModal ? cartModal.querySelector('.close-button') : null;
const cartItemsContainer = document.getElementById('cartItems') || document.getElementById('cartItemsList'); // For modal or full cart page
const requestQuoteWhatsappBtn = document.getElementById('requestQuoteWhatsapp') || document.getElementById('requestQuoteWhatsappPage');
const clearCartBtn = document.getElementById('clearCart') || document.getElementById('clearCartPage');
const floatingCartButton = document.getElementById('floatingCartButton');
const cartCountSpan = document.getElementById('cartCount');

// Function to update cart count display
function updateCartCount() {
    if (cartCountSpan) {
        cartCountSpan.textContent = cart.length;
    }
}

// Function to save cart to localStorage
function saveCart() {
    localStorage.setItem('cityHardwareCart', JSON.stringify(cart));
    updateCartCount();
    // If on the full cart page, re-render after saving
    if (cartItemsContainer && cartItemsContainer.id === 'cartItemsList') {
        renderCart();
    }
}

// Function to add item to cart (called by individual product pages)
function addToCart(product) {
    cart.push(product);
    saveCart();
    alert(`${product.name} added to your quote request!`); // Simple feedback
}

// Function to render cart items in the modal or full cart page
function renderCart() {
    if (!cartItemsContainer) return; // Exit if container not found

    cartItemsContainer.innerHTML = ''; // Clear previous items
    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p>No items in your quote request yet.</p>';
        if (requestQuoteWhatsappBtn) requestQuoteWhatsappBtn.disabled = true;
        if (clearCartBtn) clearCartBtn.disabled = true;
        return;
    }
    if (requestQuoteWhatsappBtn) requestQuoteWhatsappBtn.disabled = false;
    if (clearCartBtn) clearCartBtn.disabled = false;

    cart.forEach((item, index) => {
        const itemDiv = document.createElement('div');
        itemDiv.classList.add('cart-item');

        // Handle different product detail structures
        let detailsHtml = '';
        if (item.specs) { // For Clearview Fence
            detailsHtml = item.specs.map(spec => `<li>${spec}</li>`).join('');
            if (item.priceGalvanized) detailsHtml += `<li>${item.priceGalvanized}</li>`;
            if (item.priceColourCoated) detailsHtml += `<li>${item.priceColourCoated}</li>`;
        } else if (item.details) { // For Quartz, Marble, Services
            detailsHtml = item.details.map(detail => `<li>${detail}</li>`).join('');
        }

        itemDiv.innerHTML = `
            <div class="cart-item-details">
                <h4>${item.name}</h4>
                <ul>${detailsHtml}</ul>
            </div>
            <div class="cart-item-actions">
                <button class="remove-from-cart" data-index="${index}">Remove</button>
            </div>
        `;
        cartItemsContainer.appendChild(itemDiv);
    });

    // Add event listeners for remove buttons
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', (event) => {
            const index = event.target.dataset.index;
            cart.splice(index, 1); // Remove item from cart array
            saveCart(); // Save and re-render
        });
    });
}

// Event listener for "View Cart" button (on product pages)
if (floatingCartButton) {
    floatingCartButton.addEventListener('click', () => {
        renderCart();
        if (cartModal) cartModal.style.display = 'block';
    });
}

// Event listener for closing the modal
if (closeButton) {
    closeButton.addEventListener('click', () => {
        if (cartModal) cartModal.style.display = 'none';
    });
}

// Close modal when clicking outside of it
if (cartModal) {
    window.addEventListener('click', (event) => {
        if (event.target === cartModal) {
            cartModal.style.display = 'none';
        }
    });
}


// Event listener for "Request Quote via WhatsApp" button
if (requestQuoteWhatsappBtn) {
    requestQuoteWhatsappBtn.addEventListener('click', () => {
        let message = "Hello City Hardware, I would like to request a quote for the following items:\n\n";
        if (cart.length === 0) {
            message += "No items selected.";
        } else {
            cart.forEach((item, index) => {
                message += `${index + 1}. ${item.name}\n`;
                if (item.specs) { // For Clearview Fence
                    item.specs.forEach(spec => {
                        message += `   - ${spec}\n`;
                    });
                    if (item.priceGalvanized) message += `   - ${item.priceGalvanized}\n`;
                    if (item.priceColourCoated) message += `   - ${item.priceColourCoated}\n`;
                } else if (item.details) { // For Quartz, Marble, Services
                    item.details.forEach(detail => {
                        message += `   - ${detail}\n`;
                    });
                }
                message += "\n";
            });
            message += "Please provide a detailed quote. Thank you!";
        }

        const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
        window.open(whatsappUrl, '_blank');
    });
}

// Event listener for "Clear Cart" button
if (clearCartBtn) {
    clearCartBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear your quote request?')) {
            cart = [];
            saveCart();
            renderCart();
        }
    });
}

// Initial update of cart count on page load (for product pages)
updateCartCount();

// Initial render of cart items on page load (for cart.html)
// This check ensures renderCart is only called if the cartItemsListContainer exists
// and is specifically the one for the full cart page.
if (cartItemsContainer && cartItemsContainer.id === 'cartItemsList') {
    renderCart();
}