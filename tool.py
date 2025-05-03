"""
title: File Search Tool
author: RJTPP
author_url: https://github.com/RJTPP
git_url: https://github.com/RJTPP/open-webui-file-search-tool.git
repo_url: https://github.com/RJTPP/open-webui-file-search-tool
version: 0.0.1
license: MIT

description: An interactive tool for navigating directories, listing files, searching filenames and content using regex, and reading file contents.
"""

import os
import json
from pathlib import Path
import re
from pydantic import BaseModel, Field
from datetime import datetime
from collections import deque
import itertools

def pwd():
    return os.getcwd()


class Tools:
    class Valves(BaseModel):
        BASE_DIR: str = Field(
            default=None,
            description="The base directory to start the search from. Defaults to the current directory.",
        )

    def __init__(self):
        """Initialize the Tool."""
        self.valves = self.Valves()
        self.root_path = Path(pwd()).root
        self.init_dir = Path(self.valves.BASE_DIR).absolute().as_posix() if self.valves.BASE_DIR else pwd()
        self.base_dir = self.init_dir

    def get_current_dir(self, __event_emitter__=None) -> dict[str, str]:
        """
        Get the current directory. Equivalent to `pwd`.

        :return: Dict with:
            - 'current_dir': Absolute path of the current directory.
        """
        return { "current_dir": self.base_dir}

    async def change_dir(self, path: str, __event_emitter__=None) -> dict[str, str | bool]:
        """
        Change the current directory. Equivalent to `cd`.

        :param path: Path to change to. Set to None to revert to the initial directory.
        :return: Dict with:
            - 'success': 'True' or 'False'
            - 'response_message': Absolute path of the new current directory.
        """
        if not path:
            path = self.init_dir
            
        if not os.path.exists(path):
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Directory {path} does not exist.",
                        "done": True,
                        "hidden": False,
                    },
                }
            )
            return {
                "success": False,
                "response_message": f"Directory `{path}` does not exist. Reverting to `{self.base_dir}`."
            }
        
        self.base_dir = Path(path).absolute().as_posix()
        
        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": f"Changed working directory to {self.base_dir}.",
                    "done": True,
                    "hidden": False,
                },
            }
        )
        
        return {
            "success": True,
            "response_message": f"Changed directory to `{self.base_dir}`."
        }
    

    def get_path_type(self, paths: list[str], __event_emitter__=None) -> dict[str, list[tuple[str, str]]]:
        """
        Get the type of the given path.

        :param paths: List of paths or a single path to get the type of.
        :return: Dict with:
            - 'path_type': List of tuples of (path, type).
        """
        def _sub_get_path_type(path: str) -> str:
            if not os.path.exists(path):
                return "not found"
            file_type = "unknown"
            if os.path.isdir(path):
                file_type = "directory"
            elif os.path.islink(path):
                file_type = "symbolic link"
            elif os.path.isfile(path):
                file_type = "file"
            return file_type
        
        return { "path_type": [(p, _sub_get_path_type(p)) for p in paths]}


    async def list_files(
        self,
        base_dir: str = None,
        show_hidden: bool = False,
        limit: int = -1,
        start_from: int = 0,
        abs_path: bool = False,
        __event_emitter__=None,
    ) -> dict[str, list[str] | None]:
        """
        List files in the given directory.

        :param base_dir: Base directory to start the search from.
        :param show_hidden: Include hidden files (those starting with '.').
        :param limit: Maximum number of files to return. Set to -1 for no limit.
        :param start_from: Starting index of files to return.
        :param abs_path: If true, return absolute paths.
        :return: Dict with:
            - 'results': List of files. Sorted alphabetically.
            - 'response_message': Response message.
            - 'time_elapsed': Time elapsed in seconds.
        """
        base_dir = os.path.abspath(base_dir) if base_dir else self.base_dir
        if base_dir == "":
            base_dir = pwd()
        results: list[str] = []
        count = 0
        is_exceeded = False
        start_time = datetime.now()
        
        await __event_emitter__(
            {
                "type": "status",  # We set the type here
                "data": {
                    "description": f"Finding files in {base_dir}.",
                    "done": False,
                    "hidden": False,
                },
                # Note done is False here indicating we are still emitting statuses
            }
        )

        all_files = [f for f in os.listdir(base_dir) if show_hidden or not f.startswith(".")]
        all_files.sort()

        if start_from > 0:
            all_files = all_files[start_from:]

        for fname in all_files:

            full = os.path.join(base_dir, fname)
            rel = os.path.relpath(full, base_dir)
            results.append(full if abs_path else rel)
            count += 1

            await __event_emitter__(
                {
                    "type": "status",  # We set the type here
                    "data": {
                        "description": f"Found {len(results)} files from {base_dir}.",
                        "done": False,
                        "hidden": False,
                    },
                    # Note done is False here indicating we are still emitting statuses
                }
            )

            if limit >= 0 and count >= limit:
                is_exceeded = True
                break

        res = {
            "results": results,
            "time_elapsed": (datetime.now() - start_time).total_seconds(),
        }
        
        if is_exceeded:
            res["response_message"] = f"Limit exceeded. Returned {len(results)}/{len(all_files)} files."
        else:
            res["response_message"] = f"Found {len(results)} files from {base_dir}."

        await __event_emitter__(
            {
                "type": "status",  # We set the type here
                "data": {
                    "description": f"Found {len(results)} files from {base_dir}.",
                    "done": True,
                    "hidden": False,
                },
                # Note done is False here indicating we are still emitting statuses
            }
        )

        return res


    async def search_file_name(
        self,
        regex_pattern: list[str],
        exclude_regex_patterns: list[str] = None,
        path: str = None,
        time_limit: int = 5,
        max_level: int = -1,
        __event_emitter__=None
    ) -> dict[str, list[str] | None]:
        """
        Search for files whose **path** match the given regex, level‑by‑level.

        :param regex_pattern: A list of **regex** pattern to match against filenames. Be sure to escape special characters.
        :param exclude_regex_patterns: a list of **regex** patterns to exclude.
        :param path:          Directory to start from (defaults to base_dir).
        :param time_limit:    Seconds after which to abort (-1 = no limit).
        :param max_level:     Depth to recurse: 0 = only root, 1 = root+its subdirs, -1 = unlimited.
        :return:              Dict with
            - 'results': List of files matching regex. Sorted alphabetically.
            - 'response_message': Response message.
            - 'time_elapsed': Time elapsed in seconds.
        """
        if path in [None, ""]:
            path = self.base_dir
            
        if not os.path.exists(path):
            return {
                "results": [],
                "response_message": f"Path `{path}` does not exist.",
                "time_elapsed": 0.0
            }
        if exclude_regex_patterns is None:
            exclude_regex_patterns = []
        start_time = datetime.now()
        pat = [re.compile(p) for p in regex_pattern]
        ex_pat = [re.compile(p) for p in exclude_regex_patterns]
        root = os.path.abspath(path or self.base_dir)
        
        
        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": f"Searching for {', '.join(regex_pattern)} in {root}.",
                    "done": False,
                    "hidden": False,
                },
            }
        )
        
        results: list[str] = []
        queue = deque([(root, 0)])  # (directory, current_level)
        
        while queue:
            current_dir, level = queue.popleft()
            
            if any(p.search(current_dir) for p in ex_pat):
                continue  # skips everything for this directory
            
            # time‑quit check
            if time_limit != -1 and (datetime.now() - start_time).total_seconds() > time_limit:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Time limit exceeded. Found {len(results)} files",
                            "done": True,
                            "hidden": False,
                        },
                    }
                )
                return {
                    "results": results,
                    "response_message": f"Time limit exceeded after {level} levels. Found {len(results)} files.",
                    "time_elapsed": (datetime.now() - start_time).total_seconds(),
                }
            
            try:
                entries = os.listdir(current_dir)
            except (PermissionError, FileNotFoundError):
                continue
            
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Searching for {', '.join([p.pattern for p in pat])} in {current_dir}.",
                        "done": False,
                        "hidden": False,
                    },
                }
            )
            
            
            for name in entries:
                full_path = os.path.join(current_dir, name)
                
                # If it’s a file and matches, record it

                if not os.path.isdir(full_path):
                    for p in pat:
                        if p.search(name):
                            results.append(full_path)
                            break
                
                # If it’s a directory and we haven’t hit max_level, enqueue its contents
                if os.path.isdir(full_path):
                    if max_level < 0 or level < max_level:
                        queue.append((full_path, level + 1))
                        
        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": f"Found {len(results)} matching files.",
                    "done": True,
                    "hidden": False,
                },
            }
        )
        
        results.sort()
        
        return {
            "results": results,
            "response_message": f"Found {len(results)} matching files.",
            "time_elapsed": (datetime.now() - start_time).total_seconds()
        }
    
    
    async def read_file(self, file_paths: list[str], __event_emitter__=None) -> dict[str, list[str] | None]:
        """
        Read the contents of the given files using `open()` function. Cannot read PDFs.

        :param file_paths: List of file paths to read.
        :return: Dict with:
            - 'results': Dict with file paths as keys and file contents as values.
            - 'response_message': Response message.
        """
        if isinstance(file_paths, str):
            file_paths = [file_paths]
            
        results = {}
        for file_path in file_paths:
            file_path = os.path.abspath(file_path)
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Extracting {file_path}.",
                        "done": False,
                        "hidden": False,
                    },
                }
            )
            try:
                with open(file_path, "r") as file:
                    results[file_path] = file.read()
            except FileNotFoundError:
                results[file_path] = "[File not found]"
            except PermissionError:
                results[file_path] = "[Permission denied]"
            except Exception as e:
                results[file_path] = f"[Error: {e}]"
                
        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": f"Extracted {len(results)} files" if len(results) > 1 else f"Extracted {Path(file_path).name}.",
                    "done": True,
                    "hidden": False,
                },
            }
        )
                
        return {
            "results": results,
            "response_message": f"Read {len(results)} files."
        }


    async def search_file_lines(
        self, 
        paths: list[str], 
        regex_patterns: list[str], 
        context_lines: int = 0, 
        time_limit: float = 5.0, 
        __event_emitter__=None
    ) -> dict[str, list[list[str]] | str]:
        """
        Search each file in `paths` for lines matching ANY of `regex_patterns`,
        Returns, for each file that matches, a list of line‑blocks (each block is
        up to `context_lines` before/after the match). If a file cannot be read,
        its value is an error string.

        :param paths:            List of file paths to search.
        :param regex_patterns:   List of regex strings to match lines against.
        :param context_lines:   Number of context lines before and after each match.
        :param time_limit:       Seconds after which to abort early (−1 = no limit).
        :return:                 Dict with:
            - 'results': Dict with file paths as keys and lists of line blocks as values.
            - 'response_message': Response message.
            - 'time_elapsed': Time elapsed in seconds.
        """
        start_time = datetime.now()
        include_re = [re.compile(p) for p in regex_patterns]
        
        results: dict[str, List[list[str]] | str] = {}

        for rel_path in paths:
            # --- Time limit check ---
            if time_limit >= 0 and (datetime.now() - start_time).total_seconds() > time_limit:
                # emit final status
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"Time limit exceeded; processed {len(results)} files.",
                        "done": True,
                        "hidden": False
                    }
                })
                return {
                    "results": results,
                    "response_message": f"Time limit exceeded. processed {len(results)} files.",
                    "time_elapsed": (datetime.now() - start_time).total_seconds()
                }

            abs_path = os.path.abspath(rel_path)

            # --- Emit status per file ---
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"Extracting lines from {abs_path}.",
                    "done": False,
                    "hidden": False
                }
            })

            # --- Read file ---
            matches = []
            
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines):
                    if any(r.search(line) for r in include_re):
                        start = max(0, idx - context_lines)
                        end = min(len(lines), idx + context_lines + 1)
                        block = "".join(lines[start:end])
                        matches.append(block)
                        
            except FileNotFoundError:
                results[rel_path] = "[File not found]"
                continue
            except PermissionError:
                results[rel_path] = "[Permission denied]"
                continue
            except Exception as e:
                results[rel_path] = f"[Error: {e}]"
                continue

            if matches:
                results[rel_path] = matches

        # --- Final status emit ---

        await __event_emitter__({
            "type": "status",
            "data": {
                "description": f"Found {len(results)}/{len(paths)} files containing matches.",
                "done": True,
                "hidden": False
            }
        })

        return {
            "results": results,
            "response_message": f"Processed {len(paths)} files. Found {len(results)} files containing matches.",
            "time_elapsed": (datetime.now() - start_time).total_seconds()
        }
        