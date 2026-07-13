"""Aria Core Event Bus — event type constants (Phase 4)."""

from __future__ import annotations

EVENT_VERSION = "2.0-phase4"

# Initial event types (mission). Values are stable wire names.
MemoryCreated = "MemoryCreated"
MemoryUpdated = "MemoryUpdated"
MemoryDeleted = "MemoryDeleted"
KnowledgeAdded = "KnowledgeAdded"
KnowledgeUpdated = "KnowledgeUpdated"
LearningProposed = "LearningProposed"
LearningAccepted = "LearningAccepted"
LearningRejected = "LearningRejected"
LearningCommitted = "LearningCommitted"
LearningReplayed = "LearningReplayed"
LearningRolledBack = "LearningRolledBack"
ReferenceLookup = "ReferenceLookup"
ReferenceIndexed = "ReferenceIndexed"
ReasoningStarted = "ReasoningStarted"
ReasoningFinished = "ReasoningFinished"
PlanStarted = "PlanStarted"
PlanCompleted = "PlanCompleted"
InferenceStarted = "InferenceStarted"
InferenceFinished = "InferenceFinished"
ToolStarted = "ToolStarted"
ToolCompleted = "ToolCompleted"
ApplicationStarted = "ApplicationStarted"
ApplicationStopped = "ApplicationStopped"
RuntimeConnected = "RuntimeConnected"
RuntimeDisconnected = "RuntimeDisconnected"
RepairStarted = "RepairStarted"
RepairCompleted = "RepairCompleted"
BackupStarted = "BackupStarted"
BackupCompleted = "BackupCompleted"
RecoveryStarted = "RecoveryStarted"
RecoveryCompleted = "RecoveryCompleted"
StartupPhaseChanged = "StartupPhaseChanged"
ShutdownStarted = "ShutdownStarted"
ShutdownCompleted = "ShutdownCompleted"
CognitionStarted = "CognitionStarted"
CapabilitySelected = "CapabilitySelected"
CapabilitySkipped = "CapabilitySkipped"
PlanningRequested = "PlanningRequested"
ReasoningRequested = "ReasoningRequested"
ReferenceRequested = "ReferenceRequested"
MemoryRequested = "MemoryRequested"
KnowledgeRequested = "KnowledgeRequested"
LearningRequested = "LearningRequested"
CognitionCompleted = "CognitionCompleted"

ALL_EVENT_TYPES: tuple[str, ...] = (
    MemoryCreated,
    MemoryUpdated,
    MemoryDeleted,
    KnowledgeAdded,
    KnowledgeUpdated,
    LearningProposed,
    LearningAccepted,
    LearningRejected,
    LearningCommitted,
    LearningReplayed,
    LearningRolledBack,
    ReferenceLookup,
    ReferenceIndexed,
    ReasoningStarted,
    ReasoningFinished,
    PlanStarted,
    PlanCompleted,
    InferenceStarted,
    InferenceFinished,
    ToolStarted,
    ToolCompleted,
    ApplicationStarted,
    ApplicationStopped,
    RuntimeConnected,
    RuntimeDisconnected,
    RepairStarted,
    RepairCompleted,
    BackupStarted,
    BackupCompleted,
    RecoveryStarted,
    RecoveryCompleted,
    StartupPhaseChanged,
    ShutdownStarted,
    ShutdownCompleted,
    CognitionStarted,
    CapabilitySelected,
    CapabilitySkipped,
    PlanningRequested,
    ReasoningRequested,
    ReferenceRequested,
    MemoryRequested,
    KnowledgeRequested,
    LearningRequested,
    CognitionCompleted,
)
