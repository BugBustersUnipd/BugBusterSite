document.addEventListener('DOMContentLoaded', function () {
    const folderHeaders = document.querySelectorAll('.folder-header');

    function setCollapsedState(header, collapsed = true) {
        const folderId = header.getAttribute('data-folder');
        const content = document.getElementById(`${folderId}-content`);
        const toggleIcon = header.querySelector('.toggle-icon');
        if (!content) return;

        if (collapsed) {
            content.classList.remove('expanded');
            content.setAttribute('aria-hidden', 'true');
            header.setAttribute('aria-expanded', 'false');
            if (toggleIcon) toggleIcon.textContent = '+';
        } else {
            content.classList.add('expanded');
            content.setAttribute('aria-hidden', 'false');
            header.setAttribute('aria-expanded', 'true');
            if (toggleIcon) toggleIcon.textContent = '-';
        }
    }

    function toggleHeader(header) {
        const folderId = header.getAttribute('data-folder');
        const content = document.getElementById(`${folderId}-content`);
        if (!content) return;
        const isExpanded = content.classList.contains('expanded');
        setCollapsedState(header, isExpanded);
    }

    folderHeaders.forEach(header => {
        // Make header keyboard-focusable and expose button semantics
        header.setAttribute('role', 'button');
        header.setAttribute('tabindex', '0');
        header.setAttribute('aria-expanded', 'false');

        // Ensure associated content has aria-hidden set
        const folderId = header.getAttribute('data-folder');
        const content = document.getElementById(`${folderId}-content`);
        if (content) content.setAttribute('aria-hidden', 'true');

        // Click handler
        header.addEventListener('click', function (e) {
            // ignore clicks from interactive children (like links)
            if (e.target.tagName.toLowerCase() === 'a') return;
            toggleHeader(this);
        });

        // Keyboard support: Enter or Space toggles
        header.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleHeader(this);
            }
        });
    });

    // Initialize: collapse all folders on load
    folderHeaders.forEach(h => setCollapsedState(h, true));

    // Intercept clicks on PDF links and open them in the in-site viewer
    // This avoids the browser 'download' behavior when possible by fetching
    // the PDF and opening it via a blob URL inside `viewer.html`.
    function isPdfLink(href) {
        if (!href) return false;
        return href.toLowerCase().endsWith('.pdf');
    }

    document.querySelectorAll('a').forEach(a => {
        try {
            const href = a.getAttribute('href');
            if (isPdfLink(href)) {
                a.addEventListener('click', function (e) {
                    // let modifier keys open in new tab as usual
                    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
                    e.preventDefault();
                    // Navigate to our viewer page with the original URL encoded
                    const viewerUrl = `viewer.html?url=${encodeURIComponent(href)}`;
                    // Open in same tab so user sees the PDF viewer automatically
                    window.location.href = viewerUrl;
                });
            }
        } catch (err) {
            // ignore malformed hrefs
        }
    });
});