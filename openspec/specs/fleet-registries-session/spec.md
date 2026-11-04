# Delta for fleet-registries-session

New capability: session-isolated fleet registries with atomic, validated,
backward-compatible persistence. All requirements are ADDED.

## ADDED Requirements

### Requirement: Session isolation

Each session's registry (`twins`, `hangar`, `altas`) MUST resolve to a path
derived only from its own validated `session_id`. Sessions MUST NOT share a
global registry. A `session_id` MUST match `^[A-Za-z0-9_-]{1,64}$` and MUST
NOT contain `/`, `\` or `..`; an invalid one MUST be rejected with a visible
error and no file created.

#### Scenario: Two sessions never clobber each other

- GIVEN sessions `s1` and `s2`
- WHEN both interleave saves, each adding a different hangar engine
- THEN each file holds only its own records

#### Scenario: Invalid session_id is rejected

- GIVEN `session_id` `../escape` or empty
- WHEN the registry path is resolved
- THEN an error is returned and no file is created outside the session dir

#### Scenario: Reload restores only own fleet

- GIVEN `s1` has 3 hangar engines, `s2` has 1
- WHEN `s1` reloads
- THEN `s1` sees its 3 engines and `s2`'s file is byte-unchanged

### Requirement: Atomic writes

Saves MUST write to `{path}.tmp`, fsync, then atomically rename to `{path}`.
The destination MUST NOT be truncated before rename, so an interrupted save
leaves the last valid registry intact. Saves within one session MUST be
serialized (lock).

#### Scenario: Interrupted save keeps last valid file

- GIVEN a session file saved once with 2 hangar engines
- WHEN a second save is interrupted before rename
- THEN `{path}` still parses as valid JSON with those 2 engines

#### Scenario: Successful save replaces atomically

- GIVEN a save that completes
- WHEN the rename finishes
- THEN `{path}` parses with exactly the new records
- AND no `{path}.tmp` remains

### Requirement: Schema validation on load and save

Every load and save MUST parse with `json.load` and validate the schema:
a mapping with `twins`, `hangar` and `altas`, each a list of records with
their expected fields. A mismatch MUST raise a visible error; a failed
validation on save MUST NOT modify the existing file.

#### Scenario: Corrupt JSON falls back with visible error

- GIVEN a session file with invalid JSON and a pre-migration backup
- WHEN the registry loads
- THEN records are recovered from the backup
- AND a visible error/warning names the corruption and the recovery

#### Scenario: Corrupt JSON without backup starts empty, error visible

- GIVEN a session file containing invalid JSON and no backup
- WHEN the registry loads
- THEN all three collections are empty and a visible error reports it

#### Scenario: Schema mismatch is rejected

- GIVEN a file parsing as JSON but missing `altas`
- WHEN it loads or is saved
- THEN validation fails visibly
- AND the pre-existing file is unchanged

### Requirement: Backward-compatible migration

On first run with no session file, the legacy global
`app/registros_flota.json` MUST be **copied** (never moved) into the session
file. A pre-migration backup MUST be written before any migration. Record
counts per collection MUST match before/after; on mismatch the migration MUST
abort with no partial data, restoring from the backup (zero record loss).

#### Scenario: Legacy fleet migrates with zero loss

- GIVEN a legacy file with 5 `twins`, 2 `hangar`, 3 `altas`
- WHEN a first session runs against it
- THEN a backup exists and the session file holds 5/2/3 records
- AND the legacy file is byte-unchanged

#### Scenario: Count mismatch aborts migration

- GIVEN a corrupted copy attempt yielding different counts
- WHEN the count check runs
- THEN migration aborts, the session file holds no partial data
- AND the original legacy content is restorable from the backup

#### Scenario: New session without legacy starts empty

- GIVEN no session file and no legacy global file
- WHEN a session starts
- THEN `twins`, `hangar` and `altas` are all empty
- AND no error is shown
