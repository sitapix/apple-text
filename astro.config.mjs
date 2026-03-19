import { defineConfig } from "astro/config";
import { readFileSync } from "node:fs";
import starlight from "@astrojs/starlight";

const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] || "apple-text";

const catalog = JSON.parse(
  readFileSync("skills/catalog.json", "utf-8"),
);

const kindSpecs = JSON.parse(
  readFileSync("config/skill-kinds.json", "utf-8"),
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
  base: process.env.GITHUB_ACTIONS ? `/${repoName}` : undefined,
  integrations: [
    starlight({
      title: "Apple Text",
      tagline: "Focused docs for Apple platform text systems.",
      description:
        "Focused docs for the Apple Text Claude plugin: TextKit, UITextView, NSTextView, Writing Tools, routing, and maintenance.",
      customCss: ["./src/styles/custom.css"],
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/sitapix/apple-text",
        },
      ],
      editLink: {
        baseUrl: "https://github.com/sitapix/apple-text/edit/main/",
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
