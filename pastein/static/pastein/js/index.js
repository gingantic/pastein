// Global variable to store the current content
let content;

$(document).ready(function () {
    // Theme management module - handles all dark/light theme related functionality
    const themeManager = {
        init() {
            // Check cookies first, then localStorage, then default to 'light'
            const savedTheme = this.getCookie('theme') || localStorage.getItem('theme') || 'light';
            this.applyTheme(savedTheme);
            this.setupEventListeners();
        },

        // Add cookie management methods
        setCookie(name, value, days = 365) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            const expires = `expires=${date.toUTCString()}`;
            document.cookie = `${name}=${value};${expires};path=/`;
        },

        getCookie(name) {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [cookieName, cookieValue] = cookie.split('=').map(c => c.trim());
                if (cookieName === name) return cookieValue;
            }
            return null;
        },

        // Applies theme settings to the page
        applyTheme(theme) {
            $('body').attr('data-bs-theme', theme);
            this.updatePrismTheme(theme);
            this.updateIcon(theme);
        },

        // Updates Prism.js syntax highlighting theme
        updatePrismTheme(theme) {
            $('#prism-css').attr('href', `/static/pastein/prism/prism${theme === 'dark' ? '-dark' : ''}.css`);
        },

        // Updates the theme toggle icon between sun and moon
        updateIcon(theme) {
            $('#darkModeIcon').removeClass(theme === 'dark' ? 'fa-moon' : 'fa-sun')
                            .addClass(theme === 'dark' ? 'fa-sun' : 'fa-moon');
        },

        // Sets up theme-related event listeners
        setupEventListeners() {
            // Toggle dark/light theme
            $('#darkModeToggle').on('click', () => {
                const currentTheme = $('body').attr('data-bs-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                
                this.applyTheme(newTheme);
                // Save theme in both localStorage and cookies
                localStorage.setItem('theme', newTheme);
                this.setCookie('theme', newTheme);
            });
        }
    };

    // Content management module - handles content display and copying
    const contentManager = {
        init() {
            this.updateContent();
            this.setupEventListeners();
        },

        // Updates the content display with line numbers and syntax highlighting
        updateContent() {
            try {
                const pasteinBody = $('.pastein-body');
                const language = pasteinBody.attr('data-language');
                content = pasteinBody.text();

                pasteinBody.empty();
                const lines = content.split('\n');

                lines.forEach((line, index) => {
                    const linePair = this.createLinePair(line, index, language);
                    pasteinBody.append(linePair);
                });
            } catch (error) {
                console.error('Error updating content:', error);
            }
        },

        // Creates a line pair element (line number + content) for each line
        createLinePair(line, index, language) {
            const linePair = $('<div>').addClass('line-pair');
            const lineNumber = $('<div>')
                .addClass('line-number')
                .text(`${index + 1}.`);
            const lineContent = $('<pre>').addClass('line-content');

            // Apply syntax highlighting if language is specified
            if (language && language !== 'plaintext') {
                const codeElement = $('<code>')
                    .addClass(`language-${language}`)
                    .text(line);
                Prism.highlightElement(codeElement[0]);
                lineContent.append(codeElement);
            } else {
                lineContent.text(line);
            }

            return linePair.append(lineNumber, lineContent);
        },

        // Sets up content-related event listeners
        setupEventListeners() {
            $('#copy').click(() => {
                navigator.clipboard.writeText(content)
                    .then(() => alert("Copied to clipboard!"))
                    .catch(err => console.error("Failed to copy:", err));
            });
            $('#delete-btn').click(() => {
                if (confirm('Are you sure you want to delete this paste?')) {
                    window.location.href = $('#delete-btn').attr('href');
                }
            });
        }
    };

    // UI management module - handles general UI interactions
    const uiManager = {
        init() {
            this.setupEventListeners();
        },

        // Sets up UI-related event listeners
        setupEventListeners() {
            // Toggle password visibility for any password field with a toggle button
            $(document).on('click', '.password-toggle', function() {
                const passwordField = $(this).siblings('input[type="password"], input[type="text"]');
                const type = passwordField.attr('type') === 'password' ? 'text' : 'password';
                passwordField.attr('type', type);
                $(this).toggleClass('fa-eye fa-eye-slash');
            });

            // Double-click user dropdown to go to profile
            $('#userDropdown').dblclick(function() {
                window.location.href = $('#myPaste').attr('href');
            });
        }
    };

    // Initialize all modules when document is ready
    themeManager.init();
    contentManager.init();
    uiManager.init();
});