```mermaid
sequenceDiagram

participant Scheduler
participant GapRecovery
participant Validator
participant Kite
participant Tracker

Scheduler->>GapRecovery: recover_all_gaps()

GapRecovery->>Validator: validate()

Validator-->>GapRecovery: Missing Timestamps

loop Missing Range

GapRecovery->>Kite: historical_data()

Kite-->>GapRecovery: Missing Candles

end

GapRecovery->>Tracker: update()

GapRecovery-->>Scheduler: Complete
```