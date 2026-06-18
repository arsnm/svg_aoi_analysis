#import "./tp-report-template/telecom-paris-report.typ": telecom-paris-report
#import "global.typ": *

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

= Introduction
== Hypotheses
== Motivations

= 
= Implementation Process
= Challenges & Findings
= Results
= Discussion
= AI Usage
