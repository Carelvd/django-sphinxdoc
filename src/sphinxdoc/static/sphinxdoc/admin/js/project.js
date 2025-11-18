document.addEventListener('DOMContentLoaded', function() {
    const repo = document.getElementById('id_repository'); // Replace with your actual field ID
    const slug = document.getElementById('id_slug'); // Replace with your actual field ID
    const root = document.getElementById('id_root'); // Replace with your actual field ID
    if (root) {
        root.onfocus = function(event) {
            if (!root.value) {
                if (!!repo.value) {
                    try {
                        const url = new URL(repo.value);
                        console.log(url);
                        console.log(url.pathname);
                        root.value = url.pathname.replace(/^\/+|\/+$/g, ""); // Example: Set target field to uppercase of source
                    } catch (error) {
                        console.warn(error);
                        // TODO: Use a regexp to match this more appropriately
                        root.value = repo.value.split(":")[1].split(".")[0].replace(/^\/+|\/+$/g, ""); // Assumes URL is of the form VCS@DOMAIN.TLD:OWNER/PROJECT.VCS
                    }
                } else {
                    root.value = slug.value;
                }
            } 
        }
        // sourceField.addEventListener('change', function() {});
    }
});