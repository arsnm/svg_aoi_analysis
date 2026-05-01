#import "./global.typ": *
#import "@preview/gantty:0.5.1" as gantty
#import "./schedule.typ"

#let doc_title = "Project Plan"

// configuration and customizations
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
    link("mailto:" + a.email, box(a.name))
  }).join(", ")).

  _Under the supervision of #(link("mailto:" + supervisor.email,
  supervisor.name))._
]
#line(length: 100%, stroke: 0.5pt)
#v(1em)

#outline(depth: 1)

= Project Overview

== Description

This project's goal is to extract and visualize the _Area of Interests_
(*AOI*\s) of heterogeneous SVG files (Scalable Vector Graphics). The SVGs we are
working on are already data visualizations, and have a somewhat shared structure
(legends, labels, axes, #(etc)). This extraction's goal is to better interpret
eye-tracking data. Eye-tracking methods record where users look on a chart or
map, but only as coordinates on the screen. Without additional information,
these coordinates ($x,y$) are hard to interpret, since we don't know what part
of the visualization the user is actually looking at, we only know their
placement on the screen.

To make this data meaningful, it needs to be associated with specific elements
of a visualization, such as data points, axes or legend items. This way, instead
of just having positions, we can understand how users interact with the
visualization.

However the challenge is that SVG files are not organized in a consistent way.
Different types of visualizations (maps, treemaps, scatterplots) use different
structures, which makes it challenging to exract a unified representation.
Additionally, important elements are not always clearly labeled or explicitly
defined in SVG files.

Our goal is therefore to build a pipeline that converts heterogeneous SVG
visualizations into a standardized AOI representation, which can be later be
used for eye-tracking data analysis.

== Tasks & Approach

To achieve this, our pipeline must include the following steps:
- Parse SVG files,
- Identify meaningful elements such as data marks, axes, labels, and legend
  items,
- Retrieve semantic information from IDs, classes and group hierarchy,
- Compute bounding boxes for each element,
- Construct a standardized AOI table,
- Build a hierarchical tree representation of each visualization,
- Validate extracted AOIs through manual inspection and consistency checks.

== Data

This project relies on 2 main data sources:
- *Structured SVG files (16 visualizations)* representing heterogeneous
   visualization types (maps, treemaps, scatterplots, #(etc)). These will be the
   input for AOI extraction.
- *Pilot eye-tracking data* containing recorded user gaze coordinates. This data
  will later be used to validate the extracted AOIs and study how users look at
  different parts of a visualization.

== Methods

To turn our project into reality, we'll apply the following methods:
- *Hierarchical SVG parsing*: treating each visualization as a structured tree
  that can be traversed and analyzed.
- *Rule-based semantic extraction*: using SVG tags, IDs, classes and grouping
  structure to identify meaningful visual elements.
- *Geometric AOI modeling*: using bounding boxes and spatial representations to
  define AOIs.
- *Normalization procedures*: to convert heterogeneous SVG structures into a
  standardized AOI representation.

= Timeline

Below is an indicative yet realistic schedule developed by the team. We have
aimed for a balance between being specific and not overly exhaustive, ensuring
this schedule provides a high-level overview of our project's progress.

#schedule

= Roles & Member Tasks

The following is an initial breakdown of the roles we have assigned ourselves
for the project. The goal of this allocation is to ensure clear ownership and
accountability for every aspect of the project. However, these roles remain
flexible and may be adjusted as the project evolves.

== Shared Responsibilities
- Development of the AOI extraction pipeline
- Weekly integration and testing
- Validation and refinement of extraction rules
- Continuous documentation
- Midterm and final presentations

== SVG Exploration (by visualization types)
- *C. ABOU KHEIR: _Mixed Visualization Lead_*
  - Explore edge cases and less structured visualizations.
  - Identify potential challenges for normalization.
- *J. P. AL AM: _Cross-Visualization and Integration Lead_*
  - Compare structural patterns across all visualizations types.
  - Support development of common parsing and normalization rules.
  - Coordinate integration of findings from all members.
- *A. MALLET: _Scatterplot Lead_*
  - Analyze point marks, axes, labels and legend structures.
  - Document recurring semantic patterns.
- *M-J. TANNOURY: _Maps Lead_*
  - Analyze SVG structure and semantic patterns specific to maps.
  - Identify challenges related to geographic marks and labels.
- *A. TRAD: _Treemap Lead_*
  - Explore rectangle hierarchies and grouping structures.
  - Identify AOI extraction challenges specific to treemaps.

== Functional lead roles during implementation
- *C. ABOU KHEIR: _Validation support_*
- *J. P. AL AM: _Integration and documentation support_*
- *A. MALLET: _Geometry/AOI modeling support_*
- *M-J. TANNOURY: _Parsing support_*
- *A. TRAD: _Semantic extraction support_*

= Risks & Mitigation plans

#table(
  columns: (auto, auto),
  inset: 10pt,
  align: horizon,
  table.header(
    align(center)[*Risks*], align(center)[*Mitigation Plans*],
  ),

  [SVG structures vary significantly across visualizations, which makes it
  difficult to apply a single extraction approach.], [Begin with a common AOI
  schema and ajust parsing rules iteratively.],
  [Important semantic information may be missing or inconsistently labeled in
  some SVG files.], [Use the position of the elements and their grouping in the
  SVG to better identify AOIs whose labels are missing or unclear.],
  [Bounding boxes or AOIs may be inaccurate for complex visual elements.],
  [Perform manual validation and consistency checks on sample visualizations.],
  [Integration challenges and issues may occur when combining parsing, geometry
  and normalization.], [Use shared code repository and perform weekly
  integration.],
  [Project timeline may be underestimated due to unforeseen complexity.],
  [Prioritize completing a core AOI extraction pipeline first, leaving optional
  adjustments for later.],
)
