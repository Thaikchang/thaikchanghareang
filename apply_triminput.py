from pathlib import Path

root = Path(__file__).resolve().parent
cpython = root / "cpython-src"

p = cpython / "Include/internal/pycore_sysmodule.h"
s = p.read_text()
s = s.replace(
    "extern int _PySys_SetIntMaxStrDigits(int maxdigits);\n",
    "extern int _PySys_SetIntMaxStrDigits(int maxdigits);\n"
    "extern int _PySys_GetAutoTrimInput(void);\n",
)
p.write_text(s)

p = cpython / "Python/sysmodule.c"
s = p.read_text()
s = s.replace(
    "#ifdef HAVE_FCNTL_H\n#  include <fcntl.h>\n#endif\n",
    "#ifdef HAVE_FCNTL_H\n#  include <fcntl.h>\n#endif\n\n"
    "static int pvm_auto_trim_input = 0;\n",
)
needle = "static PyMethodDef sys_methods[] = {\n"
helper = """static PyObject *
sys_set_auto_trim_input(PyObject *Py_UNUSED(module), PyObject *enabled)
{
    int value = PyObject_IsTrue(enabled);
    if (value < 0) {
        return NULL;
    }
    _Py_atomic_store_int_relaxed(&pvm_auto_trim_input, value);
    Py_RETURN_NONE;
}

static PyObject *
sys_get_auto_trim_input(PyObject *Py_UNUSED(module), PyObject *Py_UNUSED(ignored))
{
    return PyBool_FromLong(_Py_atomic_load_int_relaxed(&pvm_auto_trim_input));
}

int
_PySys_GetAutoTrimInput(void)
{
    return _Py_atomic_load_int_relaxed(&pvm_auto_trim_input);
}

"""
s = s.replace(needle, helper + needle)
s = s.replace(
    "    SYS_EXIT_METHODDEF\n",
    "    SYS_EXIT_METHODDEF\n"
    "    {\"get_auto_trim_input\", sys_get_auto_trim_input, METH_NOARGS,\n"
    "     \"Return whether input() trims surrounding whitespace.\"},\n",
    1,
)
s = s.replace(
    "    SYS_MDEBUG_METHODDEF\n",
    "    SYS_MDEBUG_METHODDEF\n"
    "    {\"set_auto_trim_input\", sys_set_auto_trim_input, METH_O,\n"
    "     \"Enable or disable trimming surrounding whitespace from input().\"},\n",
    1,
)
p.write_text(s)

p = cpython / "Python/bltinmodule.c"
s = p.read_text()
s = s.replace(
    '#include "pycore_pythonrun.h"     // _Py_SourceAsString()\n',
    '#include "pycore_pythonrun.h"     // _Py_SourceAsString()\n'
    '#include "pycore_sysmodule.h"     // _PySys_GetAutoTrimInput()\n',
)
needle = '#include "clinic/bltinmodule.c.h"\n'
helper = '''#include "clinic/bltinmodule.c.h"

static PyObject *
builtin_input_trim(PyObject *result)
{
    if (!_PySys_GetAutoTrimInput() || !PyUnicode_Check(result)) {
        return Py_NewRef(result);
    }

    return PyObject_CallMethod(result, "strip", NULL);
}
'''
s = s.replace(needle, helper)
old = '''        if (result != NULL) {
            if (PySys_Audit("builtins.input/result", "O", result) < 0) {
                goto error;
            }
        }
'''
new = '''        if (result != NULL) {
            PyObject *trimmed = builtin_input_trim(result);
            Py_DECREF(result);
            result = trimmed;
        }
        if (result != NULL) {
            if (PySys_Audit("builtins.input/result", "O", result) < 0) {
                Py_DECREF(result);
                goto error;
            }
        }
'''
if old not in s:
    raise RuntimeError("interactive input result block not found")
s = s.replace(old, new, 1)
old = "    tmp = PyFile_GetLine(fin, -1);\n"
new = '''    tmp = PyFile_GetLine(fin, -1);
    if (tmp != NULL) {
        PyObject *trimmed = builtin_input_trim(tmp);
        Py_DECREF(tmp);
        tmp = trimmed;
    }
'''
if old not in s:
    raise RuntimeError("fallback input block not found")
s = s.replace(old, new, 1)
p.write_text(s)
