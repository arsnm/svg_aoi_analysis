#import "@preview/timeliney:0.4.0"

#let schedule = timeliney.timeline(
  show-grid: true,
  {
    import timeliney: *

    // 1 unit = 1 week. Total grid is 8 units.
    headerline(
      group(([*May 2026*], 4)),
      group(([*June 2026*], 4))
    )

    headerline(
      group(..range(8).map(n => [*W#str(n + 1)*]))
    )

    taskgroup({
      task("SVG dataset exploration", (0, 2), style: (stroke: 5pt + gray))
    })

    taskgroup(title: [*AOI extraction*], {
      task("Parse SVG files", (0, 3), style: (stroke: 5pt + gray))
      task("Identify meaningful elements", (1, 4), style: (stroke: 5pt + gray))
      task("Retrieve semantic information", (2, 5), style: (stroke: 5pt + gray))
      task("Validating the process", (4, 5), style: (stroke: 5pt + gray))
    })

    taskgroup(title: [*Building the Pipeline*], {
      task("Compute bounding boxes", (3, 6), style: (stroke: 5pt + gray))
      task("Construct AOI table", (4, 6), style: (stroke: 5pt + gray))
      task("Build hierarchical representation", (4, 7), style: (stroke: 5pt + gray))
      task("Tests, validation of AOIs", (5, 8), style: (stroke: 5pt + gray))
    })

    taskgroup({
      task("Weekly integration and testing", (3, 8), style: (stroke: 5pt + gray))
      task("Documentation & final report", (0, 8), style: (stroke: 5pt + gray))
    })

    milestone(at: 0, style: (stroke: (dash: "dashed")), align(center)[*Send Project Plan*\ Apr 30])
    milestone(at: 3.9, style: (stroke: (dash: "dashed")), align(center)[*Midterm Evaluation*\ May 29])

    milestone(
      at: 8,
      style: (stroke: (thickness: 2pt, paint: red)),
      align(right)[#text(fill: red)[*Final Deadline*\ Jun 26]]
    )
  }
)
