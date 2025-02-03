document.addEventListener("DOMContentLoaded", function () {
    // 🔹 Search Box Functionality
    let searchBox = document.getElementById("searchBox");
    let searchResults = document.getElementById("searchResults");

    if (searchBox) {
        searchBox.addEventListener("input", function () {
            let query = this.value.trim();

            if (query.length > 2) {
                searchResults.innerHTML = "<p>Searching...</p>";
                searchResults.style.display = "block";

                setTimeout(() => {
                    searchResults.innerHTML = `<p>Result for "${query}"</p>`;
                }, 500);
            } else {
                searchResults.style.display = "none";
            }
        });
    }

    // 🔹 Notifications Popup
    let notifBtn = document.getElementById("notifBtn");
    let notifPopup = document.getElementById("notifPopup");

    if (notifBtn && notifPopup) {
        notifBtn.addEventListener("click", function (event) {
            event.stopPropagation();
            notifPopup.classList.toggle("show");
        });
    }

    // 🔹 Profile Popup
    let profileBtn = document.getElementById("profileBtn");
    let profilePopup = document.getElementById("profilePopup");

    if (profileBtn && profilePopup) {
        profileBtn.addEventListener("click", function (event) {
            event.stopPropagation();
            profilePopup.classList.toggle("show");
        });
    }

    // 🔹 Hide popups when clicking outside
    document.addEventListener("click", function (event) {
        if (notifBtn && notifPopup && !notifBtn.contains(event.target) && !notifPopup.contains(event.target)) {
            notifPopup.classList.remove("show");
        }
        if (profileBtn && profilePopup && !profileBtn.contains(event.target) && !profilePopup.contains(event.target)) {
            profilePopup.classList.remove("show");
        }
    });

    // 🔹 Auto-Close Navbar on Mobile after clicking a link
    let navbarToggler = document.querySelector(".navbar-toggler");
    let navbarCollapse = document.querySelector(".navbar-collapse");
    let navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach(link => {
        link.addEventListener("click", function () {
            if (window.innerWidth < 992) {  // Close only on mobile screens
                navbarToggler.click();
            }
        });
    });
});
