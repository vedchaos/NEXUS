# NEXUS bridge_core — Core modules
from .smart_brain import get_brain
from .memory_3tier import get_memory
from .agents import get_orchestrator
from .task_classifier import classify_task, get_task_chain
from .scheduler import parse_hinglish_time, ChaosScheduler
from .recon import recon_passive, recon_active
from .voice import get_voice
from .vision import get_vision
from .ml_pipeline import get_ml_pipeline
from .automation import get_engine
