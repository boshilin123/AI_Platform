from __future__ import annotations

from app.infrastructure.llm.models import LlmMessage

PROMPT_VERSION = "v1.1"


def resume_parse_messages(resume_text: str) -> list[LlmMessage]:
    return [
        LlmMessage(
            role="system",
            content=(
                "你是企业招聘助手。只从简历中提取明确出现的信息，不猜测缺失内容。"
                "输出一个 JSON 对象，字段为 name、school、major、graduationTime、skills、projects。"
                "projects 中每项包含 name、summary、technologies、risks。缺失标量用 null，列表用空数组。"
                "只要简历中存在可读的候选人信息，就不得把所有字段都返回为空。"
            ),
        ),
        LlmMessage(role="user", content=f"请结构化解析以下简历：\n\n{resume_text}"),
    ]


def screening_messages(resume_text: str, job_description: str) -> list[LlmMessage]:
    return [
        LlmMessage(
            role="system",
            content=(
                "你是企业招聘初筛助手。根据岗位要求和简历进行辅助分析，不得替代人工录用决策。"
                "输出 JSON：matchScore(0-100)、recommendation、confidence(0-1)、strengths、risks、"
                "interviewFocus、finalComment。结论必须引用可验证的简历事实，未知信息列为待确认风险。"
            ),
        ),
        LlmMessage(
            role="user",
            content=f"岗位要求：\n{job_description}\n\n候选人简历：\n{resume_text}",
        ),
    ]


def interview_messages(
    resume_text: str, job_description: str, screening_risks: list[str]
) -> list[LlmMessage]:
    risk_text = "\n".join(f"- {item}" for item in screening_risks) or "- 暂无额外风险点"
    return [
        LlmMessage(
            role="system",
            content=(
                "你是企业技术面试设计助手。生成针对候选人的项目验真、技术能力、工程能力和风险追问题。"
                "问题不得涉及法律禁止的歧视性信息。输出 JSON：questions 数组；每项包含 type、question、purpose。"
            ),
        ),
        LlmMessage(
            role="user",
            content=(
                f"岗位要求：\n{job_description}\n\n候选人简历：\n{resume_text}"
                f"\n\n初筛风险：\n{risk_text}"
            ),
        ),
    ]
