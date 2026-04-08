#!/usr/bin/env python3
"""
strip_images.py
Removes all image/SVG content from every markdown post in site/content/posts/.
Runs as part of the GitHub Actions workflow on every deploy.

Strips:
  - <div class="article-illustration">...</div> blocks (old SVG wrappers)
  - Bare <svg ...>...</svg> blocks
  - <img ...> tags
  - image: frontmatter field
"""
import re, os, glob

POSTS_DIR = "site/content/posts"

# Matches <div class="article-illustration" ...> ... </div>  (multiline)
RE_ILLUS = re.compile(
    r'<div[^>]+class=["'][^"']*article-illustration[^"']*["'][^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)

# Matches any <svg ...> ... </svg> block
RE_SVG = re.compile(r'<svg[\s\S]*?</svg>', re.DOTALL | re.IGNORECASE)

# Matches any <img ...> tag (self-closing or not)
RE_IMG = re.compile(r'<img(?:\s[^>]*)?\/?>\s*', re.IGNORECASE)

# Matches "image: ..." frontmatter line
RE_IMG_FM = re.compile(r'^image:.*$', re.MULTILINE)


def clean(content):
    content = RE_ILLUS.sub("", content)
    content = RE_SVG.sub("", content)
    content = RE_IMG.sub("", content)
    content = RE_IMG_FM.sub("", content)
    # Collapse runs of 3+ blank lines down to 2
    content = re.sub(r'\n{3,}', "\n\n", content)
    return content


def main():
    posts = glob.glob(os.path.join(POSTS_DIR, "*.md"))
    cleaned = 0
    for path in posts:
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
        updated = clean(original)
        if updated != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(updated)
            cleaned += 1
    print(f"strip_images: cleaned {cleaned} / {len(posts)} posts")


if __name__ == "__main__":
    main()
