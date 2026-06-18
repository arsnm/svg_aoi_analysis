#import "./utils.typ": *

#let tp-logo-cover = "./ressources/Logo_Telecom_IPParis_RVB_noir_H.svg"
#let tp-logo-header = "./ressources/Logo_Telecom_IPParis_RVB_noir_V.svg"
#let tp-red = rgb("#bf1238")

#let telecom-paris-report(
  title: none,
  short-title: none,
  subtitle: none,
  authors: (),
  supervisors: (),
  keywords: (),
  abstract: none,
  date: none,
  sidebar-text: none,
  logo: true,
  show-mail: false,
  body
) = {
  // --- COVER PAGE ---
  page(margin: 0pt)[
    #grid(
      columns: (2.5cm, 1fr),
      rows: 100%,

      // --- LEFT SIDEBAR ---
      rect(
        width: 100%,
        height: 100%,
        fill: tp-red,
        stroke: none,
        inset: 0pt,
        align(bottom + center)[
          #pad(bottom: 2cm)[
            #if sidebar-text != none {
              rotate(-90deg, reflow: true)[
                #text(fill: white, size: 1.8em, tracking: 0.1em, weight: "bold",
                smallcaps(sidebar-text))
              ]
            }
          ]
        ]
      ),
      // --- COVER PAGE CONTENT ---
      box(width: 100%, height: 100%)[

        #pad(
          1cm,
          align(center + horizon)[

            #if logo {
              place(
                top + left,
                image(tp-logo-cover, height: 3cm)
              )
            }

            #let group-title = (
              if title != none { text(2.5em, weight: "bold", title) },
              if subtitle != none { text(1.5em, fill: luma(100), subtitle) },
            ).filter(it => it != none)

            #let group-people = (
              if authors.len() > 0 {
                text(1.2em, [
                  #format-names(authors, show-mail: show-mail)
                ])
              },
              if supervisors.len() > 0 {
                text(
                  1.1em,
                  [_Under the supervision of_ \ #v(0.5em)
                   #format-names(supervisors, show-mail: show-mail)],
                )
              },
            ).filter(it => it != none)

            #let group-meta = (
              if abstract != none {
                block(width: 90%)[
                  #set par(justify: true)
                  *Abstract* \
                  #abstract
                ]
              },
              if keywords.len() > 0 { block([*Keywords:* #keywords.join(", ")]) },
            ).filter(it => it != none)

            #let main-blocks = (
              if group-title.len() > 0 { stack(dir: ttb, spacing: 1.5em,
              ..group-title) },

              if group-people.len() > 0 { stack(dir: ttb, spacing: 2em,
              ..group-people) },

              if group-meta.len() > 0 { stack(dir: ttb, spacing: 1.5em,
              ..group-meta) },
            ).filter(it => it != none)

            #stack(dir: ttb, spacing: 4em, ..main-blocks)

            #if date != none {
              place(
                bottom + center, dy: -1cm,
                text(size: 1.2em, fill: luma(80), date)
              )
            }
          ]
        )
      ]
    )
  ]

  // --- CONTENT PAGE FORMAT ---
  set page(
    margin: (top: 3.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    numbering: "1/1",
    header: context {
      set text(size: 0.9em, fill: luma(100))
      let current-page = here().page()
      let active-hdgs = query(selector(heading.where(level: 1))).filter(
        h => h.location().page() <= current-page
      )
      let current-section = if active-hdgs.len() > 0 {
        active-hdgs.first().body
      } else { none }

      grid(
        columns: (1fr, auto),
        gutter: 1.5em,

        align(horizon)[
          #grid(
            columns: (65%, 1fr, auto),
            align(left + horizon)[
              #if short-title != none {
                short-title
              } else if title != none { title }
            ],
            [],
            align(right + horizon)[
              #current-section
            ],
          )
          #v(0.3em)
          #line(length: 100%, stroke: 0.5pt + luma(200))
        ],

        align(right + horizon)[
          #if logo {
            image(tp-logo-header, height: 2cm)
          }
        ]
      )
    },
    footer: context {
      align(right)[
        #text(fill: tp-red, weight: "bold")[
          #counter(page).display("1 / 1", both: true)
        ]
      ]
    }
  )

  show heading: it => {
    let pipes = "|" * it.level
    set text(weight: "semibold")
    block(above: 1.25em, below: 1em)[
      #text(fill: tp-red)[#pipes]
      #h(0.3em)
      #if it.numbering != none {
        counter(heading).display(it.numbering)
        h(0.5em)
      }
      #it.body
    ]
  }

  body
}
