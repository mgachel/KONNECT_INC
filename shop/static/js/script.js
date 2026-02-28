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

    // === Video Play / Back-to-Image Logic ===
    document.querySelectorAll('.play-video-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const media = this.closest('.product-media');
            const img = media.querySelector('img');
            const video = media.querySelector('.product-video');
            const downloadBtn = media.querySelector('.download-video-btn');

            if (!video) return;

            // Load the video source from data-source if not already loaded
            if (!video.src || video.src === window.location.href) {
                video.src = video.getAttribute('data-source');
            }

            // Toggle: if video is currently visible, go back to image
            if (video.classList.contains('active')) {
                video.pause();
                video.classList.remove('active');
                img.classList.remove('hidden');
                this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>';
                this.title = 'Play video';
                return;
            }

            // Show video, hide image
            video.classList.add('active');
            img.classList.add('hidden');
            this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';
            this.title = 'Back to image';
            video.play();

            // When video ends, switch back to image
            video.onended = function() {
                video.classList.remove('active');
                img.classList.remove('hidden');
                btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>';
                btn.title = 'Play video';
            };
        });
    });
});