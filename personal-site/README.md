# William Li — Personal Site

A clean, single‑page personal website generated from the resume. Minimal light theme with Stanford Cardinal as primary color.

Live files
- [index.html](personal-site/index.html)
- [styles.css](personal-site/styles.css)
- [script.js](personal-site/script.js)

What’s included
- Sections: Hero, Education, Experience, Projects, Publications, Skills, Contact, Footer
- Accessible navigation with skip link, sticky header, smooth scrolling, and scroll‑spy active state
- Responsive layout and typography, cards and chips for projects/skills
- Basic SEO: title, description, Open Graph/Twitter tags; JSON‑LD Person schema
- Print stylesheet for clean PDF/print

Customize content
- Update social links in Hero and Contact:
  - LinkedIn: replace placeholders in [index.html](personal-site/index.html)
  - GitHub: replace placeholders in [index.html](personal-site/index.html)
- Resume button: currently links to Google Drive (your provided link). Change if needed in [index.html](personal-site/index.html).
- Projects/Publications: replace placeholder items in [index.html](personal-site/index.html) with your real entries.
- Skills: edit chip lists in [index.html](personal-site/index.html).
- Metadata: update title/description/og:url/og:image in the <head> of [index.html](personal-site/index.html).

Design tokens
- Primary: #8C1515 (Stanford Cardinal)
- Text: #111111
- Muted: #666666
- Background: #ffffff / #fafafa surfaces
- Container width: 960px

Local usage
- Option A: open [index.html](personal-site/index.html) directly in a browser.
- Option B: serve statically (for cleaner anchor/scroll behavior). Any simple static server works.

Assets
- Favicon and social image are referenced from assets/. Add your own:
  - assets/favicon.ico
  - assets/og-image.png

Notes
- The nav highlights the section in view (scroll‑spy) and collapses into a mobile menu under ~860px.
- Print view removes nav/buttons and flattens styles for export.

Future (optional)
- Hosting via GitHub Pages:
  1) Commit this folder to a repository
  2) Push to GitHub
  3) Enable Pages (Settings → Pages → Deploy from main branch)
  4) Update og:url once you have a public URL

License
- Personal use. No license specified.