#import "@preview/gantty:0.5.1": gantt

#let authors = (
  (name: "Charbel ABOU KHEIR", email: "charbel.aboukheir@telecom-paris.fr"),
  (name: "Jean Paul AL AM", email: "jean.alam@telecom-paris.fr"),
  (name: "Arsène MALLET", email: "arsene.mallet@telecom-paris.fr"),
  (name: "Marie-José TANNOURY", email: "marie-jose.tannoury@telecom-paris.fr"),
  (name: "Alain TRAD", email: "alain.trad@telecom-paris.fr"),
)
#let superviser = (name: "Anne-Flore Cabouat", email:
"anne-flore.cabouat@inria.fr")

#let etc = smallcaps[etc.]

#set text(lang: "en")
#set page(
  paper: "a4",
  numbering: "1 of 1",
  margin: (
    top: 2cm,
    bottom: 2cm,
    left: 1cm,
    right: 2cm,
  ),
  header: [
    _DSAI Project_
    #h(1fr)
    _Telecom Paris_
  ],
  footer: [
    _#(datetime.today().display())_
    #h(1fr)
    #context[
      _#counter(page).display("1") of #counter(page).final().at(0)_
    ]
  ]
)

#align(center)[
  #stack(
    dir: ttb,
    spacing: 1em,
    text(1.5em, weight: "bold")[AOIs extraction in SVGs],
    text(1.2em, style: "italic", weight: 550)[
      Project Plan
    ],
  )
  #v(0.5em)
  #(authors.map(a => {
    link("mailto:" + a.email, box(a.name))
  }).join(", ")).

  _Under the supervision of #(link("mailto:" + superviser.email,
  superviser.name))._
]
#line(length: 100%, stroke: 0.5pt)
#v(1em)

= Presentation and discussion

This project's goal is to extract and visualize the Area of Interests (AOIs) of
heterogeneous SVG files (Scalable Vector Graphics). The SVGs we are working on
are already data visualizations, and have a somewhat shared structure (legends,
labels, axis, #(etc)).

Given what we understood and the discussions we had with our supervisor, the
task here is not to build a data model, or using machine learning techniques to
make statistical AOI recognition (furthermore, given the small dataset we're
given to work on, it would've been difficult), but rather to use deterministic
methods and algorithms to parse, semantically analyze and build a structured
representation of the AOIs in a given SVG, such as a tree structure.

After getting a working extraction, the goal of the project is also to provide
the appropriate pipeline and visualization tooling to utilize the extraction
algorithm(s) efficiently. We think that a big part of the project and
time-investment will be dedicated to this as well, and must thus not be
neglected or underestimated.

= Schedule

Below is an indicative yet realistic schedule developed by the team. We have
aimed for a balance between being specific and not overly exhaustive, ensuring
this schedule provides a high-level overview of our project's progress.

#gantt(yaml("schedule.yaml"))

= Roles

The following is an initial breakdown of the roles we have assigned ourselves
for the project. The goal of this allocation is to ensure clear ownership and
accountability for every aspect of the project. However, these roles remain
flexible and may be adjusted as the project evolves.

- *C. ABOU KHEIR*: 
- *J-P. AL AM*: 
- *A. MALLET*: 
- *M-J. TANNOURY*: 
- *A. TRAD*: 

