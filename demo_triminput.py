import io
import sys


original_stdin = sys.stdin
original_setting = sys.get_auto_trim_input()

try:
    assert original_setting is False

    sys.stdin = io.StringIO("  hello  \n")
    assert input() == "  hello  "

    sys.set_auto_trim_input(True)
    assert sys.get_auto_trim_input() is True
    sys.stdin = io.StringIO("  hello  \n")
    assert input() == "hello"

    sys.set_auto_trim_input(False)
    assert sys.get_auto_trim_input() is False
    sys.stdin = io.StringIO("  hello  \n")
    assert input() == "  hello  "
finally:
    sys.stdin = original_stdin
    sys.set_auto_trim_input(original_setting)

print("TrimInputPVM demo: PASS")
