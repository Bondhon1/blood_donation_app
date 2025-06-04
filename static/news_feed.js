
let offset = 0;
const limit = 6;
let isLoading = false;
let hasMorePosts = true;

window.onload = () => {
    loadMoreRequests();
};

window.addEventListener("scroll", () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100) {
        loadMoreRequests();
    }
});

function loadMoreRequests() {
    if (isLoading || !hasMorePosts) return;

    isLoading = true;
    document.getElementById("loading-spinner").style.display = "block";

    fetch(`/api/news_feed?offset=${offset}&limit=${limit}`)
        .then(async response => {
            const contentType = response.headers.get("content-type");
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || "Unknown error");
            }
            if (!contentType || !contentType.includes("application/json")) {
                throw new Error("Invalid response format (expected JSON)");
            }
            return response.json();
        })
        .then(data => {
            if (data.requests.length > 0) {
                data.requests.forEach(request => {
                    document.getElementById("request-feed").innerHTML += createPostHTML(request);
                });
                offset += limit;
                hasMorePosts = data.has_more;
            } else {
                hasMorePosts = false;
            }
        })
        .catch(error => {
            console.error("Fetching:", error);
            showCustomModal({
                title: "Error",
                message: error.message || "An error occurred while fetching the posts.",
            });
        })
        .finally(() => {
            isLoading = false;
            document.getElementById("loading-spinner").style.display = "none";
        });
}


function getUrgencyClass(status) {
    return status === "Critical" ? "danger" : status === "Urgent" ? "warning" : "primary";
}

function createPostHTML(request) {
    console.log("Current User:", currentUser.username, "Is Donor:", currentUser.is_donor);
    let images = [];
    if (typeof request.images === "string" && request.images.trim() !== "") {
        images = request.images.split(",").map(img => img.trim()).filter(img => img !== "");
    }

    let donorStatus = request.donors_assigned >= request.amount_needed
        ? "All Donors Assigned"
        : request.donors_assigned > 0
            ? `${request.donors_assigned} out of ${request.amount_needed} Donors Assigned`
            : "No Donor Yet";

    let moreImages = images.length > 4 ? images.length - 4 : 0;
    let imagesHTML = "";

    if (images.length > 0) {
        imagesHTML = `
            <div class="post-images-container">
                ${images.slice(0, 4).map((img, index) => `
                    <div class="post-img-box">
                        <img src="/static/profile_pics/${img}" class="post-img" onclick="openSlider(${request.id}, ${index})">
                    </div>
                `).join('')}
                ${moreImages > 0 ? `
                    <div class="post-img-box more-images" onclick="openSlider(${request.id}, 0)">
                        +${moreImages} more
                    </div>
                ` : ""}
            </div>
        `;
    }

    // 🧠 Construct options menu
    let optionsMenuHTML = "";
    if (currentUser.username === request.user.username) {
        optionsMenuHTML = `
            <button onclick="editPost(${request.id})"><i class="fas fa-edit"></i> Edit</button>
            <button onclick="deletePost(${request.id})"><i class="fas fa-trash"></i> Delete</button>
            <button onclick="markDonorFound(${request.id})"><i class="fas fa-check"></i> Donor Found</button>
        `;
    } else {
        if (currentUser.is_donor) {
            optionsMenuHTML = `
                <button onclick="reportPost(${request.id})"><i class="fas fa-flag"></i> Report to Admin</button>
                <button onclick="requestResponseFromDonor(${request.id})"><i class="fas fa-hands-helping"></i> Request Response</button>
                <!-- Button in blood request card -->
                <button onclick="openReferDonorModal(${request.id})">
                <i class="fas fa-user-plus"></i> Refer a Donor
                </button>

            `;
        } else {
            optionsMenuHTML = `
                <button onclick="reportPost(${request.id})"><i class="fas fa-flag"></i> Report to Admin</button>
                <!-- Button in blood request card -->
                <button onclick="openReferDonorModal(${request.id})">
                <i class="fas fa-user-plus"></i> Refer a Donor
                </button>
            `;
        }
    }

    return `
        <div class="card shadow-sm post-card mb-3" data-id="${request.id}" data-images='${JSON.stringify(images)}'>
            <div class="post-options">
                <button class="options-btn" onclick="toggleOptionsMenu(${request.id})">
                    <i class="fas fa-ellipsis-v"></i>
                </button>
                <div class="options-menu" id="options-menu-${request.id}">
                    ${optionsMenuHTML}
                </div>
            </div>
            <div class="post-header d-flex align-items-center">
                <a href="/profile/${request.user.username}" class="fw-bold">
                    <img src="/static/profile_pics/${request.user.profile_picture}" class="post-profile-pic">
                </a>
                <div class="post-user-info">
                    <a href="/profile/${request.user.username}" class="fw-bold">${request.user.username}</a>
                    <div class="text-muted small">${convertToUserTime(request.created_at)}</div>
                </div>
            </div>
            <div class="post-body">
                <p><strong>Patient Name:</strong> ${request.patient_name}</p>
                <p><strong>Blood Group:</strong> ${request.blood_group}</p>
                <p><strong>Hospital:</strong> ${request.hospital_name}</p>
                <p><strong>Location:</strong> ${request.location}</p>
                <p><strong>Required Date:</strong> ${request.required_date}</p>
                <p><strong>Contact:</strong> ${request.contact_number}</p>
                <p><strong>Urgency:</strong> <span class="badge bg-${getUrgencyClass(request.urgency_status)}">${request.urgency_status}</span></p>
                <p><strong>Blood Needed:</strong> ${request.amount_needed} bag${request.amount_needed > 1 ? 's' : ''}</p>
                <p>${request.reason}</p>
                ${imagesHTML}
            </div>
            <div class="post-footer">
                <div class="status-bar ${request.status === 'Fulfilled' ? 'donor-assigned' : ''}">
                    <span id="assigned-donors-${request.id}">${donorStatus}</span>
                </div>
                <div class="post-actions">
                    <button class="upvote-btn" data-id="${request.id}" onclick="upvotePost(${request.id})">
                        <i class="fas fa-thumbs-up"></i> <span id="upvote-count-${request.id}">${request.upvotes || 0}</span>
                    </button>
                    <button class="comment-toggle-btn" onclick="toggleComments(${request.id})">
                        <i class="fas fa-comment"></i> Comments
                    </button>
                </div>
                <div class="comments-section" id="comments-${request.id}"></div>
            </div>
        </div>
    `;
}


function convertToUserTime(utcString) {
    const utcFixed = utcString.endsWith("Z") ? utcString : utcString + "Z";
    const date = new Date(utcFixed);
    return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
    });
}

let selectedRequestId = null;
let selectedDonorId = null;

function openReferDonorModal(requestId) {
  selectedRequestId = requestId;
  document.getElementById("referDonorModal").style.display = "block";
  document.getElementById("donorSearchResults").innerHTML = "";
}

function closeReferDonorModal() {
  document.getElementById("referDonorModal").style.display = "none";
  selectedDonorId = null;
}

function searchDonors() {
  const query = document.getElementById("donorSearchInput").value;
  if (!query) return;

  fetch(`/api/search_donors?query=${encodeURIComponent(query)}&request_id=${selectedRequestId}`)
    .then(response => response.json()) // 🔥 parse JSON properly here
    .then(data => {
      console.log("Donor Search Results:", data);
      const container = document.getElementById("donorSearchResults");
      if (!data.results || data.results.length === 0) {
          container.innerHTML = "<div>No donors found.</div>";
          return;
      }
      container.innerHTML = data.results.map(d => `
        <div class="donor-card" data-id="${d.id}" onclick="selectDonor(${d.id})">
            <img src="/static/profile_pics/${d.profile_picture}" width="30"> 
            <b>${d.name || d.username}</b> - ${d.blood_group}
            <small>Last donation: ${d.last_donation_date || 'N/A'}</small>
        </div>
        `).join("");

    })
    .catch(error => {
      console.error("Error fetching donors:", error);
    });
}


function selectDonor(donorId) {
  selectedDonorId = donorId;
  document.querySelectorAll(".donor-card").forEach(el => el.classList.remove("selected"));
  const selectedCard = document.querySelector(`.donor-card[data-id="${donorId}"]`);
  if (selectedCard) {
    selectedCard.classList.add("selected");
  }
}


function submitDonorReferral() {
  if (!selectedDonorId || !selectedRequestId) return;

  fetch(`/api/refer_donor`, {
    method: "POST",
    headers: { 'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
     },
    body: JSON.stringify({ donor_id: selectedDonorId, request_id: selectedRequestId })
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message);
      closeReferDonorModal();
    });
}

function upvotePost(postId) {
    fetch(`/upvote_request/${postId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            document.getElementById(`upvote-count-${postId}`).innerText = data.upvotes;

            let upvoteBtn = document.querySelector(`.upvote-btn[data-id="${postId}"]`);
            if (upvoteBtn) {
                upvoteBtn.classList.toggle("upvoted");
            }
        } else {
            showCustomModal({
                title: "Error",
                message: data.error || "Unknown error occurred",
                onConfirm: () => {}
            });
        }
    })
    .catch(error => {
        console.error("Error upvoting post:", error);
        showCustomModal({
            title: "Upvote Failed",
            message: error.message || "Something went wrong.",
            onConfirm: () => {}
        });
    });
}




function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function requestResponseFromDonor(requestId) {
    showCustomModal({
        title: "Confirm Donation",
        message: "Are you sure you want to respond to this blood request?",
        onConfirm: () => {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

            fetch(`/donor_response/${requestId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({})
            })
            .then(res => {
                if (!res.ok) throw new Error("Network response was not ok");
                return res.json();
            })
            .then(data => {
                if (data.status === "success") {
                    // ✅ Update donor status UI
                    const statusText = data.donors_assigned >= data.amount_needed
                        ? "All Donors Assigned"
                        : `${data.donors_assigned} out of ${data.amount_needed} Donors Assigned`;

                    const statusElem = document.getElementById(`assigned-donors-${requestId}`);
                    if (statusElem) {
                        statusElem.textContent = statusText;
                    }

                    // ✅ Optional: mark card as fulfilled
                    if (data.donors_assigned >= data.amount_needed) {
                        document.getElementById(`request-${requestId}`)?.classList.add("fulfilled");
                    }

                    // ✅ Optional: disable or change the "Request Response" button
                    const optionsMenu = document.getElementById(`options-menu-${requestId}`);
                    if (optionsMenu) {
                        optionsMenu.innerHTML = `
                            <button disabled><i class="fas fa-check-circle"></i> You responded</button>
                        `;
                    }

                    // ✅ Show thank you modal
                    showCustomModal({
                        title: "Thank you!",
                        message: data.message
                    });

                } else {
                    showCustomModal({
                        title: "Notice",
                        message: data.message
                    });
                }
            })
            .catch(err => {
                console.error("Error:", err);
                alert("Something went wrong. Try again later.");
            });
        }
    });
}




function checkFulfilled(request) {
    if (request.donors_assigned >= request.amount_needed) {
        document.getElementById(`request-${request.id}`).classList.add("fulfilled");
    }
}

function reportPost(requestId) {
  showCustomModal({
    title: "Report Blood Request",
    message: "Are you sure you want to report this blood request to the admin?",
    onConfirm: () => {
      const csrfToken = getCSRFToken();

      fetch('/api/report_post', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ request_id: requestId })
      })
      .then(res => res.json())
      .then(data => {
        alert(data.message);
      })
      .catch(err => {
        console.error("Error reporting post:", err);
        alert("Something went wrong.");
      });
    }
  });
}

