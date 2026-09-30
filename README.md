# Tutorials

Built with [InteractiveCodeScroll](https://github.com/hhkaos/interactive-code-scroll).

Each folder in `tutorials/` is a tutorial, published at `/<folder>/`, with an index page at `/`.

```sh
pnpm install
pnpm dev      # live preview while you write
pnpm build    # static site in dist/
pnpm serve    # serve the built site locally
```

Authoring reference: https://github.com/hhkaos/interactive-code-scroll/blob/main/docs/authoring.md

Publishing: `.github/workflows/pages.yml` deploys to GitHub Pages on every push to `main` (Settings -> Pages -> Source: GitHub Actions).
