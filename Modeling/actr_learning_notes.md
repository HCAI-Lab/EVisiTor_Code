# ACT-R Learning Notes

These notes summarize the local `actr7.x` materials with an emphasis on how ACT-R models are structured in practice.

## Core Idea

An ACT-R model is usually built from four main parts:

1. `chunk-type` declarations define the data structures the model can use.
2. `add-dm` inserts declarative memory chunks.
3. `goal-focus` or `+goal>` sets the model's current task state.
4. `p` productions define condition-action rules that move the model through cognition.

Most models in `actr7.x/tutorial` follow that pattern.

## Common Model Skeleton

```lisp
(clear-all)

(define-model model-name

  (sgp ...)

  (chunk-type goal-type state ...)
  (chunk-type fact-type ...)

  (add-dm
    (... isa fact-type ...))

  (goal-focus (isa goal-type state start))

  (p production-name
     =goal>
       isa goal-type
       state start
   ==>
     =goal>
       state next-state
     +retrieval>
       isa fact-type
       ...)
)
```

## Chunks And Declarative Memory

Chunks are symbolic records with a type and slot values.

Example from `tutorial/unit1/addition.lisp`:

```lisp
(chunk-type number number next)
(chunk-type add arg1 arg2 sum count)
```

This says:

- `number` chunks store a number label and its successor.
- `add` chunks store the state of an addition task.

Declarative memory is usually initialized with `add-dm`:

```lisp
(add-dm
 (zero isa number number zero next one)
 (one isa number number one next two))
```

Important ideas:

- `isa` gives the chunk type.
- slot-value pairs define chunk content.
- chunks can represent facts, task states, operators, semantic knowledge, or temporary domain concepts.

Examples in the tutorial:

- `unit1/semantic.lisp`: semantic facts like category membership.
- `unit5/fan-model.lisp`: sentence facts and word meanings.
- `unit7/paired-learning-model.lisp`: operator chunks that control task flow.

## Production Rules

Productions are written with `p`.

They have:

- a left-hand side before `==>`: pattern matching and buffer tests
- a right-hand side after `==>`: actions that change buffers or request module operations

Example shape:

```lisp
(p production-name
   =goal>
     isa some-type
     slot value
   ?retrieval>
     state free
 ==>
   =goal>
     slot new-value
   +retrieval>
     isa other-type
     ...)
```

Useful operators seen throughout the local models:

- `=buffer>`: match or modify an existing chunk in a buffer.
- `+buffer>`: request creation, retrieval, or action in a buffer/module.
- `?buffer>`: test buffer state such as `free`, `empty`, or `failure`.
- `- slot value`: enforce inequality inside a chunk/buffer pattern.
- `*imaginal>`: modify an imaginal chunk in place in some tutorial models.
- `!output!`: print a result.

## Buffers You See Often

These are the buffers that show up repeatedly in the tutorial:

- `goal`: current task state or control state
- `retrieval`: result of a declarative memory retrieval
- `imaginal`: working representation being constructed or updated
- `visual-location`: where something is on screen
- `visual`: attended visual object
- `manual`: motor action requests like key presses

Reading ACT-R models gets much easier if you think of productions as moving information across these buffers.

## How Modeling Usually Works

A common pattern across the examples is:

1. Put the current task state in the goal buffer.
2. Request a retrieval or perceptual action.
3. Wait for the requested result to appear in another buffer.
4. Update the goal or imaginal buffer.
5. Repeat until the task terminates.

In `unit1/addition.lisp`, the model:

1. starts with an `add` goal chunk
2. retrieves a number chunk
3. increments `count`
4. increments `sum`
5. stops when `count = arg2`

In `unit1/semantic.lisp`, the model:

1. starts with an `is-member` goal
2. retrieves a category fact
3. either verifies directly, chains upward through categories, or fails

## Declarative Retrieval

Retrieval requests are often written like this:

```lisp
+retrieval>
  isa property
  object =obj
  attribute category
```

That means: retrieve a chunk from declarative memory matching those constraints.

The retrieved chunk later appears as:

```lisp
=retrieval>
  isa property
  ...
```

Retrieval can also fail, which productions detect with:

```lisp
?retrieval>
  buffer failure
```

## Parameters That Matter

Models often set parameters with `sgp`. Common ones seen in the local files:

- `:esc`: enables stochastic retrieval/selection behavior
- `:lf`: latency factor
- `:bll`: base-level learning
- `:ans`: activation noise
- `:mas`: maximum associative strength
- `:mp`: partial matching
- `:pct`: production compilation
- `:ul`: utility learning
- `:epl`: expected gain / utility-related learning controls used in tutorial models

You do not need all of these to build a first model. A simple model can start with only a few.

## Good Beginner Mental Model

When writing an ACT-R model, ask:

- What chunks represent the knowledge?
- What chunk in the goal buffer represents the current task state?
- What must be retrieved, perceived, or acted on next?
- What buffer state tells me that step succeeded or failed?
- What production should fire next?

If those are clear, the model usually becomes manageable.

## Practical Starting Files In This Repo

Best local starting points for learning:

- `actr7.x/tutorial/unit1/addition.lisp`
- `actr7.x/tutorial/unit1/semantic.lisp`
- `actr7.x/tutorial/unit2/demo2-model.lisp`
- `actr7.x/tutorial/unit5/declarative-issues.lisp`
- `actr7.x/tutorial/unit5/fan-model.lisp`
- `actr7.x/tutorial/unit7/paired-learning-model.lisp`

Operational docs:

- `actr7.x/docs/QuickStart.txt`
- `actr7.x/readme.txt`
- `actr7.x/tutorial/readme.txt`

## What I Learned To Reuse Later

- ACT-R models in this codebase are highly state-machine-like.
- Declarative chunks are the knowledge store; productions are the control logic.
- The goal buffer usually carries the current phase of processing.
- Retrieval, visual, imaginal, and manual buffers are the main bridges between memory, perception, and action.
- Most debugging will involve checking why a production did not match or why a retrieval failed.
