from contentgen.model.project import Family

# Familias de texto
_READ_ONLY = {
    "TextView", "android.widget.TextView",
    "androidx.appcompat.widget.AppCompatTextView",
    "com.google.android.material.textview.MaterialTextView",
    "android.support.v7.widget.AppCompatTextView"
}

_EDITABLE = {
    "EditText", "android.widget.EditText",
    "AutoCompleteTextView", "android.widget.AutoCompleteTextView",
    "MultiAutoCompleteTextView", "android.widget.MultiAutoCompleteTextView",
    "androidx.appcompat.widget.AppCompatEditText",
    "androidx.appcompat.widget.AppCompatAutoCompleteTextView",
    "androidx.appcompat.widget.AppCompatMultiAutoCompleteTextView",
    "com.google.android.material.textfield.TextInputEditText",
    "com.google.android.material.textfield.MaterialAutoCompleteTextView",
    "android.support.v7.widget.AppCompatEditText",
    "android.support.v7.widget.AppCompatAutoCompleteTextView",
    "android.support.v7.widget.AppCompatMultiAutoCompleteTextView",
    "android.support.design.widget.TextInputEditText"
}

_CONTROL = {
    "Button", "android.widget.Button",
    "CheckBox", "android.widget.CheckBox",
    "RadioButton", "android.widget.RadioButton",
    "Switch", "android.widget.Switch",
    "ToggleButton", "android.widget.ToggleButton",
    "CheckedTextView", "android.widget.CheckedTextView",
    "androidx.appcompat.widget.AppCompatButton",
    "androidx.appcompat.widget.AppCompatCheckBox",
    "androidx.appcompat.widget.AppCompatRadioButton",
    "androidx.appcompat.widget.AppCompatToggleButton",
    "androidx.appcompat.widget.AppCompatCheckedTextView",
    "androidx.appcompat.widget.SwitchCompat",
    "com.google.android.material.button.MaterialButton",
    "com.google.android.material.checkbox.MaterialCheckBox",
    "com.google.android.material.radiobutton.MaterialRadioButton",
    "com.google.android.material.switchmaterial.SwitchMaterial",
    "com.google.android.material.materialswitch.MaterialSwitch",
    "com.google.android.material.chip.Chip",
    "android.support.v7.widget.AppCompatButton",
    "android.support.v7.widget.AppCompatCheckBox",
    "android.support.v7.widget.AppCompatRadioButton",
    "android.support.v7.widget.AppCompatCheckedTextView",
    "android.support.v7.widget.SwitchCompat"
}

# Contenedores con semántica de campo
_CONTAINERS = {
    "com.google.android.material.textfield.TextInputLayout",
    "android.support.design.widget.TextInputLayout"
}

def resolve_element_class(tag: str, class_attr: str | None) -> str:
    """
    Resuelve la clase real del elemento. Si es el elemento genérico, 
    extrae la clase del atributo.
    """
    if tag.lower() == "view" and class_attr:
        return class_attr
    return tag

def get_family(element_class: str) -> Family | None:
    """
    Asigna la familia según la clase.
    Devuelve None si no pertenece a ninguna de las listas.
    """
    if element_class in _READ_ONLY:
        return Family.READ_ONLY
    if element_class in _EDITABLE:
        return Family.EDITABLE
    if element_class in _CONTROL:
        return Family.CONTROL
    return None

def is_field_container(element_class: str) -> bool:
    """Detecta si el elemento es un contenedor que aporta semántica al campo."""
    return element_class in _CONTAINERS