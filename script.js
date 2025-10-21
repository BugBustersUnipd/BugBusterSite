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

    // Fix broken links to assets/docs when the site is served from a different Pages source
    // If a relative assets/docs/... link returns 404, replace it with the raw.githubusercontent.com URL
    function fixBrokenDocLinks() {
        const owner = 'BugbustersUnipd';
        const repo = 'BugBusterSite';
        const branch = 'main';

        const anchors = Array.from(document.querySelectorAll('a[href^="assets/docs/"]'));
        anchors.forEach(a => {
            const href = a.getAttribute('href');
            // Try a HEAD request to check existence
            fetch(href, { method: 'HEAD' }).then(res => {
                if (!res.ok) {
                    // fallback to raw.githubusercontent.com
                    const raw = 'https://raw.githubusercontent.com/' + owner + '/' + repo + '/' + branch + '/' + encodeURI(href);
                    a.setAttribute('href', raw);
                }
            }).catch(() => {
                // on network error, also fallback
                const raw = 'https://raw.githubusercontent.com/' + owner + '/' + repo + '/' + branch + '/' + encodeURI(href);
                a.setAttribute('href', raw);
            });
        });
    }

    fixBrokenDocLinks();
});