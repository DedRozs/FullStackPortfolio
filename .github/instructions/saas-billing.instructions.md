---
applyTo: "**/domain/**/*.{py,ts,cs,java,kt}, **/application/**/*.{py,ts,cs,java,kt}"
---
# SaaS Subscription Billing Rules

Subscription lifecycle changes (SubscriptionCreated, SubscriptionUpgraded,
SubscriptionDowngraded, SubscriptionCancelled, SubscriptionRenewed, TrialExpired) must
be modeled as domain events. Each event must carry the full subscription state at the
time of the change. Partial state in domain events prevents downstream consumers from
reconstructing the current subscription state without additional queries.

Payment provider SDK types (e.g., Stripe, Paddle, Chargebee objects) must never appear
in use-case input/output ports, domain entities, or domain services. An anti-corruption
layer adapter must translate between external billing provider models and internal domain
models. Allowing SDK types to cross the adapter boundary couples the domain and
application layers to a specific billing vendor and makes switching providers a
rewrite rather than a configuration change.

The billing domain must publish domain events when subscription state changes occur.
Downstream features (feature flag enforcement, usage limit checks) must react to these
events rather than querying billing state directly. Tight coupling between downstream
features and the billing aggregate creates a distributed monolith that defeats the
purpose of event-driven architecture.

Billing retry logic (failed payment retries, dunning workflows) must be implemented in
the infrastructure layer as event-driven processes reacting to domain events. Retry
schedules must not be hardcoded in domain entities. Embedding retry timing in domain
entities introduces temporal coupling and infrastructure concerns into the domain layer.

Usage-based billing metering must be recorded as domain events (`UsageRecorded`) before
being forwarded to the billing provider. The domain event is the source of truth; the
billing provider is a downstream sink. This ordering guarantees that usage data is not
lost in the event of a billing provider outage.

PCI DSS scope must be minimized by ensuring raw card data never touches the application
servers. All payment collection must use provider-hosted fields or tokenization SDKs.
Any code path that handles raw card numbers, CVVs, or full PANs on application servers
is a PCI DSS scope expansion and is prohibited.
