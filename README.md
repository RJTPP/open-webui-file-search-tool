# 📂 File Search Tool

An interactive [OpenWebUI](https://openwebui.com/t/rjtpp/file_search_tool) plugin for searching, reading, and navigating files directly from the UI — with optional regex filtering, status reporting, recursion depth control, and more.

## ✨ Features

- 📁 List files in a directory (with pagination, sorting, and hidden file support)
- 🔍 Search filenames using one or multiple **regex patterns**
- ❌ Exclude paths using **regex exclusion filters**
- 🧠 Read full text files or extract matching lines with context
- 🧭 Change working directory and retrieve current path

## ⚙️ API Overview

| Method                  | Description                                              |
|--------------------------|----------------------------------------------------------|
| `get_current_dir()`      | Get the current working directory                        |
| `change_dir(path)`       | Change directory (reset to initial if `None`)           |
| `list_files(...)`        | List files in a directory (limit, pagination supported) |
| `search_file_name(...)`  | Search file names using regex (with depth/exclude)      |
| `get_path_type(paths)`   | Show the type of each path                              |
| `read_file(file_paths)`  | Read content from text files                            |
| `search_file_lines(...)` | Find lines matching regex (with before/after context)   |


## 📜 License

This project is released under the [MIT License](LICENSE).

You are free to use, modify, and distribute this software under the terms of the MIT License. See the LICENSE file for detailed terms and conditions.
