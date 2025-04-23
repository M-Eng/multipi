document.addEventListener('DOMContentLoaded', function() {
    const imageContainers = document.querySelectorAll('.pi-image img');

    // Handle hover and click for each image
    imageContainers.forEach(img => {
        img.addEventListener('click', enlargeImage);
    });

    // Close enlarged image when the overlay is clicked
    document.getElementById('imageOverlay').addEventListener('click', function() {
        this.style.display = 'none';
    });
});

function enlargeImage(event) {
    const enlargedImg = document.getElementById('enlargedImage');
    enlargedImg.src = event.target.src;  // Set the source for the enlarged image
    document.getElementById('imageOverlay').style.display = 'block';  // Display the overlay
}