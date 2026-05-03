// This file is supposed to store some functions, environments, configurations
// that can (or need to) be used a lot throughout the different documents of the
// project.

#let etc = smallcaps[etc.]

#let _show-comments-global = false

// To show some comments directly in the rendered document, make sure the
// parameter `enabled` is set to false before compiling any *final* version.
#let comment(author: "unknown", enabled: none, body) = {
  let is-visible = if enabled != none { enabled } else { _show-comments-global }

  if is-visible {
    block(
      fill: yellow.lighten(80%),
      stroke: 0.5pt + orange,
      inset: 8pt,
      radius: 4pt,
      width: 100%,
      [
        #text(size: 0.8em, weight: "bold", fill: orange.darken(20%))[
          Comment (by #author):
        ] \
        #body
      ]
    )
  }
}

// Custom style for web links.
#let web-link(target, body) = {
  set text(fill: blue)
  underline(stroke: 0.5pt + blue, offset: 2pt)[#link(target, body)]
}

// Custom style for internal links.
#let int-link(target, body) = {
  underline(stroke: 0.5pt, offset: 2pt)[#link(target, body)]
}


