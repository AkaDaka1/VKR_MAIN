from PySide6.QtWidgets import QDialogButtonBox


def localize_dialog_buttons(button_box: QDialogButtonBox):
    """Translate standard dialog buttons to Russian."""
    ok_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)
    cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)

    if ok_btn is not None:
        ok_btn.setText("ОК")
    if cancel_btn is not None:
        cancel_btn.setText("Отмена")
