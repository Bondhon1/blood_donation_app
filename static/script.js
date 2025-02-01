document.addEventListener("DOMContentLoaded", function () {
    // Search Box
    document.getElementById("searchBox").addEventListener("input", function () {
        let query = this.value;
        let searchResults = document.getElementById("searchResults");

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

    // Toggle Dropdowns
    function toggleDropdown(buttonId, popupId) {
        document.getElementById(buttonId).addEventListener("click", function (event) {
            let popup = document.getElementById(popupId);
            popup.style.display = (popup.style.display === "block") ? "none" : "block";
            event.stopPropagation(); // Prevent closing immediately
        });
    }

    toggleDropdown("notifBtn", "notifPopup");
    toggleDropdown("profileBtn", "profilePopup");

    // Hide popups when clicking outside
    document.addEventListener("click", function (event) {
        if (!event.target.closest("#notifBtn") && !event.target.closest("#notifPopup")) {
            document.getElementById("notifPopup").style.display = "none";
        }
        if (!event.target.closest("#profileBtn") && !event.target.closest("#profilePopup")) {
            document.getElementById("profilePopup").style.display = "none";
        }
    });
});
