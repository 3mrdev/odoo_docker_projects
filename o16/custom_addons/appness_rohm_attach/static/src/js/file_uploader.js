/** @odoo-module **/

import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {FileUploader} from "@web/views/fields/file_handler";
import {humanSize} from "@web/core/utils/binary";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";
import {_t} from "@web/core/l10n/translation"; // eslint-disable-line sort-imports
import {useService} from "@web/core/utils/hooks";

// Define allowed image formats
const ALLOWED_IMAGE_FORMATS = ["image/jpeg", "image/png", "image/tiff"];

// List of specific models to apply restrictions
const RESTRICTED_MODELS1 = ["project.project", "project.task"];
const RESTRICTED_MODELS2 = ["helpdesk.ticket"];

patch(FileUploader.prototype, {
    setup() {
        super.setup();
        this.max_attachment_size1 = session.max_attachment_size1 || 2 * 1024 * 1024;
        this.max_attachment_size2 = session.max_attachment_size2 || 2 * 1024 * 1024;
        this.dialogService = useService("dialog");
    },
    /**
     * @inherit
     */
    // eslint-disable-next-line no-unused-vars
    async onFileChange(ev) {
        var larger_files = [];
        const invalid_format_files = [];
        const currentModel = this.props.slots.toggler.__ctx.props.threadModel;
        
        for (const file of ev.target.files) {

            // Check if the current model is restricted
            if (RESTRICTED_MODELS1.includes(currentModel)) {
                // Check file size
                if (file.size > this.max_attachment_size1) {
                    larger_files.push(file);
                }
            }

            // Check if the current model is restricted
            if (RESTRICTED_MODELS2.includes(currentModel)) {
                // Check file size
                if (file.size > this.max_attachment_size2) {
                    larger_files.push(file);
                }
            }
            
            console.log(ALLOWED_IMAGE_FORMATS);
            console.log(file.type);

            // Check file format
            if (!ALLOWED_IMAGE_FORMATS.includes(file.type)) {
                invalid_format_files.push(file);
            }
        }

        // Check if the current model is restricted
        if (RESTRICTED_MODELS1.includes(currentModel)) {
            // Handle larger files
            // The selected file exceeds the maximum file size of
            if (larger_files.length !== 0) {
                this.dialogService.add(ConfirmationDialog, {
                    body: _t(
                        "The attachment exceed the maximum attachment size please make sure to insert attachment less than or equal %s",
                        humanSize(this.max_attachment_size1)
                    ),
                    title: _t("Valiation Error"),
                });
                return false;
            }
        }
        
        // Check if the current model is restricted
        if (RESTRICTED_MODELS2.includes(currentModel)) {
            // Handle invalid format files
            if (invalid_format_files.length !== 0) {
                this.dialogService.add(ConfirmationDialog, {
                    body: _t("Only image files (JPEG, PNG, TIFF) are allowed."),
                    title: _t("Validation Error"),
                });
                return false;
            }

            // Handle larger files
            // The selected file exceeds the maximum file size of
            if (larger_files.length !== 0) {
                this.dialogService.add(ConfirmationDialog, {
                    body: _t(
                        "The attachment exceed the maximum attachment size please make sure to insert attachment less than or equal to %s",
                        humanSize(this.max_attachment_size2)
                    ),
                    title: _t("Valiation Error"),
                });
                return false;
            }
        }
        
        return super.onFileChange(...arguments);
    },
});