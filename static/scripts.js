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
            if (window.innerWidth < 992 && navbarToggler) {
                navbarToggler.click();
            }
        });
    });

    // 🔹 Dark Mode Toggle
    let darkModeToggle = document.getElementById("darkModeToggle");
    let body = document.body;

    if (darkModeToggle) {
        if (localStorage.getItem("darkMode") === "enabled") {
            body.classList.add("dark-mode");
            darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }

        darkModeToggle.addEventListener("click", function () {
            body.classList.toggle("dark-mode");

            if (body.classList.contains("dark-mode")) {
                darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                localStorage.setItem("darkMode", "enabled");
            } else {
                darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                localStorage.setItem("darkMode", "disabled");
            }
        });
    }  
    
});
// 🔹 Custom Mobile Menu Toggle
let burgerButton = document.getElementById("mobileMenuToggle");
let mobileMenu = document.getElementById("customMobileMenu");

if (burgerButton && mobileMenu) {
    burgerButton.addEventListener("click", function (e) {
        e.stopPropagation();
        mobileMenu.classList.toggle("show");
    });

    document.addEventListener("click", function (e) {
        if (!burgerButton.contains(e.target) && !mobileMenu.contains(e.target)) {
            mobileMenu.classList.remove("show");
        }
    });
}
function showCustomModal({ title = "", message = "", input = false, onConfirm, onCancel }) {
    const modal = document.getElementById("customModal");
    const modalTitle = document.getElementById("customModalTitle");
    const modalMessage = document.getElementById("customModalMessage");
    const inputField = document.getElementById("customModalInput");
    const okBtn = document.getElementById("customModalOkBtn");
    const cancelBtn = document.getElementById("customModalCancelBtn");

    modalTitle.textContent = title;
    modalMessage.textContent = message;

    inputField.style.display = input ? "block" : "none";
    inputField.value = "";

    modal.style.display = "flex";

    okBtn.onclick = () => {
        const inputValue = input ? inputField.value : null;
        modal.style.display = "none";
        if (onConfirm) onConfirm(inputValue);
    };

    cancelBtn.onclick = () => {
        modal.style.display = "none";
        if (onCancel) onCancel();
    };
}
document.addEventListener("DOMContentLoaded", function () {
    // Ensure slider exists in the DOM
    if (!document.getElementById("image-slider")) {
        const sliderDiv = document.createElement("div");
        sliderDiv.id = "image-slider";
        sliderDiv.className = "image-slider";
        document.body.appendChild(sliderDiv);
    }

    // Close slider when clicking outside the image
    document.getElementById("image-slider").addEventListener("click", function (event) {
        if (event.target.id === "image-slider") {
            closeSlider();
        }
    });
});

let currentImageIndex = 0;
let sliderImages = [];

// Function to open the image slider
function openSlider(postId, index) {
    const post = document.querySelector(`.post-card[data-id='${postId}']`);
    
    // Retrieve all images for this post
    const images = JSON.parse(post.getAttribute("data-images")); // Get full image list from attribute
    
    sliderImages = images;  // Store all images
    currentImageIndex = index;  // Start from clicked image
    
    const slider = document.getElementById("image-slider");
    updateSliderImage();

    slider.style.display = "flex";
}

// Function to update the slider image
function updateSliderImage() {
    const sliderContent = document.getElementById("slider-content");
    sliderContent.innerHTML = `
        <span class="close-btn" onclick="closeSlider()">&times;</span>
        <button class="nav-btn prev-btn" onclick="prevImage()">&#10094;</button>
        <img id="slider-img" src="/static/profile_pics/${sliderImages[currentImageIndex]}" class="slider-img">
        <button class="nav-btn next-btn" onclick="nextImage()">&#10095;</button>
        <div class="zoom-controls">
            <button onclick="zoomIn()">+</button>
            <button onclick="zoomOut()">-</button>
        </div>
    `;
}

// Function to show the previous image
function prevImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        updateSliderImage();
    }
}

// Function to show the next image
function nextImage() {
    if (currentImageIndex < sliderImages.length - 1) {
        currentImageIndex++;
        updateSliderImage();
    }
}

// Function to close the slider
function closeSlider() {
    document.getElementById("image-slider").style.display = "none";
}

// Function to zoom in
function zoomIn() {
    const img = document.getElementById("slider-img");
    img.style.transform = `scale(${parseFloat(img.style.transform.replace("scale(", "").replace(")", "")) + 0.2 || 1.2})`;
}

// Function to zoom out
function zoomOut() {
    const img = document.getElementById("slider-img");
    img.style.transform = `scale(${Math.max(parseFloat(img.style.transform.replace("scale(", "").replace(")", "")) - 0.2 || 0.8, 0.8)})`;
}

// Keyboard navigation
document.addEventListener("keydown", function (event) {
    if (document.getElementById("image-slider").style.display === "flex") {
        if (event.key === "ArrowLeft") {
            prevImage();
        } else if (event.key === "ArrowRight") {
            nextImage();
        } else if (event.key === "Escape") {
            closeSlider();
        }
    }
});
function reloadComments(requestId) {
    const commentsSection = document.getElementById(`comments-${requestId}`);
    if (!commentsSection) return;

    commentsSection.innerHTML = "";

    fetch(`/get_comments/${requestId}`)
        .then(res => res.json())
        .then(data => {
            commentsSection.innerHTML = data.comments.map(comment => createCommentHTML(comment, requestId)).join('');
            commentsSection.innerHTML += `
                <div class="comment-input d-flex align-items-center gap-2 mt-3">
                    <label for="comment-image-${requestId}" class="btn btn-outline-secondary p-2 d-flex align-items-center justify-content-center" style="height: 38px; width: 38px;">
                        <i class="bi bi-camera"></i>
                    </label>
                    <input type="file" accept="image/*" id="comment-image-${requestId}" style="display:none">
                    
                    <input type="text" id="comment-text-${requestId}" class="form-control" placeholder="Write a comment...">

                    <button onclick="submitComment(${requestId})" class="btn btn-danger">Post</button>
                </div>

                <div class="preview-container" id="preview-wrapper-${requestId}" style="display:none;">
                    <img id="preview-comment-img-${requestId}">
                    <button class="remove-preview-btn" onclick="removeCommentPreview(${requestId})">×</button>
                </div>


            `;
            addCommentImagePreviewListener(requestId);
            document.getElementById(`comment-text-${requestId}`).addEventListener("keydown", function (event) {
                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    submitComment(requestId);
                }
            });
        });
}

function addCommentImagePreviewListener(requestId) {
    const input = document.getElementById(`comment-image-${requestId}`);
    const preview = document.getElementById(`preview-comment-img-${requestId}`);
    const wrapper = document.getElementById(`preview-wrapper-${requestId}`);

    if (!input || !preview || !wrapper) {
        console.warn(`Comment preview elements not found for requestId: ${requestId}`);
        return;
    }

    input.addEventListener("change", () => {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = e => {
                preview.src = e.target.result;
                wrapper.style.display = "flex";
            };
            reader.readAsDataURL(input.files[0]);
        }
    });
}


function removeCommentPreview(requestId) {
    const input = document.getElementById(`comment-image-${requestId}`);
    const preview = document.getElementById(`preview-comment-img-${requestId}`);
    const wrapper = document.getElementById(`preview-wrapper-${requestId}`);
    
    input.value = "";
    preview.src = "";
    wrapper.style.display = "none";
}

let isSubmittingComment = false;

function submitComment(requestId) {
    if (isSubmittingComment) return;
    isSubmittingComment = true;

    const text = document.getElementById(`comment-text-${requestId}`).value;
    const imageInput = document.getElementById(`comment-image-${requestId}`);
    const formData = new FormData();

    formData.append("text", text || "");
    if (imageInput && imageInput.files.length > 0) {
        formData.append("image", imageInput.files[0]);
    }

    fetch(`/add_comment/${requestId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) reloadComments(requestId);
    })
    .finally(() => {
        isSubmittingComment = false;
    });
}



function toggleComments(requestId) {
    const commentsSection = document.getElementById(`comments-${requestId}`);
    
    if (commentsSection.innerHTML !== "") {
        commentsSection.innerHTML = ""; // Hide comments
        return;
    }

    fetch(`/get_comments/${requestId}`)
        .then(res => res.json())
        .then(data => {
            commentsSection.innerHTML = data.comments.map(comment => createCommentHTML(comment, requestId)).join('');

            commentsSection.innerHTML += `
                <div class="comment-input d-flex align-items-center gap-2 mt-3">
                    <label for="comment-image-${requestId}" class="btn btn-outline-secondary p-2 d-flex align-items-center justify-content-center" style="height: 38px; width: 38px;">
                        <i class="bi bi-camera"></i>
                    </label>
                    <input type="file" accept="image/*" id="comment-image-${requestId}" style="display:none">
                    
                    <input type="text" id="comment-text-${requestId}" class="form-control" placeholder="Write a comment...">
                    

                    <button onclick="submitComment(${requestId})" class="btn btn-danger">Post</button>
                </div>

                <div class="preview-container" id="preview-wrapper-${requestId}" style="display:none;">
                    <img id="preview-comment-img-${requestId}">
                    <button class="remove-preview-btn" onclick="removeCommentPreview(${requestId})">×</button>
                </div>


            `;

            addCommentImagePreviewListener(requestId);
            document.getElementById(`comment-text-${requestId}`).addEventListener("keydown", function (event) {
                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    submitComment(requestId);
                }
            });
        });
}

function createCommentHTML(comment, requestId) {
    const isValidImage = (img) => {
        return typeof img === 'string' && img.trim() !== "" && img.trim().toLowerCase() !== "none";
    };

    const repliesHTML = comment.replies.map(reply => {
        const replyProfileImg = isValidImage(reply.profile_picture)
            ? `<img src="/static/profile_pics/${reply.profile_picture}" class="comment-avatar me-2">`
            : `<div class="comment-avatar placeholder-avatar me-2"></div>`;

        const replyContentImg = isValidImage(reply.image)
            ? `<img src="/static/profile_pics/${reply.image}" class="comment-img">`
            : "";

        return `
            <div class="reply d-flex ms-4 mt-3 align-items-start">
                ${replyProfileImg}
                <div class="d-flex flex-column flex-md-row align-items-start">
                    <div class="user-info me-2 text-start">
                        <a href="/profile/${reply.username}" class="username d-block">${reply.username}</a>
                        <div class="timestamp">${convertToUserTime(reply.created_at)}</div>
                    </div>
                    <div class="comment-bubble">
                        <div class="comment-text">${reply.text}</div>
                        ${replyContentImg}
                        <div class="comment-actions d-flex align-items-center mt-1">
                            <button class="btn btn-sm btn-outline-danger like-btn me-2" data-comment-id="${reply.id}">
                                <i class="fa fa-heart"></i> <span class="like-count">${reply.like_count}</span>
                            </button>
                        </div>
                        <div class="comment-options">
                            <i class="fa fa-ellipsis-v" onclick="toggleOptions(this)"></i>
                            <div class="options-dropdown">
                                <a href="#" onclick="editComment(${reply.id})">Edit</a>
                                <a href="#" onclick="deleteComment(${reply.id})">Delete</a>
                                <a href="#" onclick="reportComment(${reply.id})">Report to Admin</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    const commentProfileImg = isValidImage(comment.profile_picture)
        ? `<img src="/static/profile_pics/${comment.profile_picture}" class="comment-avatar me-2">`
        : `<div class="comment-avatar placeholder-avatar me-2"></div>`;

    const commentContentImg = isValidImage(comment.image)
        ? `<img src="/static/profile_pics/${comment.image}" class="comment-img">`
        : "";

    return `
        <div class="comment mt-3">
            <div class="d-flex align-items-start">
                ${commentProfileImg}
                <div class="d-flex flex-column flex-md-row align-items-start">
                    <div class="user-info me-2 text-start">
                        <a href="/profile/${comment.username}" class="username d-block">${comment.username}</a>
                        <div class="timestamp">${convertToUserTime(comment.created_at)}</div>
                    </div>
                    <div class="comment-bubble">
                        <div class="comment-text">${comment.text}</div>
                        ${commentContentImg}
                        <div class="comment-actions d-flex align-items-center mt-1">
                            <button class="btn btn-sm btn-outline-danger like-btn me-2" data-comment-id="${comment.id}">
                                <i class="fa fa-heart"></i> <span class="like-count">${comment.like_count}</span>
                            </button>
                        </div>

                        <a href="javascript:void(0);" onclick="showReplyInput(${comment.id}, ${requestId})" class="reply-link">Reply</a>
                        <div class="comment-options">
                            <i class="fa fa-ellipsis-v" onclick="toggleOptions(this)"></i>
                            <div class="options-dropdown">
                                <a href="#" onclick="editComment(${comment.id})">Edit</a>
                                <a href="#" onclick="deleteComment(${comment.id})">Delete</a>
                                <a href="#" onclick="reportComment(${comment.id})">Report to Admin</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="replies w-100 mt-2 ms-4" id="replies-${comment.id}">
                ${repliesHTML}
            </div>
        </div>
    `;
}

function toggleOptions(icon) {
  const dropdown = icon.nextElementSibling;
  document.querySelectorAll('.options-dropdown').forEach(el => {
    if (el !== dropdown) el.style.display = 'none';
  });
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// Optional: close on click outside
document.addEventListener('click', function(e) {
  if (!e.target.closest('.comment-options')) {
    document.querySelectorAll('.options-dropdown').forEach(el => el.style.display = 'none');
  }
});
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('.like-btn').forEach(button => {
      button.addEventListener('click', function () {
        const commentId = this.getAttribute('data-comment-id');

        fetch(`/like_comment/${commentId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'  // if CSRF protection is used
          }
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            this.querySelector('.like-count').innerText = data.likes;
            this.classList.toggle('btn-outline-danger');
            this.classList.toggle('btn-danger');
          }
        });
      });
    });
  });


function showReplyInput(commentId, requestId) {
    const existingInput = document.getElementById(`reply-input-${commentId}`);
    if (existingInput) {
        existingInput.parentElement.remove(); // Close input if open
        return;
    }

    const replyContainer = document.getElementById(`replies-${commentId}`);
    const inputBox = document.createElement('div');
    inputBox.classList.add("mt-2");

    inputBox.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <label for="reply-image-${commentId}" class="btn btn-outline-secondary p-2 d-flex align-items-center justify-content-center" style="height: 38px; width: 38px;">
                <i class="bi bi-camera"></i>
            </label>
            <input type="file" accept="image/*" id="reply-image-${commentId}" style="display:none">
            <input type="text" id="reply-input-${commentId}" class="form-control" placeholder="Write a reply...">
            <button class="btn btn-danger" onclick="submitReply(${commentId}, ${requestId})">Reply</button>
        </div>
        <div class="preview-container" id="preview-reply-wrapper-${commentId}" style="display:none;">
            <img id="preview-reply-img-${commentId}">
            <button class="remove-preview-btn" onclick="removeReplyPreview(${commentId})">×</button>
        </div>


    `;

    replyContainer.appendChild(inputBox);
    addReplyImagePreviewListener(commentId);
    document.getElementById(`reply-input-${commentId}`).addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            submitReply(commentId, requestId);
        }
    });

}


function addReplyImagePreviewListener(commentId) {
    const input = document.getElementById(`reply-image-${commentId}`);
    const preview = document.getElementById(`preview-reply-img-${commentId}`);
    const wrapper = document.getElementById(`preview-reply-wrapper-${commentId}`);

    input.addEventListener("change", () => {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = e => {
                preview.src = e.target.result;
                wrapper.style.display = "flex";
            };
            reader.readAsDataURL(input.files[0]);
        }
    });
}

function removeReplyPreview(commentId) {
    const input = document.getElementById(`reply-image-${commentId}`);
    const preview = document.getElementById(`preview-reply-img-${commentId}`);
    const wrapper = document.getElementById(`preview-reply-wrapper-${commentId}`);

    input.value = "";
    preview.src = "";
    wrapper.style.display = "none";
}



function submitReply(commentId, requestId) {
    const textInput = document.getElementById(`reply-input-${commentId}`);
    const imageInput = document.getElementById(`reply-image-${commentId}`);
    const formData = new FormData();

    formData.append("text", textInput.value);
    if (imageInput && imageInput.files.length > 0) {
        formData.append("image", imageInput.files[0]);
    }

    fetch(`/add_reply/${commentId}`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken()
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            reloadComments(requestId);
        }
    });
}
function toggleOptionsMenu(postId) {
    const menu = document.getElementById(`options-menu-${postId}`);
    
    // Hide all other menus
    document.querySelectorAll('.options-menu').forEach(menu => menu.style.display = 'none');

    // Toggle current menu
    if (menu.style.display === 'block') {
        menu.style.display = 'none';
    } else {
        menu.style.display = 'block';
    }
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.post-options')) {
        document.querySelectorAll('.options-menu').forEach(menu => menu.style.display = 'none');
    }
});
function editPost(postId) {
    
    fetch(`/get_post/${postId}`)
        .then(response => response.json())
        .then(post => {
            let imagesHTML = post.images.map(img => `
                <div class="edit-img-box">
                    <img src="/static/profile_pics/${img}" class="edit-post-img">
                    <button class="remove-img-btn" onclick="removeImage('${img}')">X</button>
                </div>
            `).join("");

            const editForm = `
                <div id="editModal" class="modal">
                    <div class="modal-content">
                        <span class="close" onclick="closeEditModal()">&times;</span>
                        <h3>Edit Blood Request</h3>
                        <label>Patient Name:</label>
                        <input type="text" id="editPatientName" value="${post.patient_name || ''}">
                        
                        <label>Blood Group:</label>
                        <select id="editBloodGroup">
                            <option value="A+">A+</option>
                            <option value="A-">A-</option>
                            <option value="B+">B+</option>
                            <option value="B-">B-</option>
                            <option value="O+">O+</option>
                            <option value="O-">O-</option>
                            <option value="AB+">AB+</option>
                            <option value="AB-">AB-</option>
                        </select>

                        <label>Number of Blood Bags:</label>
                        <input type="number" id="editAmountNeeded" value="${post.amount_needed || 1}" min="1">
                        
                        <label>Hospital Name:</label>
                        <input type="text" id="editHospitalName" value="${post.hospital_name || ''}">
                        
                        <label>Required Date & Time:</label>
                        <input type="datetime-local" id="editRequiredDate" value="${post.required_date || ''}">
                        
                        <label>Urgency Status:</label>
                        <select id="editUrgencyStatus">
                            <option value="Critical">Critical</option>
                            <option value="Urgent">Urgent</option>
                            <option value="Normal">Normal</option>
                        </select>
                        
                        <label>Reason for Request:</label>
                        <textarea id="editReason">${post.reason || ''}</textarea>

                        <label>Uploaded Images:</label>
                        <div id="existingImages">${imagesHTML}</div>

                        <label for="editImages" class="custom-file-upload">
                        📷 Upload Images
                        </label>
                        <input type="file" id="editImages" name="images" multiple accept="image/*" style="display: none;">
                        <div class="preview-container" id="editImagePreviews"></div>


                        <button onclick="savePostEdit(${postId})">Save Changes</button>
                        <button onclick="closeEditModal()">Cancel</button>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML("beforeend", editForm);
            document.getElementById("editModal").style.display = "block";
            setupImagePreview();
            removedImages = []; // Reset when modal opens

            // ✅ Set selected values explicitly after rendering
            document.getElementById("editBloodGroup").value = post.blood_group || '';
            document.getElementById("editUrgencyStatus").value = post.urgency_status || '';
        });
        function setupImagePreview() {
            const editImageInput = document.getElementById("editImages");
            const previewContainer = document.getElementById("editImagePreviews");

            if (!editImageInput || !previewContainer) return;

            let selectedFiles = [];

            editImageInput.addEventListener("change", function () {
                const newFiles = Array.from(editImageInput.files);

                newFiles.forEach((file) => {
                    // Avoid duplicates by filename (optional)
                    if (selectedFiles.some(f => f.name === file.name)) return;

                    selectedFiles.push(file);

                    const reader = new FileReader();
                    reader.onload = function (e) {
                        const previewDiv = document.createElement("div");
                        previewDiv.classList.add("image-preview");

                        const img = document.createElement("img");
                        img.src = e.target.result;

                        const removeBtn = document.createElement("button");
                        removeBtn.classList.add("remove-preview");
                        removeBtn.innerHTML = "×";
                        removeBtn.onclick = function () {
                            // Remove this file from selectedFiles
                            selectedFiles = selectedFiles.filter(f => f !== file);
                            previewDiv.remove();

                            // Update input files
                            const dt = new DataTransfer();
                            selectedFiles.forEach(f => dt.items.add(f));
                            editImageInput.files = dt.files;
                        };

                        previewDiv.appendChild(img);
                        previewDiv.appendChild(removeBtn);
                        previewContainer.appendChild(previewDiv);
                    };
                    reader.readAsDataURL(file);
                });

                // Update input files with combined selection
                const dt = new DataTransfer();
                selectedFiles.forEach(f => dt.items.add(f));
                editImageInput.files = dt.files;
            });
        }
        
    
}


// Function to remove an image from edit form
let removedImages = [];

function removeImage(imageName) {
    removedImages.push(imageName);
    document.querySelector(`img[src='/static/profile_pics/${imageName}']`).parentElement.remove();
}
function savePostEdit(postId) {
    const updatedData = new FormData();
    updatedData.append("patient_name", document.getElementById("editPatientName").value);
    updatedData.append("blood_group", document.getElementById("editBloodGroup").value);
    updatedData.append("amount_needed", document.getElementById("editAmountNeeded").value);
    updatedData.append("hospital_name", document.getElementById("editHospitalName").value);
    updatedData.append("required_date", document.getElementById("editRequiredDate").value);
    updatedData.append("urgency_status", document.getElementById("editUrgencyStatus").value);
    updatedData.append("reason", document.getElementById("editReason").value);
    updatedData.append("removed_images", JSON.stringify(removedImages));

    const images = document.getElementById("editImages").files;
    for (let i = 0; i < images.length; i++) {
        updatedData.append("images", images[i]);
    }

    const saveButton = document.querySelector("#editModal button[onclick^='savePostEdit']");
    const originalText = saveButton.innerText;
    saveButton.innerText = "Saving...";
    saveButton.disabled = true;

    fetch(`/edit_post/${postId}`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken()
        },
        body: updatedData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showCustomModal({
                title: "Success",
                message: data.message,
                onConfirm: () => {}
            });

            // ✅ Live update the post DOM
            const postCard = document.querySelector(`.post-card[data-id="${postId}"]`);
            if (postCard) {
                postCard.querySelector(".post-body").innerHTML = `
                    <p><strong>Patient Name:</strong> ${data.updated.patient_name}</p>
                    <p><strong>Blood Group:</strong> ${data.updated.blood_group}</p>
                    <p><strong>Hospital:</strong> ${data.updated.hospital_name}</p>
                    <p><strong>Urgency:</strong> <span class="badge bg-${getUrgencyClass(data.updated.urgency_status)}">${data.updated.urgency_status}</span></p>
                    <p><strong>Blood Needed:</strong> ${data.updated.amount_needed} bag${data.updated.amount_needed > 1 ? 's' : ''} (${data.updated.amount_needed} donor${data.updated.amount_needed > 1 ? 's' : ''} needed)</p>
                    <p>${data.updated.reason}</p>
                    ${createImagesHTML(data.updated.images, postId)}
                `;

                postCard.setAttribute("data-images", JSON.stringify(data.updated.images));
            }

            // ✅ Update the modal inputs (optional, in case user opens it again)
            document.getElementById("editPatientName").value = data.updated.patient_name;
            document.getElementById("editBloodGroup").value = data.updated.blood_group;
            document.getElementById("editAmountNeeded").value = data.updated.amount_needed;
            document.getElementById("editHospitalName").value = data.updated.hospital_name;
            document.getElementById("editRequiredDate").value = data.updated.required_date;
            document.getElementById("editUrgencyStatus").value = data.updated.urgency_status;
            document.getElementById("editReason").value = data.updated.reason;

            // ✅ Update images in the modal preview
            if (document.getElementById("existingImages")) {
                const existingImages = document.getElementById("existingImages");
                existingImages.innerHTML = data.updated.images.map(img => `
                    <div class="edit-img-box">
                        <img src="/static/profile_pics/${img}" class="edit-post-img">
                        <button class="remove-img-btn" onclick="removeImage('${img}')">X</button>
                    </div>
                `).join("");
            }

            removedImages = [];  // Clear removed list
            closeEditModal();
        } else {
            showCustomModal({
                title: "Update Failed",
                message: "Failed to update the post. ",
                onConfirm: () => {}
            });
        }
    })
    .catch(error => {
        console.error("Update error:", error);
        showCustomModal({
            title: "Error",
            message: "Something went wrong while saving the post.",
            onConfirm: () => {}
        });
    })
    .finally(() => {
        saveButton.innerText = originalText;
        saveButton.disabled = false;
    });
}
function createImagesHTML(images, postId) {
    const moreImages = images.length > 4 ? images.length - 4 : 0;
    let html = `
        <div class="post-images-container">
            ${images.slice(0, 4).map((img, index) => `
                <div class="post-img-box">
                    <img src="/static/profile_pics/${img}" class="post-img" onclick="openSlider(${postId}, ${index})">
                </div>
            `).join('')}
            ${moreImages > 0 ? `
                <div class="post-img-box more-images" onclick="openSlider(${postId}, 0)">
                    +${moreImages} more
                </div>
            ` : ""}
        </div>
    `;
    return html;
}
function closeEditModal() {
    const modal = document.getElementById("editModal");
    if (modal) {
        modal.remove();
    }
}
function closeEditModal() {
    document.getElementById("editModal").remove();
}

function deletePost(postId) {
    if (!confirm("Are you sure you want to delete this post?")) return;

    fetch(`/delete_post/${postId}`, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Post deleted successfully") {
            showCustomModal({
                title: "Success",
                message: data.message,
                onConfirm: () => {}
            });
            const postElement = document.querySelector(`.post-card[data-id='${postId}']`);
            if (postElement) {
                postElement.style.transition = "opacity 0.3s ease";
                postElement.style.opacity = "0";
                setTimeout(() => postElement.remove(), 300);
            }
        } else {
            showCustomModal({
                title: "Delete Failed",
                message: data.message || "Failed to delete the post.",
                onConfirm: () => {}
            });
        }
    })
    .catch(error => {
        console.error("Delete error:", error);
        showCustomModal({
            title: "Error",
            message: "An error occurred while deleting the post.",
            onConfirm: () => {}
        });
    });
}

function markDonorFound(postId) {
    // Get current status and donor count from the DOM
    const statusBar = document.querySelector(`.card[data-id="${postId}"] .status-bar`);
    const donorText = document.getElementById(`assigned-donors-${postId}`).innerText;

    // If all donors already assigned, just show alert and exit
    if (donorText === "All Donors Assigned" || statusBar.classList.contains("donor-assigned")) {
        showCustomModal({
            title: "Already Fulfilled",
            message: "All required donors have already been assigned for this request.",
            onConfirm: () => {}
        });
        return;
    }

    // Otherwise, show input modal
    showCustomModal({
        title: "Donor Found",
        message: "How many donors have you found?",
        input: true,
        inputPlaceholder: "Enter number of donors...",
        onConfirm: (foundCount) => {
            const count = parseInt(foundCount);

            if (!count || count <= 0) {
                showCustomModal({
                    title: "Invalid Input",
                    message: "Please enter a valid number greater than 0.",
                    onConfirm: () => {}
                });
                return;
            }

            fetch(`/mark_donor_found/${postId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ found_count: count })
            })
            .then(async (response) => {
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || "Unknown error");
                }

                showCustomModal({
                    title: "Success",
                    message: data.message,
                    onConfirm: () => {
                        // ✅ Update UI
                        document.getElementById(`assigned-donors-${postId}`).innerText = data.new_assigned;

                        if (data.status === "Fulfilled") {
                            statusBar.classList.add("donor-assigned");
                        }
                    }
                });
            })
            .catch(err => {
                console.error("🚨 AJAX Error:", err);
                showCustomModal({
                    title: "Error",
                    message: err.message || "Something went wrong.",
                    onConfirm: () => {}
                });
            });
        }
    });
}

// Automatically remove flash messages after 5 seconds
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            // Only remove alerts that are NOT inside the notification popup
            if (!alert.closest('#notifPopup')) {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);