import uuid
from pathlib import Path

import flet as ft

from database.mongodb_service import MongoDiscussionService
from mode.FileAnonymization import FileAnonymization
from mode.PromptAnonymization import PromptAnonymization


def section_title(title: str):
    return ft.Column(
        controls=[
            ft.Text(
                title,
                size=21,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK87,
            ),
            ft.Container(
                width=165,
                height=2,
                bgcolor=ft.colors.BLUE_400,
                margin=ft.margin.only(top=-4),
            ),
        ],
        spacing=0,
    )


def result_box(title: str, text_control: ft.Text, height: int):
    return ft.Container(
        height=height,
        width=305,
        bgcolor=ft.colors.GREY_50,
        border_radius=4,
        padding=ft.padding.only(top=18, left=12, right=12),
        content=ft.Column(
            controls=[
                ft.Text(
                    title,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                text_control,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    )


def build_text_anonymization_card(
        discussion_uuid: str,
        discussion_service: MongoDiscussionService,
        language_state: dict,
        set_result: callable,
):
    anonymizer_fr = PromptAnonymization(language="fr")
    anonymizer_en = PromptAnonymization(language="en")

    prompt_input = ft.TextField(
        hint_text="Enter prompt to anonymize...",
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE_400,
        height=42,
        text_size=14,
        expand=True,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
    )

    def anonymize_text(e):
        prompt = prompt_input.value.strip()

        if not prompt:
            set_result("Please enter text to anonymize.")
            return

        try:
            lang = language_state["current"]
            anonymizer = anonymizer_en if lang == "en" else anonymizer_fr
            response = anonymizer.anonymize(prompt)

            discussion_service.save_prompt(
                discussion_uuid=discussion_uuid,
                prompt=response.originalText,
                anonymized_text=response.anonymizedText,
                match_table=response.matchTable,
            )

            set_result(response.anonymizedText)
            prompt_input.value = ""
            prompt_input.update()

        except Exception as exc:
            set_result(f"Could not anonymize text: {exc}")

    return ft.Container(
        width=350,
        height=200,
        padding=ft.padding.all(22),
        bgcolor=ft.colors.WHITE,
        border_radius=8,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=14,
            color=ft.colors.with_opacity(0.09, ft.colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
        content=ft.Column(
            controls=[
                section_title("Text Anonymization"),
                ft.Row(
                    controls=[
                        prompt_input,
                        ft.IconButton(
                            icon=ft.icons.SEND_OUTLINED,
                            icon_color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_500,
                            width=42,
                            height=42,
                            tooltip="Anonymize text",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=6),
                            ),
                            on_click=anonymize_text,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            spacing=20,
        ),
    )


def build_file_anonymization_card(
        page: ft.Page,
        discussion_uuid: str,
        discussion_service: MongoDiscussionService,
        language_state: dict,
        set_result: callable,
):
    file_anonymizer_fr = FileAnonymization(language="fr")
    file_anonymizer_en = FileAnonymization(language="en")
    anonymized_files: list[dict[str, bytes | str]] = []

    selected_files_text = ft.Text(
        "No files selected",
        size=12,
        color=ft.colors.GREY_600,
        text_align=ft.TextAlign.CENTER,
        overflow=ft.TextOverflow.ELLIPSIS,
        max_lines=4,
    )

    download_all_button = ft.ElevatedButton(
        text="Download all anonymized files",
        icon=ft.icons.DOWNLOAD_OUTLINED,
        disabled=True,
    )

    def create_anonymized_files_zip() -> bytes:
        zip_buffer = io.BytesIO()

        with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
            for anonymized_file in anonymized_files:
                filename = str(anonymized_file["filename"])
                content = anonymized_file["content"]

                if isinstance(content, bytes):
                    zip_file.writestr(filename, content)

        return zip_buffer.getvalue()

    def on_download_location_selected(e: ft.FilePickerResultEvent):
        if not e.path:
            set_result("Download was cancelled.")
            return

        try:
            zip_bytes = create_anonymized_files_zip()

            with open(e.path, "wb") as output_file:
                output_file.write(zip_bytes)

            set_result(f"Downloaded {len(anonymized_files)} anonymized files to:\n{e.path}")

        except Exception as exc:
            set_result(f"Could not download anonymized files: {exc}")

    download_picker = ft.FilePicker()
    download_picker.on_result = on_download_location_selected

    if download_picker not in page.overlay:
        page.overlay.append(download_picker)

    async def download_all_files(e):
        if not anonymized_files:
            set_result("No anonymized files are available to download yet.")
            return

        try:
            if download_picker not in page.overlay:
                page.overlay.append(download_picker)
                page.update()

            await download_picker.save_file(
                dialog_title="Save anonymized files",
                file_name="anonymized_files.zip",
                allowed_extensions=["zip"],
            )

        except Exception as exc:
            set_result(f"Could not open download dialog: {exc}")

    download_all_button.on_click = download_all_files

    def on_file_selected(e: ft.FilePickerResultEvent):
        if not e.files:
            selected_files_text.value = "No files selected"
            selected_files_text.update()
            set_result("File selection was cancelled.")
            return

        selected_file_names = [file.name for file in e.files]
        selected_files_text.value = "\n".join(selected_file_names)
        selected_files_text.update()

        try:
            set_result(f"Anonymizing {len(e.files)} files, please wait...")
            lang = language_state["current"]
            file_anonymizer = file_anonymizer_en if lang == "en" else file_anonymizer_fr

            success_count = 0
            anonymized_files.clear()

            for file in e.files:
                file_path = file.path
                if not file_path:
                    continue

                result = file_anonymizer.anonymize(file_path)

                # Map extension to content type
                ext = Path(file_path).suffix.lower()
                content_type = "application/octet-stream"
                if ext == ".pdf":
                    content_type = "application/pdf"
                elif ext == ".docx":
                    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif ext == ".odt":
                    content_type = "application/vnd.oasis.opendocument.text"
                elif ext == ".txt":
                    content_type = "text/plain"

                file_id = discussion_service.save_file(
                    discussion_uuid=discussion_uuid,
                    filename=result.output_filename,
                    content=result.file_bytes,
                    content_type=content_type,
                )

                anonymized_files.append(
                    {
                        "file_id": str(file_id),
                        "filename": result.output_filename,
                        "content": result.file_bytes,
                        "content_type": content_type,
                    }
                )

                discussion_service.save_prompt(
                    discussion_uuid=discussion_uuid,
                    prompt=result.response.originalText,
                    anonymized_text=result.response.anonymizedText,
                    match_table=result.response.matchTable,
                )
                success_count += 1

            download_all_button.disabled = success_count == 0
            download_all_button.update()

            set_result(f"Successfully anonymized {success_count} files.")

        except Exception as exc:
            set_result(f"Error: {exc}")

    file_picker = ft.FilePicker()
    file_picker.on_result = on_file_selected

    if file_picker not in page.overlay:
        page.overlay.append(file_picker)

    async def pick_files(e):
        try:
            if file_picker not in page.overlay:
                page.overlay.append(file_picker)
                page.update()

            await file_picker.pick_files(
                dialog_title="Select files to anonymize",
                allow_multiple=True,
                allowed_extensions=["pdf", "docx", "odt", "txt"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )

        except Exception as exc:
            set_result(f"Could not open file picker: {exc}")

    upload_box = ft.Container(
        width=305,
        height=100,
        border=ft.border.all(1, ft.colors.GREY_400),
        border_radius=6,
        padding=ft.padding.all(12),
        on_click=pick_files,
        ink=True,
        content=ft.Column(
            controls=[
                ft.Icon(
                    ft.icons.ADD_BOX_OUTLINED,
                    size=30,
                    color=ft.colors.BLACK,
                ),
                ft.Text(
                    "Click to select files",
                    size=13,
                    color=ft.colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                selected_files_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5,
        ),
    )

    return ft.Container(
        width=350,
        height=245,
        padding=ft.padding.all(22),
        bgcolor=ft.colors.WHITE,
        border_radius=8,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=14,
            color=ft.colors.with_opacity(0.09, ft.colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
        content=ft.Column(
            controls=[
                section_title("File Anonymization"),
                upload_box,
                download_all_button,
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

def build_anonymizer_page(page: ft.Page):
    discussion_uuid = str(uuid.uuid4())
    discussion_service = MongoDiscussionService()
    language_state = {"current": "fr"}

    result_text = ft.Text(
        "Results will appear here...",
        size=14,
        color=ft.colors.BLACK87,
        text_align=ft.TextAlign.CENTER,
        selectable=True,
    )

    def set_result(message: str):
        result_text.value = message
        result_text.update()

    def on_language_change(e):
        language_state["current"] = e.control.value
        page.update()

    language_selector = ft.Dropdown(
        label="Select Language (BERT Model)",
        value="fr",
        options=[
            ft.dropdown.Option("fr", "French (CamemBERT)"),
            ft.dropdown.Option("en", "English (BERT Large)"),
        ],
        width=300,
    )
    language_selector.on_change = on_language_change

    return ft.Container(
        expand=True,
        bgcolor=ft.colors.WHITE,
        padding=ft.padding.only(top=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    controls=[language_selector],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    controls=[
                        build_text_anonymization_card(
                            discussion_uuid=discussion_uuid,
                            discussion_service=discussion_service,
                            language_state=language_state,
                            set_result=set_result,
                        ),
                        build_file_anonymization_card(
                            page=page,
                            discussion_uuid=discussion_uuid,
                            discussion_service=discussion_service,
                            language_state=language_state,
                            set_result=set_result,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=32,
                ),
                ft.Row(
                    controls=[
                        result_box(
                            "ANONYMIZATION OUTPUT",
                            result_text,
                            250,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )