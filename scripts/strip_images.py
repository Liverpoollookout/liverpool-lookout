#!/usr/bin/env python3
"""
strip_images.py - Remove all images and SVGs from markdown posts.
"""
import re, os, glob

POSTS_DIR = "site/content/posts"

# Match <div class="article-illustration" ...> ... </div>
# [^>]+ covers the attribute regardless of quote style
RE_ILLUS = re.compile(
    r"<div[^>]+article-illustration[^>]*>.*?</div>",
    re.DOTALL | re.IGNORECASE,
)

RE_SVG = re.compile(r"<svg[\s\S]*?</svg>", re.DOTALL | re.IGNORECASE)
RE_IMG = re.compile(r"<img[^>]*>", re.IGNORECASE)
RE_IMG_FM = re.compile(r"^image:.*$", re.MULTILINE)


def clean(content):
    content = RE_ILLUS.sub("", content)
    content = RE_SVG.sub("", content)
    content = RE_IMG.sub("", content)
    content = RE_IMG_FM.sub("", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
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
