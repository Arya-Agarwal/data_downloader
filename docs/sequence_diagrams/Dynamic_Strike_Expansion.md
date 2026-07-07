```mermaid
sequenceDiagram

participant SpotTick
participant LiveSession
participant StrikeUniverse
participant SubscriptionManager
participant KiteTicker

SpotTick->>LiveSession: update()

LiveSession->>StrikeUniverse: update()

alt New High/Low

StrikeUniverse-->>SubscriptionManager: New Strikes

SubscriptionManager->>KiteTicker: subscribe()

SubscriptionManager->>KiteTicker: MODE_FULL

else No Change

StrikeUniverse-->>SubscriptionManager: Ignore

end
```