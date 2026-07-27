def pre_find_module_path(hook_api):
    # The embedded Python build used in this environment has a working tkinter,
    # but PyInstaller's Tcl/Tk detector can report it as unavailable. Keep the
    # normal module search path so tkinter is bundled.
    return
