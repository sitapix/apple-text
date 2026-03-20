import { defineConfig } from "astro/config";
import { readFileSync } from "node:fs";
import starlight from "@astrojs/starlight";
import starlightThemeBlack from "starlight-theme-black";

const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] || "apple-text";

const catalog = JSON.parse(
  readFileSync(new URL("../skills/catalog.json", import.meta.url), "utf-8"),
);

const kindSpecs = JSON.parse(
  readFileSync(new URL("../tooling/config/skill-kinds.json", import.meta.url), "utf-8"),
);

const compareSkills = (a, b) =>
  a.entrypoint_priority - b.entrypoint_priority || a.name.localeCompare(b.name);

const skillGroups = kindSpecs.map(({ key, sidebar_label: sidebarLabel }) => ({
  label: sidebarLabel,
  collapsed: true,
  items: catalog.skills
    .filter((s) => s.kind === key)
    .sort(compareSkills)
    .map((s) => ({ label: s.name, slug: `skills/${s.name}` })),
}));

export default defineConfig({
  site: "https://sitapix.github.io",
  base: `/${repoName}`,
  integrations: [
    starlight({
      components: {
        Header: "./src/components/Header.astro",
      },
      plugins: [
        starlightThemeBlack({
          navLinks: [
            { label: "Docs", link: "/guide/quick-start/" },
            { label: "GitHub", link: "https://github.com/sitapix/apple-text" },
          ],
          footerText:
            "Apple Text docs for TextKit, Apple text views, and Writing Tools. Source on [GitHub](https://github.com/sitapix/apple-text).",
        }),
      ],
      title: "Apple Text",
      tagline: "Focused docs for Apple platform text systems.",
      description:
        "Focused docs for the Apple Text Claude plugin: TextKit, UITextView, NSTextView, Writing Tools, routing, and maintenance.",
      disable404Route: true,
      customCss: ["./src/styles/custom.css"],
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/sitapix/apple-text",
        },
      ],
      editLink: {
        baseUrl: "https://github.com/sitapix/apple-text/edit/main/docs/",
      },
      sidebar: [
        {
          label: "Start Here",
          items: [
            { label: "Overview", slug: "index" },
            { label: "Setup", slug: "setup" },
            { label: "Commands", slug: "commands" },
            { label: "Agents", slug: "agents" },
            { label: "Examples", slug: "example-conversations" },
          ],
        },
        {
          label: "Guide",
          autogenerate: { directory: "guide" },
        },
        {
          label: "Skills",
          items: [
            { label: "Overview", slug: "skills" },
            ...skillGroups,
          ],
        },
      ],
    }),
  ],
});
