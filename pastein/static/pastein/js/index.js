let content;

$(document).ready(function () {
    // Check for saved theme on page load
    const savedTheme = localStorage.getItem('theme') || 'light';
    $('body').attr('data-bs-theme', savedTheme);
    updateIcon(savedTheme);

    // Toggle dark mode on button click
    $('#darkModeToggle').on('click', function () {
        const currentTheme = $('body').attr('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        // Set theme attribute and update icon
        $('body').attr('data-bs-theme', newTheme);
        updateIcon(newTheme);

        // Save theme to localStorage
        localStorage.setItem('theme', newTheme);
    });
    
    // Function to update the moon/sun icon
    function updateIcon(theme) {
        if (theme === 'dark') {
            $('#darkModeIcon').removeClass('fa-moon').addClass('fa-sun');
        } else {
            $('#darkModeIcon').removeClass('fa-sun').addClass('fa-moon');
        }
    }

    $('#togglePassword').click(function() {
        const password = $('#password');
        const icon = $(this);
        
        // Toggle password visibility
        const type = password.attr('type') === 'password' ? 'text' : 'password';
        password.attr('type', type);
        
        // Toggle icon
        icon.toggleClass('fa-eye fa-eye-slash');
    });

    $('#copy').click(function() {
        // Use the Clipboard API
        navigator.clipboard.writeText(content)
            .then(() => {
                alert("Copied to clipboard!");
            })
            .catch(err => {
                console.error("Failed to copy: ", err);
            });
    });

    // Function to making the line numbers on the view
    function updateContent() {
        const pasteinBody = $('.pastein-body');
        content = pasteinBody.text();

        pasteinBody.empty(); // Clear previous content
    
        // Split content into lines
        const lines = content.split('\n');
    
        lines.forEach((line, index) => {
            // Create line-pair container
            const linePair = $('<div>').addClass('line-pair');
    
            // Create line number
            const lineNumber = $('<div>')
                .addClass('line-number')
                .text(`${index + 1}.`);
    
            // Create line content
            const lineContent = $('<div>')
                .addClass('line-content')
                .text(line);
    
            // Append elements to the line-pair
            linePair.append(lineNumber, lineContent);
    
            // Append line-pair to the container
            pasteinBody.append(linePair);
        });
    }

    updateContent();          
});