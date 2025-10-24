document.addEventListener('DOMContentLoaded', function () {
    // Before attaching collapse behavior, sort verbali subfolders so the most recent appear first
    function sortSubfoldersDesc(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        // collect direct .subfolder children
        const items = Array.from(container.querySelectorAll(':scope > .subfolder'));
        if (items.length === 0) return;
        items.sort((a, b) => {
            const ha = (a.querySelector('.folder-header') || {}).textContent || '';
            const hb = (b.querySelector('.folder-header') || {}).textContent || '';
            // reverse order, numeric-aware
            return hb.trim().localeCompare(ha.trim(), undefined, { numeric: true, sensitivity: 'base' });
        });
        // re-append in sorted order
        items.forEach(i => container.appendChild(i));
    }

    // Sort internal and external verbali lists
    sortSubfoldersDesc('verbali-interni-content');
    sortSubfoldersDesc('verbali-esterni-content');

    const folderHeaders = document.querySelectorAll('.folder-header');

    // Flatten nested .subfolder structures into a single list of links
    function flattenVerbaliLinks(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        // find all anchors anywhere inside the container
        const anchors = Array.from(container.querySelectorAll('a'));
        if (anchors.length === 0) return;

        // build list items from anchors (clone to preserve attributes)
        const items = anchors.map(a => {
            return {
                text: (a.textContent || a.innerText || '').trim(),
                href: a.getAttribute('href'),
                node: a.cloneNode(true)
            };
        });

        // sort descending (most recent first) using numeric-aware compare on the visible text
        items.sort((x, y) => y.text.localeCompare(x.text, undefined, { numeric: true, sensitivity: 'base' }));

        // create a new ul and append sorted items
        const ul = document.createElement('ul');
        items.forEach(it => {
            const li = document.createElement('li');
            // ensure links open in new tab and are safe
            it.node.setAttribute('target', '_blank');
            it.node.setAttribute('rel', 'noopener noreferrer');
            li.appendChild(it.node);
            ul.appendChild(li);
        });

        // clear current content and insert the new list
        container.innerHTML = '';
        container.appendChild(ul);
    }

    // Flatten both internals and externals after sorting so the order is preserved
    flattenVerbaliLinks('verbali-interni-content');
    flattenVerbaliLinks('verbali-esterni-content');

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
    
});