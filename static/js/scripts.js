document.addEventListener("DOMContentLoaded", function () {
    const sections = document.querySelectorAll("section");
    
    function revealOnScroll() {
        sections.forEach(section => {
            let windowHeight = window.innerHeight;
            let sectionTop = section.getBoundingClientRect().top;
            let sectionVisible = 150;
            if (sectionTop < windowHeight - sectionVisible) {
                section.classList.add("visible");
            }
        });
    }
    
    window.addEventListener("scroll", revealOnScroll);
    revealOnScroll();
    const lazyImages = document.querySelectorAll("img.lazyload");
    lazyImages.forEach(img => {
        img.addEventListener("load", () => img.classList.add("loaded"));
    });
});
