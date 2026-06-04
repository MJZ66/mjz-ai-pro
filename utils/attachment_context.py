"""附件预解析与 system 上下文注入（供多轮追问使用）。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from utils.file_utils import (
    DEFAULT_MAX_FILE_CHARS,
    LoadedFile,
    prepare_file_content,
    truncate_notice,
)

ATTACHMENT_BLOCK_START = "\n\n---\n【当前已加载附件（用户可直接提问，无需重复上传）】\n"

SESSION_KEY = "parsed_attachment"


def loaded_file_to_attachment(loaded: LoadedFile) -> Dict[str, Any]:
    """将 LoadedFile 转为可存入 session_state 的结构。"""
    if loaded.is_image:
        return {
            "filename": loaded.filename,
            "extension": loaded.extension,
            "kind": "image",
            "text": loaded.text,
            "truncated": False,
            "char_count": 0,
            "image_base64": loaded.image_base64,
            "image_mime": loaded.image_mime,
        }

    body, truncated, original_len = prepare_file_content(loaded.text)
    return {
        "filename": loaded.filename,
        "extension": loaded.extension,
        "kind": "text",
        "text": body,
        "truncated": truncated,
        "char_count": original_len,
        "image_base64": "",
        "image_mime": "",
    }


def strip_attachment_from_system(system_content: str) -> str:
    """移除 system 中已注入的附件块，得到基础角色 Prompt。"""
    if ATTACHMENT_BLOCK_START in system_content:
        return system_content.split(ATTACHMENT_BLOCK_START, 1)[0]
    return system_content


def format_attachment_block(
    attachment: Dict[str, Any],
    *,
    max_chars: int = DEFAULT_MAX_FILE_CHARS,
) -> str:
    filename = attachment.get("filename", "未知文件")
    ext = attachment.get("extension", "")
    kind = attachment.get("kind", "text")

    if kind == "image":
        return (
            f"文件名：{filename}\n"
            f"类型：图片 {ext}\n"
            "说明：用户已上传图片。回答时请结合用户对图片的描述；"
            "若当前模型支持视觉，可参考对话中的图片消息。"
        )

    text = attachment.get("text") or ""
    truncated = attachment.get("truncated", False)
    char_count = attachment.get("char_count", len(text))
    trunc_line = (
        f"\n（原文约 {char_count} 字，{truncate_notice(max_chars)}）"
        if truncated
        else ""
    )
    return (
        f"文件名：{filename}\n"
        f"文件类型：{ext}\n"
        f"正文如下：\n{text}{trunc_line}\n\n"
        "要求：用户后续提问均默认针对上述附件内容作答，"
        "勿声称「未提供文件」或「缺少信息」，除非附件正文确实无法回答。"
    )


def apply_attachment_to_system(
    base_system: str,
    attachment: Optional[Dict[str, Any]],
) -> str:
    """在基础 system Prompt 后追加附件正文，供多轮对话引用。"""
    if not attachment:
        # 已合并过附件的 system（如 ChatAgent.system_prompt）须原样保留，
        # 否则 ensure_system 会在每次回复时把附件块剥掉。
        return base_system
    base = strip_attachment_from_system(base_system)
    return base + ATTACHMENT_BLOCK_START + format_attachment_block(attachment)


def build_user_message_from_attachment(
    attachment: Dict[str, Any],
    user_note: str = "",
) -> dict:
    """基于已解析附件构建一轮分析用的 user 消息。"""
    note = (user_note or "").strip()
    prefix = f"{note}\n\n" if note else ""
    filename = attachment.get("filename", "附件")
    ext = attachment.get("extension", "")

    if attachment.get("kind") == "image" and attachment.get("image_base64"):
        text_part = (
            f"{prefix}请分析已加载的图片附件（{filename}）。"
            "描述画面关键信息并回答用户问题。"
        )
        mime = attachment.get("image_mime") or "image/png"
        b64 = attachment["image_base64"]
        return {
            "role": "user",
            "content": [
                {"type": "text", "text": text_part},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                },
            ],
        }

    body = attachment.get("text") or ""
    trunc = attachment.get("truncated", False)
    trunc_hint = "\n\n（正文此前已截断，仅保留前段参与对话。）" if trunc else ""
    content = (
        f"{prefix}请分析以下已加载文件：\n"
        f"文件名：{filename}\n"
        f"文件类型：{ext}\n\n"
        f"文件内容：\n{body}{trunc_hint}"
    )
    return {"role": "user", "content": content}


def attachment_status_line(attachment: Optional[Dict[str, Any]]) -> str:
    if not attachment:
        return ""
    name = attachment.get("filename", "文件")
    kind = attachment.get("kind", "text")
    if kind == "image":
        return f"已加载图片「{name}」，可直接在下方提问。"
    chars = attachment.get("char_count") or len(attachment.get("text") or "")
    trunc = "（正文已截断）" if attachment.get("truncated") else ""
    return f"已解析「{name}」约 {chars} 字{trunc}，可直接在下方提问。"
