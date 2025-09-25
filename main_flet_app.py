# main_flet_app.py
import os

import flet as ft

from backend_controller import RAGSystem


def main(page: ft.Page):
    page.title = "Asistente de Investigación RAG"
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    try:
        rag_system = RAGSystem()
    except Exception as e:
        page.add(ft.Text(f"Error fatal al iniciar el backend: {e}", color="red"))
        return

    state = {"selected_document_id": None, "selected_prompt_name": None}

    # --- Componentes UI ---
    doc_dropdown = ft.Dropdown(
        on_change=lambda e: set_state("selected_document_id", e.control.value),
        hint_text="Selecciona un documento...",
        expand=True  # <--- SOLUCIÓN
    )
    prompt_dropdown_chat = ft.Dropdown(
        on_change=lambda e: set_state("selected_prompt_name", e.control.value),
        hint_text="Selecciona una personalidad...",
        expand=True  # <--- SOLUCIÓN
    )
    chat_view = ft.ListView(expand=True, auto_scroll=True, spacing=10)
    user_input = ft.TextField(label="Escribe tu pregunta...", expand=True, multiline=True, shift_enter=True)
    send_button = ft.IconButton(icon=ft.Icons.SEND, tooltip="Enviar Pregunta")
    progress_ring_chat = ft.ProgressRing(visible=False, width=20, height=20)
    source_input = ft.TextField(label="Pega una URL o selecciona un archivo local", expand=True)
    add_button = ft.ElevatedButton(text="Añadir a la Biblioteca")
    progress_indicator_library = ft.Row(controls=[ft.ProgressRing(), ft.Text("Procesando...")], visible=False)
    library_list_view = ft.ListView(expand=True, spacing=5)
    prompt_dropdown_editor = ft.Dropdown(label="Seleccionar Personalidad para Editar")
    prompt_name_input = ft.TextField(label="Nombre de la Personalidad")
    prompt_content_input = ft.TextField(label="Contenido (usa {context} y {question})", multiline=True, min_lines=15, expand=True)
    save_prompt_button = ft.ElevatedButton(text="Guardar Personalidad")
    new_prompt_button = ft.ElevatedButton(text="Nuevo")

    def set_state(key, value):
        state[key] = value

    def show_snackbar(message, color):
        page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def copy_to_clipboard(e):
        text_to_copy = e.control.data
        page.set_clipboard(text_to_copy)
        show_snackbar("Texto copiado al portapapeles", ft.Colors.GREEN)

    def update_library_list():
        library_summary = rag_system.get_library_summary()
        library_list_view.controls.clear()
        doc_options = []
        for doc_info in library_summary:
            library_list_view.controls.append(
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.DESCRIPTION),
                        title=ft.Text(doc_info['titulo'], weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"Autor: {doc_info['autor']} | Fecha: {doc_info['fecha']}\nTags: {doc_info['tags']}"),
                        trailing=ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE, tooltip="Eliminar Documento",
                            data=doc_info['id'], on_click=handle_delete_document
                        )
                    )
                )
            )
            doc_options.append(ft.dropdown.Option(key=doc_info['id'], text=doc_info['titulo']))
        doc_dropdown.options = doc_options
        page.update()

    def handle_add_document(e):
        source = source_input.value
        if not source:
            show_snackbar("Por favor, introduce una URL o selecciona un archivo.", ft.Colors.AMBER)
            return
        add_button.disabled = True
        progress_indicator_library.controls[1].value = "Paso 1/3: Extrayendo texto..."
        progress_indicator_library.visible = True
        page.update()
        extract_result = rag_system.extract_and_analyze(source)
        if not extract_result["success"]:
            show_snackbar(extract_result["message"], ft.Colors.RED)
            add_button.disabled = False; progress_indicator_library.visible = False
            page.update()
            return
        progress_indicator_library.controls[1].value = "Paso 2/3: Analizando con IA..."
        page.update()
        progress_indicator_library.controls[1].value = "Paso 3/3: Indexando en la biblioteca..."
        page.update()
        index_result = rag_system.chunk_and_index(
            source=source,
            text_to_chunk=extract_result["extracted_text"],
            analysis_data=extract_result["analysis_data"]
        )
        add_button.disabled = False
        progress_indicator_library.visible = False
        source_input.value = ""
        if index_result["success"]:
            show_snackbar(index_result["message"], ft.Colors.GREEN)
            update_library_list()
        else:
            show_snackbar(index_result["message"], ft.Colors.RED)
        page.update()

    def handle_delete_document(e):
        result = rag_system.delete_document(e.control.data)
        show_snackbar(result["message"], ft.Colors.GREEN if result["success"] else ft.Colors.RED)
        update_library_list()
    
    def handle_send_message(e):
        if not state["selected_document_id"]: show_snackbar("Selecciona un tratado.", ft.Colors.AMBER); return
        if not state["selected_prompt_name"]: show_snackbar("Selecciona una personalidad.", ft.Colors.AMBER); return
        question = user_input.value
        if not question: return

        send_button.disabled = True; progress_ring_chat.visible = True
        chat_view.controls.append(ft.Card(ft.Container(ft.Text(f"Tú: {question}"), padding=10)))
        user_input.value = ""; page.update()

        answer, context, _ = rag_system.query_document(question, state["selected_document_id"], state["selected_prompt_name"])
        
        sources_view = ft.ExpansionTile(
            title=ft.Text("Fuentes Consultadas"),
            controls=[
                ft.Row([
                    ft.Text(context, selectable=True, font_family="monospace", expand=True),
                    ft.IconButton(icon=ft.Icons.COPY, tooltip="Copiar Fuentes", on_click=copy_to_clipboard, data=context)
                ])
            ]
        )
        
        response_card = ft.Card(
            ft.Container(
                content=ft.Column([
                    ft.Row(
                        [
                            ft.Text(f"{state['selected_prompt_name']}:", weight=ft.FontWeight.BOLD, expand=True),
                            ft.IconButton(icon=ft.Icons.COPY, tooltip="Copiar Respuesta", on_click=copy_to_clipboard, data=answer),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Markdown(answer, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, on_tap_link=lambda e: page.launch_url(e.data)),
                    sources_view if context else ft.Container(),
                ]),
                padding=10,
            ),
            color=ft.Colors.BLUE_GREY_900,
        )
        
        chat_view.controls.append(response_card)

        send_button.disabled = False; progress_ring_chat.visible = False
        page.update()

    def update_prompt_dropdowns():
        prompts = rag_system.list_prompts()
        options = [ft.dropdown.Option(p) for p in prompts]
        prompt_dropdown_chat.options = options
        prompt_dropdown_editor.options = options
        page.update()

    def handle_prompt_select(e):
        prompt_name = e.control.value
        content = rag_system.get_prompt_content(prompt_name)
        if content: prompt_name_input.value = prompt_name; prompt_content_input.value = content; page.update()

    def handle_save_prompt(e):
        name, content = prompt_name_input.value, prompt_content_input.value
        if not name or not content: show_snackbar("El nombre y contenido son obligatorios.", ft.Colors.AMBER); return
        result = rag_system.save_prompt(name, content)
        show_snackbar(result["message"], ft.Colors.GREEN if result["success"] else ft.Colors.RED)
        if result["success"]: update_prompt_dropdowns()

    def handle_new_prompt(e):
        prompt_name_input.value = ""; prompt_content_input.value = ""; prompt_dropdown_editor.value = None
        page.update()

    add_button.on_click = handle_add_document
    send_button.on_click = handle_send_message
    prompt_dropdown_editor.on_change = handle_prompt_select
    save_prompt_button.on_click = handle_save_prompt
    new_prompt_button.on_click = handle_new_prompt
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files: source_input.value = e.files[0].path; page.update()
            
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    browse_button = ft.IconButton(icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: file_picker.pick_files(allow_multiple=False))

    tabs = ft.Tabs(
        selected_index=0, expand=True,
        tabs=[
            ft.Tab(text="Consulta", icon=ft.Icons.QUESTION_ANSWER, content=ft.Column(controls=[
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("1. Selecciona un Tratado para Consultar", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                                doc_dropdown,
                            ],
                            expand=True
                        ),
                        ft.Column(
                            [
                                ft.Text("2. Selecciona una Personalidad", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                                prompt_dropdown_chat,
                            ],
                            expand=True
                        ),
                    ],
                    spacing=10
                ),
                ft.Divider(), 
                chat_view, 
                ft.Divider(), 
                ft.Row([user_input, send_button, progress_ring_chat])
            ], expand=True)),
            ft.Tab(text="Biblioteca", icon=ft.Icons.BOOK, content=ft.Column(controls=[ft.Text("Añadir Nuevo Tratado", style=ft.TextThemeStyle.HEADLINE_SMALL), ft.Row([source_input, browse_button, add_button]), progress_indicator_library, ft.Divider(), ft.Text("Tratados en la Biblioteca", style=ft.TextThemeStyle.HEADLINE_SMALL), library_list_view], expand=True, spacing=10)),
            ft.Tab(text="Personalidades", icon=ft.Icons.PSYCHOLOGY, content=ft.Column(controls=[prompt_dropdown_editor, prompt_name_input, prompt_content_input, ft.Row([save_prompt_button, new_prompt_button])], expand=True))
        ]
    )
    page.add(tabs)
    update_library_list()
    update_prompt_dropdowns()

if __name__ == "__main__":
    ft.app(target=main)