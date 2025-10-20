document.addEventListener('DOMContentLoaded', function() {
    const folderHeaders = document.querySelectorAll('.folder-header');
    
    folderHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const folderId = this.getAttribute('data-folder');
            const content = document.getElementById(`${folderId}-content`);
            const toggleIcon = this.querySelector('.toggle-icon');
            
            const isExpanded = content.classList.contains('expanded');
            
            if (!isExpanded) {
                content.classList.add('expanded');
                toggleIcon.textContent = '-';
            } else {
                content.classList.remove('expanded');
                toggleIcon.textContent = '+';
            }
        });
    });
    

    const defaultFolderHeader = document.querySelector('[data-folder="verbali"]');
    if (defaultFolderHeader) {
        defaultFolderHeader.click();
    }
});