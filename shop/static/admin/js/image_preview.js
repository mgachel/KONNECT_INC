// Live image preview when selecting a file in the admin product form
document.addEventListener('DOMContentLoaded', function () {
    // Find the file input for product_image (Cloudinary widget or standard file input)
    const fileInput = document.querySelector('input[name="product_image"]');
    if (!fileInput || fileInput.type !== 'file') return;

    fileInput.addEventListener('change', function () {
        if (!this.files || !this.files[0]) return;

        const file = this.files[0];
        if (!file.type.startsWith('image/')) return;

        const reader = new FileReader();
        reader.onload = function (e) {
            // Try to update the existing preview image
            let preview = document.querySelector('.field-image_preview img');
            if (preview) {
                preview.src = e.target.result;
            } else {
                // If no preview image exists yet, create one inside the preview container
                const container = document.querySelector('.field-image_preview .readonly');
                if (container) {
                    container.innerHTML =
                        '<img src="' + e.target.result + '" style="max-height:300px;max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15)" />';
                }
            }
        };
        reader.readAsDataURL(file);
    });
});
