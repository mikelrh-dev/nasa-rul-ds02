# Delta: ds02-live-evaluation

## ADDED Requirements

### Requirement: Every scored engine SHALL have an identity

The live evaluation SHALL attach an engine id, the data source and a SHA-256
fingerprint of the scored table to the result, the work order and the twin.

#### Scenario: scoring with an id

- GIVEN the user types `ESN-DEMO-01` and scores a table
- WHEN the result is built
- THEN the contract carries `motor = ESN-DEMO-01`
- AND the fingerprint is 64 hexadecimal characters

#### Scenario: the same table twice

- GIVEN the same table is scored twice
- WHEN the fingerprints are compared
- THEN they are equal

### Requirement: Validation SHALL run before the model loads

A model-free pre-flight SHALL report whether the table is scoreable, how many
windows it yields and which channels fall outside the observed envelope.
Scoring SHALL be refused, and the model SHALL NOT be loaded, while the table is
not scoreable.

#### Scenario: a table with a missing channel

- GIVEN a CSV without `T24`
- WHEN the pre-flight runs
- THEN it returns `ok = false` naming the missing column
- AND the evaluation is refused before `score_table` is called
- AND the reason is shown to the user without a TensorFlow load

### Requirement: The pre-flight SHALL bound the size of a table

The pre-flight and the scorer SHALL reject a table larger than 5 000 rows before
any window is built, naming the row count and the limit. The bound exists because
each extra row is one more window (`step = 1`), so a full engine history turns an
interactive check into minutes of scoring and a tensor that does not fit in
memory.

#### Scenario: a full engine history

- GIVEN a CSV with 300 000 rows
- WHEN the pre-flight runs
- THEN it returns `ok = false`, `ventanas = 0` and the limit in the message
- AND `score_table` raises the same message without loading the model

### Requirement: A scored engine SHALL be storable as a twin

The user SHALL be able to register a scored engine as a twin. The twin SHALL
store the engine id, the fingerprint, the band source, the correction applied,
the thresholds in force, and the series of scored windows.

#### Scenario: registering a twin

- GIVEN a scored result for `ESN-DEMO-01`
- WHEN the user registers it
- THEN the registry contains the twin under that id
- AND the stored series has one record per scored window

#### Scenario: duplicate id

- GIVEN a twin `ESN-DEMO-01` already registered
- WHEN another twin with the same id is registered without asking to replace it
- THEN the registry rejects it with a message naming the id
- AND the existing twin is unchanged

#### Scenario: scoring the same engine again

- GIVEN a twin `ESN-DEMO-01` with a reported real RUL
- WHEN the user scores another window of that engine and asks to replace it
- THEN the series, the fingerprint and the contract are replaced
- AND the reported real RUL is kept, because it is a fact about the engine
- AND the previous twin object is not mutated

### Requirement: A twin SHALL be documented without re-scoring

A registered twin SHALL produce the same work-order document as a live unit,
built from the stored series (the worst window of the latest cycle), the stored
fingerprint and the stored band, without calling the model and without claiming
ground truth.

#### Scenario: asking for the paper of one engine

- GIVEN a twin `ESN-DEMO-01` whose last cycle is 41 with `L_inf = 8.0`
- WHEN the user downloads its order as JSON and CSV
- THEN the entry names cycle 41 and `limite_inferior = 8.0`
- AND the document carries the stored artifact hash and `sin_ground_truth = true`
- AND the CSV leaves `rul_real` empty instead of failing

### Requirement: The real RUL SHALL close the loop when reported

A twin SHALL accept a reported real RUL and cycle, and SHALL expose the error
and whether the stored band covered it.

#### Scenario: truth inside the band

- GIVEN a twin whose band at cycle 40 is `[12.0, 30.0]`
- WHEN the user reports a real RUL of 21 at cycle 40
- THEN the twin reports `cubierta = true` and an error of `pred - 21`
