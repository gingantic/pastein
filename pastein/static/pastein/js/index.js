// Global variable to store the current content
let content;

$(document).ready(function () {
    // Theme management module - handles all dark/light theme related functionality
    const themeManager = {
        init() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            this.applyTheme(savedTheme);
            this.setupEventListeners();
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
                localStorage.setItem('theme', newTheme);
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
        }
    };

    // UI management module - handles general UI interactions
    const uiManager = {
        init() {
            this.setupEventListeners();
        },

        // Sets up UI-related event listeners
        setupEventListeners() {
            // Toggle password visibility
            $('#togglePassword').click(function() {
                const password = $('#password');
                const type = password.attr('type') === 'password' ? 'text' : 'password';
                password.attr('type', type);
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