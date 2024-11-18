document.addEventListener('DOMContentLoaded', function() {
    // UI Elements
    const navLinks = document.querySelectorAll('.sidebar nav a');
    const sections = document.querySelectorAll('.dashboard-section');
    const fileInput = document.getElementById('csv-file');
    const fileName = document.querySelector('.file-name');
    const emailPromptTextarea = document.getElementById('email-prompt');
    const detectedColumnsDiv = document.querySelector('.variable-buttons');
    const searchInput = document.getElementById('email-search');

    // Navigation functionality
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSection = link.dataset.section;
            
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === `${targetSection}-section`) {
                    section.classList.add('active');
                }
            });
        });
    });

    // File Upload Handling
    fileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const content = e.target.result;
                const lines = content.split('\n');
                const headers = lines[0].split(',').map(header => header.trim());

                // Display column buttons
                detectedColumnsDiv.innerHTML = headers.map(header => 
                    `<button class="variable-button" type="button">{${header}}</button>`
                ).join('');

                // Add click handlers for variable buttons
                document.querySelectorAll('.variable-button').forEach(button => {
                    button.addEventListener('click', function() {
                        const cursorPos = emailPromptTextarea.selectionStart;
                        const textBefore = emailPromptTextarea.value.substring(0, cursorPos);
                        const textAfter = emailPromptTextarea.value.substring(cursorPos);
                        emailPromptTextarea.value = textBefore + button.textContent + textAfter;
                        emailPromptTextarea.focus();
                    });
                });
            };
            reader.readAsText(file);
        }
    });

    // Loading overlay functions
    function showLoading() {
        document.querySelector('.loading-overlay').style.display = 'flex';
    }

    function hideLoading() {
        document.querySelector('.loading-overlay').style.display = 'none';
    }

    // Schedule Campaign Function
    window.scheduleEmailCampaign = function() {
        showLoading();
        
        const formData = new FormData();
        const csvFile = fileInput.files[0];
        const emailPrompt = emailPromptTextarea.value;
        const scheduledTime = document.getElementById('schedule-time').value;

        // Get CSV headers for validation
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const headers = content.split('\n')[0].split(',').map(h => h.trim());
            
            if (!validateTemplate(emailPrompt, headers)) {
                hideLoading();
                return;
            }

            // Continue with form submission
            formData.append('file', csvFile);
            formData.append('email_prompt', emailPrompt);
            formData.append('scheduled_time', scheduledTime);
            formData.append('email_method', 'esp');

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.status === 'success') {
                    alert('Campaign scheduled successfully!');
                    updateScheduledEmailsList();
                    updateAnalytics(data);
                } else {
                    alert(data.message || 'Error scheduling campaign');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                hideLoading();
                alert('Error scheduling campaign');
            });
        };
        reader.readAsText(csvFile);
    };

    // Update Analytics Function
    function updateAnalytics(data) {
        if (data) {
            document.getElementById('total-sent').textContent = data.total_sent || 0;
            document.getElementById('total-opened').textContent = data.opened || 0;
            document.getElementById('total-clicked').textContent = data.clicked || 0;
            document.getElementById('total-failed').textContent = data.failed || 0;
        }
    }

    // Scheduled Emails List Function
    function updateScheduledEmailsList() {
        fetch('/scheduled-emails')
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('scheduled-emails-list');
                tbody.innerHTML = data.map(email => `
                    <tr class="scheduled-email-row">
                        <td>${email.email}</td>
                        <td>${new Date(email.scheduled_time).toLocaleString()}</td>
                        <td><span class="status-${email.status.toLowerCase()}">${email.status}</span></td>
                        <td>${email.company_name || 'N/A'}</td>
                    </tr>
                `).join('');
            })
            .catch(error => console.error('Error fetching scheduled emails:', error));
    }

    // Search Functionality
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.scheduled-email-row');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Initialize Analytics Chart
    const ctx = document.getElementById('analytics-chart');
    if (ctx) {
        new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Emails Sent',
                    data: [0, 0, 0, 0, 0, 0, 0],
                    borderColor: '#3498db',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Auto-update scheduled emails list
    updateScheduledEmailsList();
    setInterval(updateScheduledEmailsList, 30000);

    // Initial analytics update
    fetch('/analytics')
        .then(response => response.json())
        .then(data => updateAnalytics(data))
        .catch(error => console.error('Error fetching analytics:', error));

    // Email Preview Functions
    function previewEmail() {
        const emailPrompt = document.getElementById('email-prompt').value;
        const modal = document.getElementById('previewModal');
        const previewContent = document.getElementById('email-preview-content');
        
        if (!emailPrompt.trim()) {
            showNotification('Please enter an email template first', 'error');
            return;
        }

        // Show modal with loading state
        modal.style.display = 'block';
        previewContent.innerHTML = `
            <div class="preview-loading">
                <div class="spinner"></div>
                <p>Generating preview...</p>
            </div>
        `;

        // Get sample data from CSV if available
        let sampleData = {
            Name: "John Doe",
            Company: "ACME Corp",
            Role: "Marketing Manager",
            Email: "john@example.com"
        };

        // If CSV is loaded, use first row data
        const csvFile = document.getElementById('csv-file').files[0];
        if (csvFile) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const content = e.target.result;
                const lines = content.split('\n');
                if (lines.length > 1) {
                    const headers = lines[0].split(',').map(h => h.trim());
                    const firstRow = lines[1].split(',').map(v => v.trim());
                    sampleData = {};
                    headers.forEach((header, index) => {
                        sampleData[header] = firstRow[index] || '';
                    });
                }
                generatePreview(emailPrompt, sampleData);
            };
            reader.readAsText(csvFile);
        } else {
            generatePreview(emailPrompt, sampleData);
        }
    }

    function generatePreview(template, sampleData) {
        fetch('/preview-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                template: template,
                sample_data: sampleData
            })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('email-preview-content').innerHTML = `
                <div class="preview-header">
                    <p><strong>To:</strong> ${sampleData.Email}</p>
                    <p><strong>Subject:</strong> Your Customized Email</p>
                </div>
                <div class="preview-body">
                    ${data.preview}
                </div>
            `;
        })
        .catch(error => {
            console.error('Preview error:', error);
            showNotification('Error generating preview', 'error');
        });
    }

    // Modal Controls
    document.addEventListener('DOMContentLoaded', function() {
        const modal = document.getElementById('previewModal');
        const closeBtn = document.querySelector('.close-modal');

        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };

        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    });

    // Notification System
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Add icon based on type
        const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
        
        notification.innerHTML = `
            <span class="notification-icon">${icon}</span>
            <span class="notification-message">${message}</span>
        `;
        
        document.getElementById('notification-container').appendChild(notification);
        
        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }

    // Initialize Server-Sent Events for real-time notifications
    function initializeSSE() {
        const eventSource = new EventSource('/campaign-events');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            showNotification(data.message, data.type);
        };
        
        eventSource.onerror = function(error) {
            console.error('SSE Error:', error);
            eventSource.close();
            // Try to reconnect after 5 seconds
            setTimeout(initializeSSE, 5000);
        };
    }

    // Initialize notifications when document loads
    document.addEventListener('DOMContentLoaded', function() {
        initializeSSE();
    });
});

// Add drag and drop functionality
document.addEventListener('dragover', (e) => {
    e.preventDefault();
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.classList.add('dragover');
    }
});

document.addEventListener('dragleave', (e) => {
    e.preventDefault();
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.classList.remove('dragover');
    }
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'text/csv') {
            document.getElementById('csv-file').files = e.dataTransfer.files;
            document.querySelector('.file-name').textContent = file.name;
            // Trigger the change event
            const event = new Event('change');
            document.getElementById('csv-file').dispatchEvent(event);
        } else {
            alert('Please upload a CSV file');
        }
    }
});

function validateTemplate(template, csvHeaders) {
    const placeholderRegex = /\{([^}]+)\}/g;
    const matches = template.match(placeholderRegex) || [];
    
    // Check if all placeholders exist in CSV headers
    const invalidPlaceholders = matches.filter(placeholder => {
        const field = placeholder.slice(1, -1); // Remove { and }
        return !csvHeaders.includes(field);
    });

    if (invalidPlaceholders.length > 0) {
        alert(`Invalid placeholders found: ${invalidPlaceholders.join(', ')}\nAvailable fields: ${csvHeaders.join(', ')}`);
        return false;
    }
    return true;
}