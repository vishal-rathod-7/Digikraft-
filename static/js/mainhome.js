// Logged-in user email
let currentUserEmail = sessionStorage.getItem("userEmail");


// ================== UPLOAD (only if elements exist) ==================
const fileInput = document.getElementById("fileInput");
const selectFileBtn = document.getElementById("selectFileBtn");
const uploadForm = document.getElementById("uploadForm");
const selectedFilesDiv = document.getElementById("selectedFiles");
const uploadBox = document.getElementById("uploadBox");

if (uploadBox && fileInput) {
    uploadBox.addEventListener("click", () => {
        fileInput.click();
    });
}

if (selectFileBtn && fileInput && uploadForm) {
    // Select files button
    selectFileBtn.addEventListener("click", () => {
        fileInput.click();
    });

    // Show selected files
    fileInput.addEventListener("change", () => {
        selectedFilesDiv.innerHTML = "";
        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            const p = document.createElement("p");
            p.textContent = file.name;
            selectedFilesDiv.appendChild(p);
        }
    });

    // Upload files
    uploadForm.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!currentUserEmail) {
            Swal.fire({
                icon: 'warning',
                title: 'Not logged in',
                text: 'Please log in to upload files'
            });
            return;
        }
        if (fileInput.files.length === 0) {
            Swal.fire({
                icon: 'warning',
                title: 'No files selected',
                text: 'Please select file(s) to upload'
            });
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append("file", fileInput.files[i]);
        }
        formData.append("email", currentUserEmail);

        fetch("http://127.0.0.1:5000/upload", {
            method: "POST",
            body: formData,
        })
            .then((res) => res.json())
            .then((data) => {
                Swal.fire({
                    icon: data.message.includes("success") ? 'success' : 'error',
                    title: data.message.includes("success") ? 'Uploaded!' : 'Upload Failed',
                    text: data.message,
                    timer: 2000,
                    showConfirmButton: !data.message.includes("success")
                });
                fileInput.value = ""; 
                selectedFilesDiv.innerHTML = "";
                loadUserFiles(); // Refresh after upload
            })
            .catch((err) => {
                Swal.fire({
                    icon: 'error',
                    title: 'Error!',
                    text: 'Something went wrong while uploading'
                });
                console.error(err);
            });
    });
}
let allFiles = []; // Store all fetched files for search/filter

function loadUserFiles() {
    if (!currentUserEmail) return;
    fetch("http://127.0.0.1:5000/get_files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: currentUserEmail }),
    })
        .then((res) => res.json())
        .then((data) => {
            allFiles = data.files || [];
            renderFileTable(allFiles);
        })
        .catch((err) => console.error(err));
}

function renderFileTable(files) {
    const tbody = document.getElementById("fileTableBody");
    if (!tbody) return; 

    tbody.innerHTML = "";
    files.forEach((file) => {
        const ext = (file.filename.split(".").pop() || "").toUpperCase();
        const uploaded = file.uploaded_at;
        const viewUrl = `http://127.0.0.1:5000${file.url}`;
        const downloadUrl = `http://127.0.0.1:5000/download/${file.id}`;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${file.filename}</td>
            <td>${ext}</td>
            <td>${uploaded}</td>
            <td>
                <i class="fa-solid fa-eye" onclick="window.open('${viewUrl}', '_blank')"></i> |
                <i class="fas fa-download action-icon download" onclick="window.location.href='${downloadUrl}'"></i> |
                <i class="fa-regular fa-trash-can" onclick="deleteFile(${file.id})"></i>                 
            </td>
            <td>
                <i class="fa-solid fa-share-nodes" style="color:#3aeb4f; margin-left: 17px;" onclick="shareFile('${file.filename}')"></i>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
// Delete file
function deleteFile(fileId) {
    if (!confirm("Are you sure you want to delete this file?")) return;

    fetch(`http://127.0.0.1:5000/delete_file/${fileId}`, {
        method: "DELETE",
    })
        .then((res) => res.json())
        .then((data) => {
            alert(data.message);
            loadUserFiles(); // Refresh list after delete
        })
        .catch((err) => console.error(err));
}

// ================== SEARCH & FILTER ==================
const searchInput = document.getElementById("searchInput");
const fileTypeFilter = document.getElementById("fileTypeFilter");

function filterFiles() {
    const searchText = searchInput ? searchInput.value.toLowerCase() : "";
    const typeFilter = fileTypeFilter ? fileTypeFilter.value : "";

    const filtered = allFiles.filter(file => {
        const matchesName = file.filename.toLowerCase().includes(searchText);
        const matchesType = !typeFilter || (file.filename.split(".").pop() || "").toLowerCase() === typeFilter.toLowerCase();
        return matchesName && matchesType;
    });

    renderFileTable(filtered);
}

if (searchInput) searchInput.addEventListener("input", filterFiles);
if (fileTypeFilter) fileTypeFilter.addEventListener("change", filterFiles);

// Load files on page load (only if table exists)
window.onload = () => {
    if (document.getElementById("fileTableBody")) {
        loadUserFiles();
    }
};

// uniq
// SHOW USER EMAIL
document.getElementById("userEmailShow").innerText = sessionStorage.getItem("userEmail") || "User";

// ----- FETCH USER STATS -----
function loadStats() {
    fetch("http://127.0.0.1:5000/get_files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: sessionStorage.getItem("userEmail") }),
    })
    .then(res => res.json())
    .then(data => {
        let files = data.files || [];

        document.getElementById("totalDocs").innerText = files.length;

        if (files.length > 0) {
            let last = files[files.length - 1].uploaded_at;
            document.getElementById("lastUpload").innerText = new Date(last).toLocaleString();
        }

    });
}

loadStats();



// ----- FETCH USER STATS -----
function updateDashboardStats() {
    // Last Upload fetch
    fetch("http://localhost:5000/last_upload")
        .then(res => res.json())
        .then(data => {
            document.getElementById("lastUpload").innerText = data.last_upload;
        });
}


window.onload = function() {
    updateDashboardStats();
};

// ----- AI WIDGET -----
function showComingSoon() {
    document.getElementById("comingSoonModal").style.display = "flex";
}

function closeComingSoon() {
    document.getElementById("comingSoonModal").style.display = "none";
}

