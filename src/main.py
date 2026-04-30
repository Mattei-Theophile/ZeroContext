import flet as ft

from views.anonymizer_page import build_anonymizer_page


def main(page: ft.Page):
    page.title = "Anomizum"
    page.padding = 0
    page.bgcolor = ft.colors.WHITE
    page.window_width = 900
    page.window_height = 780

    content_area = ft.Container(expand=True)

    def build_navbar():
        return ft.Container(
            height=38,
            padding=ft.padding.only(left=8, right=8),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.GREY_300)),
            content=ft.Row(
                controls=[
                    ft.Text("Anomizum Anonymizer", size=16, weight=ft.FontWeight.BOLD),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    content_area.content = build_anonymizer_page(page)

    root = ft.Column(
        controls=[
            build_navbar(),
            content_area,
        ],
        spacing=0,
        expand=True,
    )

    page.add(root)


if __name__ == "__main__":
    ft.app(target=main)