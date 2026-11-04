"""Register the built-in assistant skills."""
from skills.agent_tasks import AgentTasksSkill
from skills.app_identity import AppIdentitySkill
from skills.computer_settings import ComputerSettingsSkill
from skills.file_controller import FileControlSkill
from skills.file_processor import FileProcessingSkill
from skills.proactive_checks import ProactiveChecksSkill
from skills.reminders import ReminderSkill
from skills.screen_camera import ScreenCaptureSkill
from skills.system_monitor import SystemMonitorSkill
from skills.video_player import VideoPlayerSkill
from skills.web_search import WebSearchSkill
from skills.loader import SkillLoader


def build_skill_loader() -> SkillLoader:
    loader = SkillLoader()
    for skill in (
        AgentTasksSkill(),
        AppIdentitySkill(),
        ComputerSettingsSkill(),
        FileControlSkill(),
        FileProcessingSkill(),
        ProactiveChecksSkill(),
        ReminderSkill(),
        ScreenCaptureSkill(),
        SystemMonitorSkill(),
        VideoPlayerSkill(),
        WebSearchSkill(),
    ):
        loader.register(skill)
    return loader
