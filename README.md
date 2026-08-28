# Umesh Gautam — Academic Website

A lightweight academic website designed for GitHub Pages. It uses plain HTML, CSS, and JavaScript—no build system and no paid hosting required.

## Files

- `index.html` — all website content
- `styles.css` — design and responsive layout
- `script.js` — mobile navigation and expandable research details
- `assets/Umesh_Gautam_CV.pdf` — CV used by the site
- `assets/Umesh_Gautam_Headshot.jpg` — optimized professional headshot
- `assets/favicon.svg` — browser icon
- `.nojekyll` — tells GitHub Pages to serve the static site directly

## Optional additions

The website is publishable as-is. If you want them, you can later add your Google Scholar, LinkedIn, ORCID, GitHub, or a direct PDF link to the job-market paper.

## Publish free with GitHub Pages

1. Create a GitHub repository named `YOUR-GITHUB-USERNAME.github.io`.
2. Upload the **contents** of this folder to the repository root.
3. Open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select your main branch and the root folder.
6. Your website will then be available at `https://YOUR-GITHUB-USERNAME.github.io/`.

## Preview on your computer

From this folder, run:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000` in a browser.
