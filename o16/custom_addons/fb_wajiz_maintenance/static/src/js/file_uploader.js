/** @odoo-module **/

import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { FileUploader } from "@web/views/fields/file_handler";
import { humanSize } from "@web/core/utils/binary";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation"; // eslint-disable-line sort-imports
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";

// Define allowed image formats
const ALLOWED_IMAGE_FORMATS = ["image/jpeg", "image/png", "image/tiff"];

// List of specific models to apply restrictions
const RESTRICTED_MODELS = ["maintenance.request"];

patch(FileUploader.prototype, "fb_wajiz_maintenance_file_uploader", {
    setup() {
        // Manually replicate parent setup (can't use super in patches)
        this.notification = useService("notification");
        this.fileInputRef = useRef("fileInput");
        this.state = useState({
            isUploading: false,
        });

        // Add our custom initialization
        this.max_attachment_size = session.max_attachment_size || 2 * 1024 * 1024;
        this.dialogService = useService("dialog");
        console.log("FileUploader patched - max_attachment_size:", this.max_attachment_size);
    },
    async onFileChange(ev) {
        console.log("onFileChange called!");
        console.log("ALLOWED_IMAGE_FORMATS", ALLOWED_IMAGE_FORMATS);

        // Get the current model - improved approach with multiple fallbacks
        let currentModel = null;

        if (this.props.resModel) {
            currentModel = this.props.resModel;
        } else if (this.props.threadModel) {
            currentModel = this.props.threadModel;
        } else if (this.env.model && this.env.model.config && this.env.model.config.resModel) {
            currentModel = this.env.model.config.resModel;
        }

        console.log("Detected model:", currentModel);

        var larger_files = [];
        const invalid_format_files = [];

        for (const file of ev.target.files) {

            // Check if the current model is restricted
            if (RESTRICTED_MODELS.includes(currentModel)) {
                // Check file size
                if (file.size > this.max_attachment_size) {
                    larger_files.push(file);
                }
            }

            console.log("Checking file:", file.name, "type:", file.type, "size:", file.size);

            // Check file format
            if (!ALLOWED_IMAGE_FORMATS.includes(file.type)) {
                invalid_format_files.push(file);
            }
        }

        // Check if the current model is restricted
        if (RESTRICTED_MODELS.includes(currentModel)) {
            // Handle invalid format files
            if (invalid_format_files.length !== 0) {
                this.dialogService.add(ConfirmationDialog, {
                    body: _t("Only image files (JPEG, PNG, TIFF) are allowed."),
                    title: _t("Validation Error"),
                });
                ev.target.value = null;  // Clear the input
                return;
            }

            // Handle larger files
            // The selected file exceeds the maximum file size of
            if (larger_files.length !== 0) {
                this.dialogService.add(ConfirmationDialog, {
                    body: _t(
                        "The attachment exceeds the maximum attachment size. Please upload files less than or equal to %s",
                        humanSize(this.max_attachment_size)
                    ),
                    title: _t("Validation Error"),
                });
                ev.target.value = null;  // Clear the input
                return;
            }
        }

        return super.onFileChange(...arguments);
    },
});