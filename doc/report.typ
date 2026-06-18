#import "./tp-report-template/telecom-paris-report.typ": telecom-paris-report
#import "global.typ": *
#import "utils.typ": *

#let abstract = [
  TODO
]

#show: telecom-paris-report.with(
  title: title,
  short-title: "AOI extraction from SVG visualizations",
  authors: authors,
  show-mail: true,
  supervisors: supervisor,
  date: "June 2026",
  abstract: abstract,
  keywords: keywords,
  sidebar-text: "DSAI Project Report"
)

#set heading(numbering: "I.a.")
#set par(justify: true)

= Introduction, Hypotheses & Motivations<intro>

Given a predefined set of *S*\calable *V*\ector *G*\raphics visualizations
(maps, treemaps, scatterplots, #etc.), this project aims to build a set of tools
capable of extracting relevant information, mainly position and semantic, of the
*A*\reas *O*\f *I*\nterest present in the SVG. This project is initially part of
a broader initiative to extract eye-tracking data from these same SVGs, the
ultimate goal being to correlate gaze patterns with AOIs in order to better
interpret the whole process one would use to understand various visualizations.
With the aim of generalizing the approach, this project seeks to extract
semantic information from SVG visualizations beyond the original --- and already
very verbose --- dataset.

As discussed in the introduction, the original dataset was composed of very
verbose SVGs. By that, we mean that these SVGs were greatly annotated, with many
attributes, such as `id`s and `class`es, already having relevant semantic
information. That is the first hypothesis made, parsing these attributes
properly would already give a good idea of the semantics of the elements making
up the visualizations. Combined with the tree structure of the SVG format itself
#cite(<w3c-svg>), we initially thought that the original dataset could
practically be fully interpreted this way. After discussing with our supervisor,
we understood that the SVGs of the dataset had already been processed manually a
lot for the sake of research, our _naive_ approach was thus not satisfactory,
and needed a more general strategy. We then made the hypothesis that the
semantics of the AOIs could come from a _broader_ context, which will be
discussed in #ref(<impl>).

Since our goal is also to extract positional information about the AOIs, we also
needed a strategy to compute _bounding boxes_, in order to have a mapping of the
semantic information in the space of the SVG. Even though the geometry is not
trivial, the tree structure of the SVG combined with the vector description of
the shapes made the computation of precise spatial boundaries a systematic,
albeit complex, geometric problem. By traversing the document tree and
translating the raw vector paths and affine transformations into exploitable
geometric objects, we hypothesized that we could accurately compute these
bounding boxes, regardless of the shape's complexity. This spatial mapping is a
critical prerequisite: without a reliable system to map an element's extracted
semantics to its exact 2D coordinates, correlating the data with eye-tracking
logs would be impossible.

In the remainder of this report, we will detail our implementation pipeline,
from the initial parsing of the SVG Document Object Model (DOM) to the geometric
processing and generalized semantic extraction. We will then discuss the
technical challenges encountered---particularly regarding non-standard SVG
structures and complex composite shapes---before evaluating our findings and our
alignment with the project's initial objectives.

= Implementation Process<impl>

In this section, we discuss both the technical and managerial aspect of our
project's pipeline implementation.

== Development Roles & Assigments

== Techinal Strategies

= Challenges & Findings

= Results

= Discussion

= AI Usage

#bibliography("refs.yaml", title: "References")
