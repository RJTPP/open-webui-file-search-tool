# 📂 File Search Tool

An interactive [OpenWebUI](https://openwebui.com/t/rjtpp/file_search_tool) plugin for searching, reading, and navigating files directly from the UI — with optional regex filtering, status reporting, recursion depth control, and more.

## ✨ Features

- 📁 List files in a directory with pagination, sorting, and hidden file support
- 🔍 Search filenames using one or multiple **regex patterns** (with BFS or DFS traversal)
- 🧠 Read full file content or extract matching lines with **context windows**
- 🧭 Navigate the filesystem (change and retrieve working directory)
- 🔎 Identify path types (file, directory, symbolic link, or excluded/missing)
- ⏱️ Enforce time limits and depth limits during search operations

## ⚙️ API Overview

| Method                    | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `get_current_dir()`       | Get the current working directory                                           |
| `change_dir(path)`        | Change directory (reset to initial if `None`, enforces exclusions)          |
| `list_file_paths(...)`    | List files in a directory (pagination, hidden toggle, limit control)        |
| `search_file_name(...)`   | Search file names using regex (with BFS/DFS, depth, time limit, exclusions) |
| `get_path_type(paths)`    | Show the type of each path (file, dir, symlink)                             |
| `get_exclude_paths()`     | Returns configured exclude paths from `Valves`                              |
| `read_file(file_paths)`   | Read content from plain text files                                          |
| `search_file_lines(...)`  | Find lines matching regex (with before/after context and exclusion support) |



## ⚠️ Security Notice

This tool provides direct access to your local filesystem, including the ability to read and traverse files recursively.

- It is strongly recommended to use this tool for **local, personal, or trusted environments only**.
- Avoid exposing the tool over public networks without strict access controls.
- Use the `EXCLUDE_PATHS` configuration to restrict access to sensitive directories such as `/home/user`, `/Users`, `/etc`, or cloud-synced locations.

This tool is not hardened for sandboxed or multi-user environments.


## 📜 License

This project is released under the [MIT License](LICENSE).

You are free to use, modify, and distribute this software under the terms of the MIT License. See the LICENSE file for detailed terms and conditions.
