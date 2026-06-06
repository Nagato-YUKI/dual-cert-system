"""AI review service module."""

import json
import os
from typing import Any

import requests


def ai_review_registration(registration: Any) -> dict:
    """Review a registration using LLM API.

    Args:
        registration: Registration ORM object with related student/exam loaded.

    Returns:
        Parsed JSON dict with keys: result, score, reason, issues.
    """
    student = registration.student
    exam = registration.exam
    cert_type = exam.cert_type if exam else None
    class_ = student.class_ if student else None
    rule = cert_type.registration_rule if cert_type else None

    materials = registration.materials_path or "未提交"

    prompt = f"""你是一个学生证书考试报名审核助手。请审核以下报名信息：

- 学生：{student.name if student else "未知"}，学号：{student.student_no if student else "未知"}
- 班级：{class_.name if class_ else "未知"}，专业：{class_.major if class_ else "未知"}
- 报名考试：{exam.exam_name if exam else "未知"}（{cert_type.name if cert_type else "未知"}）
- 报名条件：{rule.rule_content if rule else "无特殊要求"}
- 提交材料：{materials}

请根据以下检查项进行审核：
1. 学生基本信息是否完整（学号、姓名、班级）
2. 是否满足报名条件（年级、专业要求）
3. 提交材料是否齐全
4. 历史是否有重复报名

请返回严格的JSON格式（不要包含markdown代码块标记）：
{{
    "result": "approved|rejected|need_more_info",
    "score": 0-100,
    "reason": "审核理由",
    "issues": ["问题列表"]
}}
"""

    response_text = _call_llm_api(prompt)
    return _parse_response(response_text)


def _call_llm_api(prompt: str) -> str:
    """Call LLM API with the given prompt."""
    api_key = os.environ.get("AI_API_KEY")
    api_base = os.environ.get("AI_API_BASE", "https://api.openai.com/v1")
    model = os.environ.get("AI_MODEL", "gpt-3.5-turbo")

    if not api_key:
        # Fallback: return a mock response for development
        return json.dumps(
            {
                "result": "approved",
                "score": 85,
                "reason": "AI API key not configured, returning default approval for development.",
                "issues": [],
            },
            ensure_ascii=False,
        )

    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        # Return a safe fallback so the flow doesn't break
        return json.dumps(
            {
                "result": "need_more_info",
                "score": 50,
                "reason": f"AI service error: {e}",
                "issues": ["AI审核服务暂时不可用，请转人工审核"],
            },
            ensure_ascii=False,
        )


def _parse_response(text: str) -> dict:
    """Parse LLM response text into a dict."""
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # Remove first line (```json or ```)
        if lines:
            lines = lines[1:]
        # Remove last line (```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "result": "need_more_info",
            "score": 50,
            "reason": "AI返回格式无法解析，请转人工审核",
            "issues": ["AI返回格式异常"],
        }

    # Normalize keys
    return {
        "result": result.get("result", "need_more_info"),
        "score": float(result.get("score", 50)),
        "reason": result.get("reason", ""),
        "issues": result.get("issues", []),
    }
