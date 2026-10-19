import { i18next } from "@translations/invenio_requests/i18next";
import tinymce from "tinymce/tinymce";
import swedishLabels from "./sv.json";
import "./tinymce-sv";

// The instance registry loads before invenio-requests-base (see the RDM
// javascript template), so these resources exist before the PR's shared
// richEditorLabels object evaluates its translation calls at module import.
// Keep the upstream comment editors and all their logic unchanged.
i18next.addResourceBundle("sv", "translation", swedishLabels, true, true);

// TinyMCE's built-in labels use its own language pack, not i18next.
// Defaults apply to new editors site-wide; explicit editorConfig takes priority.
if ((i18next.language || "").split(/[-_]/)[0] === "sv") {
  tinymce.overrideDefaults({ ...tinymce.defaultOptions, language: "sv" });
}
