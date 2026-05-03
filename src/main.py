import flet as ft

from views.anonymizer_page import build_anonymizer_page


def main(page: ft.Page):
    page.title = "Zero Context"
    page.padding = 0
    page.bgcolor = ft.Colors.WHITE
    page.window.width = 900
    page.window.height = 780

    content_area = ft.Container(expand=True)

    content_area.content = build_anonymizer_page(page)

    root = ft.Column(
        controls=[
            content_area,
        ],
        spacing=0,
        expand=True,
    )

    page.add(root)


if __name__ == "__main__":
    ft.app(target=main)