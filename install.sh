#!/usr/bin/env bash
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
archive="$script_dir/triminput-pvm-sdk.tar.gz"
prefix=/opt/triminput-pvm

if [ "$(id -u)" -ne 0 ]; then
    exec sudo bash "$script_dir/install.sh"
fi

if [ ! -f "$archive" ]; then
    echo "SDK archive not found: $archive" >&2
    exit 1
fi

rm -rf "$prefix"
tar -xzf "$archive" -C /opt

python_bin=
for candidate in "$prefix"/bin/python3.[0-9]*; do
    if [ -x "$candidate" ]; then
        python_bin=$candidate
        break
    fi
done

if [ -z "$python_bin" ]; then
    echo "No versioned Python executable found under $prefix/bin" >&2
    exit 1
fi

ln -sfn "$python_bin" /usr/local/bin/triminput-python
echo "Installed $python_bin as /usr/local/bin/triminput-python"
