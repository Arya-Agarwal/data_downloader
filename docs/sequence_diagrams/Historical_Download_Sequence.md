```mermaid
sequenceDiagram

participant Scheduler
participant SpotDownloader
participant FutureDownloader
participant OptionDownloader
participant Validator
participant Tracker

Scheduler->>SpotDownloader: download_spot()

SpotDownloader->>Validator: validate()

Validator->>Tracker: update()

Scheduler->>FutureDownloader: download_futures()

FutureDownloader->>Validator: validate()

Validator->>Tracker: update()

Scheduler->>OptionDownloader: download_options()

OptionDownloader->>Validator: validate()

Validator->>Tracker: update()
```