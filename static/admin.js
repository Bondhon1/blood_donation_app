
document.addEventListener("DOMContentLoaded", function() {
    const menuBtn = document.getElementById("menu-btn");
    const sidebar = document.querySelector(".sidebar");

    menuBtn.addEventListener("click", function() {
        sidebar.classList.toggle("active");

        // Move button when sidebar is open/closed
        if (sidebar.classList.contains("active")) {
            menuBtn.style.left = "230px";
        } else {
            menuBtn.style.left = "10px";
        }
    });
});
