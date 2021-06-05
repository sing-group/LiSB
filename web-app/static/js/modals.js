var div;

function open_restore_modal(backup_name) {

    // Change backup name
    document.getElementById('to-restore-backup-name').innerHTML = backup_name;
    document.getElementById('to-restore-input').value = backup_name;

    // Include field for key if encrypted backup
    if (backup_name.includes(".enc") && div == undefined) {
        const key_label = document.createElement('label');
        const key_input = document.createElement('input');
        key_input.name = 'decryption-key';
        key_input.type = 'text';
        key_label.htmlFor = 'decryption-key';
        key_label.innerHTML = "Please provide the decryption key:";

        div = document.getElementById('decryption-key');
        div.classList.add('form-group');
        div.appendChild(key_label);
        div.appendChild(key_input);
    }

    // Open modal
    $('#restore-modal').modal('show');
}

function open_delete_modal(backup_name) {

    // Change backup name
    document.getElementById('to-delete-backup-name').innerHTML = backup_name;
    document.getElementById('to-delete-input').value = backup_name;

    // Open modal
    $('#delete-modal').modal('show');
}