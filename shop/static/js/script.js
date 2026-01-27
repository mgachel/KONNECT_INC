document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.category-tab');
    const productSections = document.querySelectorAll('.category-products');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const categoryId = this.getAttribute('data-category');

            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');

            // Hide all product sections
            productSections.forEach(section => section.classList.remove('active'));
            // Show the selected category's products
            document.querySelector(`.category-products[data-category="${categoryId}"]`).classList.add('active');
        });
    });
});