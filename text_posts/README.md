# Blog Posts Directory

This directory contains all blog posts for the "Stream of Consciousness" page.

## How to Add a New Blog Post

1. **Create a new `.md` file** in this directory
2. **Name the file** - The filename (without `.md`) will become the post title
3. **Add frontmatter** at the top of the file:

```markdown
---
date: YYYY-MM-DD
---

Your post content here...
```

## Example

**File: `My New Post.md`**

```markdown
---
date: 2024-11-08
---

This is the content of my blog post.

It can have multiple paragraphs.

And they will be preserved with proper spacing.
```

## Features

- **Automatic Loading**: Posts are automatically discovered and loaded
- **Date Sorting**: Posts are sorted by date (newest first)
- **YAML Frontmatter**: Simple metadata format
- **Cached Loading**: Posts are cached for performance
- **Fallback Dating**: If no date is provided, file modification time is used

## Formatting Tips

- Use blank lines between paragraphs
- Indentation is preserved (great for poems!)
- No need to use markdown formatting - plain text works beautifully
- The title comes from the filename, so name it descriptively

## That's It!

No code changes needed. Just add your `.md` file and it will appear automatically.
