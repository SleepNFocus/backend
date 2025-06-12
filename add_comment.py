# 작성자: 한율
# D:\project\add_comment.py

import os

comment_line = "# 작성자: 한율\n"
root_dir = "."

for root, _, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py") and "venv" not in root:
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if lines and lines[0].strip() == comment_line.strip():
                continue

            with open(path, "w", encoding="utf-8") as f:
                f.write(comment_line + "".join(lines))
