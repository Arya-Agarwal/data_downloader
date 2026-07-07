```mermaid
sequenceDiagram

participant LiveScheduler
participant Scheduler
participant LiveWebSocket

alt FORCE_MARKET_CLOSE=True

LiveScheduler->>Scheduler: Historical Download

Scheduler->>Scheduler: Gap Recovery

Scheduler->>Scheduler: EOD Refresh

Scheduler-->>LiveScheduler: Exit

else Before 8AM

LiveScheduler->>Scheduler: Historical Download

Scheduler-->>LiveScheduler: Done

LiveScheduler->>LiveScheduler: Wait Market Open

LiveScheduler->>LiveWebSocket: Connect

else Between 9:00-9:15

LiveScheduler->>LiveScheduler: Wait 30 Seconds

LiveScheduler->>LiveWebSocket: Connect

else Market Open

LiveScheduler->>LiveWebSocket: Connect Immediately

else After Market Close

LiveScheduler->>Scheduler: Historical Download

Scheduler->>Scheduler: Gap Recovery

Scheduler->>Scheduler: EOD Refresh

end
```