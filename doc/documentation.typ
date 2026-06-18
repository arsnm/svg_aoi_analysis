#import "./global.typ": *
#import "./utils.typ": *

#let doc_title = "Documentation"

// configuration and customizations

// Set to false when compiling a *final* version.
#let show-comments = true
#let comment = comment.with(enabled: show-comments)

#set text(
  lang: "en",
)
#set par(
  justify: true,
  leading: 0.55em,
)
#set page(
  paper: "a4",
  numbering: "1 of 1",
  margin: (
    top: 3cm,
    bottom: 2cm,
    left: 2cm,
    right: 2cm,
  ),
  header: [
    _DSAI Project_
    #h(1fr)
    _#(school)_
  ],
  footer: [
    _#(datetime.today().display())_
    #h(1fr)
    #context[
      _#counter(page).display("1") of #counter(page).final().at(0)_
    ]
  ]
)

#show heading.where(level: 1): it => underline(it)

// Start of document
#align(center)[
  #stack(
    dir: ttb,
    spacing: 1em,
    block(width: 75%)[#text(1.5em, weight: "bold", hyphenate: false)[#title]],
    text(1.2em, style: "italic", weight: 550)[
      #(doc_title)
    ],
  )
  #v(0.5em)
  #(authors.map(a => {
    link("mailto:" + a.mail, box(a.name))
  }).join(", ")).

  _Under the supervision of #(link("mailto:" + supervisor.mail,
  supervisor.name))._
]
#line(length: 100%, stroke: 0.5pt)
#v(1em)

#outline(depth: 1)

= Data

= Implementation Prototype
#comment(author: "Arsène")[
  Below I described how I started prototyping the pipeline. To be honest I
  haven't thought about it much, everything was quite naive and to get a first
  architecture of the pipeline that we can build on and improve upon. The point
  was also for me to get familiar with some of the tools we'll probably use. But
  of course, since we haven't even discussed anything concrete yet, do not
  consider that anything below is definitive (as suggested by the term
  _prototype_ #emoji.face.smile).
]

== Parsing an SVG stimuli

The first approach considered is to build a simplified version of the tree
obtained with
#web-link("https://docs.python.org/3/library/xml.etree.elementtree.html")[Python's
built-in XML API]. Still with the idea of simplifying things at first, we remove
from this tree the non-visual or unsupported (_yet_) elements (see
#int-link(<cleaned_elements>)[below] the _current_ cleaned elements)

#let cleaned-elements = (
  "clipPath", "defs", "desc", "filter", "linearGradient", "marker", "mask",
  "metadata", "pattern", "radialGradient", "script", "style", "title",
)

List of the cleaned elements:
#block(width: 100%)[
  #cleaned-elements.map(item => [
    #box([- #raw(item)]) #h(1em)
  ]).join()
] <cleaned_elements>

== AOI Extraction

After building the SVG tree, the next step to extracting the AOIs is to be able
to know where they appear on the screen. To do that, a first approach is to
compute a *bounding* for every element in the tree. This can be done _quite_
easily using the tree structure itself. We first implement methods that compute
the bounding for every SVG visual element (this is done easily for simple
geometrical shapes such as `circle`, `rectangle` or `polygon`, and for the
trickier shapes such as `path`, we'll discuss method later) and after that we go
from the leaf of the tree #sym.dash.em which are these visual elements #sym.dash.em to
the root, uniting the bounding of all the children node at every step.

This approach brings two questions:
 - _What bounding method can we use ?_
 - _Given this bounding method, how to compute a meaningful and efficient union
   ?_

For the bounding, an appropriate method seems to be using polygons. From that
structure, we'll then be able to refine or roughen the level of precision of our
extraction depending on our needs (polygon simplification algorithm:
#web-link("https://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm")[
Ramer-Douglas-Peucker algorithm]).

*TODO*: find an appropriate way to unite two boundings (especially when they're
disjoints).

== AOI Identification

*TODO*.

= Miscellaneous
#comment(author: "Arsène")[
  This section is dedicated to add or specify some information that need to be
  known by the other, without really knowing where (or even if) they belong yet.
]

*Data source to visualization type correspondance:*
- `A-a-[1|2].svg` $arrow.r$ map
- `A-b-[1|2].svg` $arrow.r$ treemap
- `B-a-[1|2].svg` $arrow.r$ scatterplot (_as a weird histogram_)
- `B-b-[1|2].svg` $arrow.r$ scatterplot
- `C-a-[1|2].svg` $arrow.r$ map
- `C-b-[1|2].svg` $arrow.r$ calendar heatmap
- `D-a-[1|2].svg` $arrow.r$ topological map
- `D-b-[1|2].svg` $arrow.r$ graph


