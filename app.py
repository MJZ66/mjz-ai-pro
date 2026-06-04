"""
MJZ AI Pro — Streamlit 主入口
多轮对话 · RAG 知识库 · Agent 工具
"""
import streamlit as st

from agents.base_agent import BaseAgent
from agents.chat_agent import ChatAgent
from agents.prompts import AGENT_NAME_ALIASES, SYSTEM_PROMPTS, normalize_agent_name
from ui.upload_zone import (
    RAG_UPLOAD_TYPES,
    is_new_upload,
    render_drag_drop_uploader,
    upload_fingerprint,
)
from utils.attachment_context import (
    SESSION_KEY,
    attachment_status_line,
    apply_attachment_to_system,
    build_user_message_from_attachment,
    loaded_file_to_attachment,
)
from utils.file_utils import (
    UPLOAD_TYPES,
    build_file_user_message,
    format_message_display,
    load_uploaded_file,
)
from common import build_llm_client
from core.config import (
    ConfigError,
    api_key_missing_message,
    format_key_loaded_hint,
    get_vendor_models,
    load_settings,
    normalize_sidebar_override,
    select_model_index,
    VENDOR_CHATTONGYI,
    VENDOR_DEEPSEEK,
)
from rag.rag_agent import RAGAgent
from rag.vector_store import VectorStore
from ui.panels import streamlit_panel
from ui.theme import (
    AGENT_ICONS,
    inject_theme,
    render_hero,
    render_mode_strip,
    render_sidebar_brand,
    sidebar_section,
)
from utils.math_intent import try_quick_calculate
from utils.stream_ui import stream_chat_into_message
from utils.logger import setup_logging, user_friendly_error
from utils.session_utils import (
    build_initial_messages,
    reset_system,
    should_reset_messages_on_agent_change,
)

setup_logging()

MODES = ["多轮对话", "RAG 知识库", "Agent 工具"]

st.set_page_config(
    page_title="MJZ AI Pro",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()


def render_sidebar():
    with st.sidebar:
        render_sidebar_brand()

        sidebar_section("工作模式")
        mode = st.radio(
            "工作模式",
            MODES,
            label_visibility="collapsed",
        )

        sidebar_section("模型")
        vendor = st.radio(
            "模型提供商",
            [VENDOR_CHATTONGYI, VENDOR_DEEPSEEK],
            format_func=lambda v: "通义千问" if v == VENDOR_CHATTONGYI else "DeepSeek",
        )
        model_options = get_vendor_models(vendor)
        model_name = st.selectbox(
            "对话模型",
            model_options,
            index=select_model_index(vendor, model_options),
        )
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

        if mode == "多轮对话":
            sidebar_section("智能体")
            agent_labels = [
                f"{AGENT_ICONS.get(k, '·')} {k}" for k in SYSTEM_PROMPTS
            ]
            agent_keys = list(SYSTEM_PROMPTS.keys())
            picked = st.selectbox(
                "角色",
                agent_labels,
                label_visibility="collapsed",
            )
            agent_type = agent_keys[agent_labels.index(picked)]
            keep_history = st.checkbox(
                "切换角色时保留历史",
                value=False,
                help="默认关闭，避免不同角色上下文混杂",
            )
        else:
            agent_type = "通用聊天助手"
            keep_history = False

        sidebar_section("连接")
        api_key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="留空则读取 .env",
            help="通义：DASHSCOPE_API_KEY · DeepSeek：DEEPSEEK_API_KEY · RAG 向量另需通义 Key",
        )
        try:
            _preview = load_settings(
                api_key_override=api_key_input,
                vendor=vendor,
                model_override=model_name,
            )
            if not normalize_sidebar_override(api_key_input):
                chat_hint = format_key_loaded_hint(_preview.openai_api_key)
                if chat_hint:
                    st.caption(chat_hint)
                if mode == "RAG 知识库":
                    embed_hint = format_key_loaded_hint(
                        _preview.embedding_api_key, label="向量"
                    )
                    if embed_hint:
                        st.caption(embed_hint)
            elif not _preview.openai_api_key:
                st.caption("侧边栏已填写但 Key 为空，请检查输入。")
        except ConfigError:
            st.caption(api_key_missing_message(vendor))

        if mode == "多轮对话":
            st.divider()
            if st.button("清空当前会话", use_container_width=True):
                st.session_state["_clear_chat_pending"] = True

    return {
        "mode": mode,
        "vendor": vendor,
        "model_name": model_name,
        "temperature": temperature,
        "agent_type": agent_type,
        "keep_history": keep_history,
        "api_key_input": api_key_input,
    }


def migrate_agent_names():
    old_agent = st.session_state.get("current_agent")
    if old_agent and old_agent in AGENT_NAME_ALIASES:
        st.session_state.current_agent = normalize_agent_name(old_agent)


def get_parsed_attachment():
    return st.session_state.get(SESSION_KEY)


def effective_system_prompt(agent_type: str) -> str:
    base = SYSTEM_PROMPTS[normalize_agent_name(agent_type)]
    return apply_attachment_to_system(base, get_parsed_attachment())


def sync_messages_system_prompt(agent_type: str):
    """将 session 中的附件上下文同步到 messages[0]。"""
    if "messages" not in st.session_state or not st.session_state.messages:
        return
    content = effective_system_prompt(agent_type)
    if st.session_state.messages[0].get("role") == "system":
        st.session_state.messages[0]["content"] = content
    else:
        st.session_state.messages.insert(
            0, {"role": "system", "content": content}
        )


def clear_parsed_attachment():
    st.session_state.pop(SESSION_KEY, None)
    for key in list(st.session_state.keys()):
        if key.startswith("_upload_fp_"):
            del st.session_state[key]


def parse_and_store_attachment(uploaded) -> dict:
    loaded = load_uploaded_file(uploaded)
    attachment = loaded_file_to_attachment(loaded)
    st.session_state[SESSION_KEY] = attachment
    return attachment


def init_chat_session(agent_type: str, keep_history: bool):
    agent_type = normalize_agent_name(agent_type)
    migrate_agent_names()
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = agent_type
    attachment = get_parsed_attachment()
    if "messages" not in st.session_state:
        st.session_state.messages = build_initial_messages(
            agent_type,
            SYSTEM_PROMPTS,
            attachment=attachment,
        )
        st.session_state.current_agent = agent_type
    elif should_reset_messages_on_agent_change(
        st.session_state.current_agent,
        agent_type,
        keep_history,
    ):
        st.session_state.messages = build_initial_messages(
            agent_type,
            SYSTEM_PROMPTS,
            attachment=attachment,
        )
        st.session_state.current_agent = agent_type
        st.session_state.agent_switch_notice = (
            f"已切换至「{agent_type}」，历史对话已清空。"
        )
    elif st.session_state.current_agent != agent_type:
        st.session_state.messages = reset_system(
            st.session_state.messages,
            agent_type,
            SYSTEM_PROMPTS,
            attachment=attachment,
        )
        st.session_state.current_agent = agent_type
        st.session_state.agent_switch_notice = (
            f"已切换至「{agent_type}」，已保留历史并更新系统角色。"
        )
    else:
        st.session_state.messages = reset_system(
            st.session_state.messages,
            agent_type,
            SYSTEM_PROMPTS,
            attachment=attachment,
        )
    sync_messages_system_prompt(agent_type)


def process_chat_attachment(uploaded, file_note, agent, cfg) -> bool:
    """根据附件触发一轮分析，仅写入 session，由统一消息区渲染。"""
    loaded = None
    if uploaded is not None:
        loaded = load_uploaded_file(uploaded)
        user_msg = build_file_user_message(loaded, file_note)
    else:
        stored = get_parsed_attachment()
        if not stored:
            raise ValueError("没有可分析的附件，请先拖入文件。")
        user_msg = build_user_message_from_attachment(stored, file_note)
    st.session_state.messages.append(user_msg)
    st.session_state["_awaiting_llm_reply"] = True
    return True


def stream_pending_chat_reply(agent, cfg):
    """生成助手回复并写入会话（稳定渲染，避免 DOM removeChild）。"""
    sync_messages_system_prompt(normalize_agent_name(cfg["agent_type"]))
    agent.system_prompt = effective_system_prompt(cfg["agent_type"])
    try:
        reply = stream_chat_into_message(
            agent,
            st.session_state.messages,
            temperature=cfg["temperature"],
            model=cfg["model_name"],
        )
    except Exception as exc:
        st.error(user_friendly_error(exc))
        return ""
    if reply:
        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )
    return reply


def render_chat_history():
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
            st.write(format_message_display(msg["content"]))


def render_chat_mode(llm_client, cfg):
    init_chat_session(cfg["agent_type"], cfg["keep_history"])

    if st.session_state.pop("_clear_chat_pending", False):
        clear_parsed_attachment()
        st.session_state.messages = build_initial_messages(
            cfg["agent_type"], SYSTEM_PROMPTS, with_welcome=False
        )

    agent_type = normalize_agent_name(cfg["agent_type"])
    agent = ChatAgent(
        llm_client,
        effective_system_prompt(agent_type),
        agent_type=agent_type,
    )

    upload_notice = st.session_state.pop("_upload_notice", None)
    if upload_notice:
        st.success(upload_notice)

    with streamlit_panel("附件", "📎"):
        st.caption(
            "拖入文件后会自动解析并写入对话上下文，可直接在底部提问；"
            "图片建议使用视觉模型（如 qwen-vl）。"
        )
        uploaded = render_drag_drop_uploader(
            "chat_file_upload",
            UPLOAD_TYPES,
            formats_hint="TXT PDF DOCX XLSX PNG JPG",
            help_text="拖入单文件后松开，系统会自动解析",
        )

        att = get_parsed_attachment()
        if att:
            st.success(attachment_status_line(att))
            if st.button("移除当前附件", use_container_width=True):
                clear_parsed_attachment()
                sync_messages_system_prompt(agent_type)
                agent.system_prompt = effective_system_prompt(agent_type)
                st.session_state["_upload_notice"] = "已移除附件。"
        else:
            st.info("尚未加载附件。拖入 PDF / Word 等文件后即可直接提问。")

        auto_analyze = st.checkbox(
            "解析后自动让 AI 总结一遍（可选）",
            value=False,
            help="默认仅静默解析；勾选后会在解析完成时自动发起一轮分析",
        )
        file_note = st.text_input(
            "补充说明（可选，用于自动分析或「立即分析」）",
            placeholder="例如：请总结要点 / 这份简历的专业是什么？",
            key="chat_file_note",
        )

        fp = upload_fingerprint(uploaded)
        trigger_parse = uploaded and is_new_upload("chat_file_upload", fp)
        trigger_manual_analyze = st.button("立即分析附件", use_container_width=True)

        if trigger_parse:
            try:
                with st.spinner("正在解析附件…"):
                    parse_and_store_attachment(uploaded)
                    sync_messages_system_prompt(agent_type)
                    agent.system_prompt = effective_system_prompt(agent_type)
                st.session_state["_upload_notice"] = attachment_status_line(
                    get_parsed_attachment()
                )
                if auto_analyze:
                    process_chat_attachment(uploaded, file_note, agent, cfg)
            except Exception as exc:
                st.error(user_friendly_error(exc))
        elif trigger_manual_analyze:
            if not uploaded and not get_parsed_attachment():
                st.warning("请先拖入文件，或保留已解析的附件后再分析。")
            else:
                try:
                    if uploaded:
                        parse_and_store_attachment(uploaded)
                        sync_messages_system_prompt(agent_type)
                        agent.system_prompt = effective_system_prompt(agent_type)
                    process_chat_attachment(uploaded, file_note, agent, cfg)
                except Exception as exc:
                    st.error(user_friendly_error(exc))

    visible = [m for m in st.session_state.messages if m["role"] != "system"]
    if len(visible) <= 1:
        ready_hint = (
            "附件已解析，可在页面底部直接提问（如：这个人的专业是什么？）。"
            if get_parsed_attachment()
            else "在页面底部输入问题，开始你的第一轮对话。"
        )
        st.info(f"{AGENT_ICONS.get(agent_type, '◈')} **{agent_type}** 已就绪 — {ready_hint}")

    user_input = st.chat_input("输入问题，Enter 发送…")
    if user_input:
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )
        quick = try_quick_calculate(user_input)
        if quick:
            st.session_state.messages.append(
                {"role": "assistant", "content": quick}
            )
        else:
            st.session_state["_awaiting_llm_reply"] = True

    render_chat_history()

    if st.session_state.pop("_awaiting_llm_reply", False):
        stream_pending_chat_reply(agent, cfg)


def render_rag_mode(llm_client, settings):
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = VectorStore(settings.vector_store_dir)
    rag = RAGAgent(llm_client, st.session_state.vector_store)

    with streamlit_panel("知识库管理", "◎"):
        st.caption(
            "支持 txt · md · pdf · docx · xlsx · xls → 分块向量化 → 检索问答（图片请用多轮对话模式）"
        )
        if settings.vendor == VENDOR_DEEPSEEK:
            st.info(
                "当前对话模型为 DeepSeek；**向量化固定走通义 Embedding**，"
                "请在 .env 配置 `DASHSCOPE_API_KEY`（或 `EMBEDDING_API_KEY`）。"
            )
        col1, col2 = st.columns([1.2, 1])
        with col1:
            docs = render_drag_drop_uploader(
                "rag_upload",
                RAG_UPLOAD_TYPES,
                multiple=True,
                formats_hint="TXT MD PDF DOCX XLSX",
                help_text="可一次拖入多个文档构建知识库",
            )
            auto_index = st.checkbox("拖入后自动构建索引", value=True)
            build = st.button(
                "构建 / 追加索引", type="primary", use_container_width=True
            )

            doc_list = docs if isinstance(docs, list) else ([docs] if docs else [])
            batch_fp = "|".join(upload_fingerprint(d) for d in doc_list)
            should_auto = (
                doc_list and auto_index and is_new_upload("rag_upload", batch_fp)
            )
            should_build = build or should_auto

            if should_build:
                if not doc_list:
                    st.warning("请先拖入或选择文档。")
                else:
                    total_added = 0
                    with st.spinner("正在解析文档并写入向量库…"):
                        for doc in doc_list:
                            count, msg = rag.ingest_upload(doc)
                            if count > 0:
                                total_added += count
                                st.success(f"{doc.name}：{msg}")
                            else:
                                st.error(f"{doc.name}：{msg}")
                    if total_added and len(doc_list) > 1:
                        st.info(f"本次共入库 {total_added} 个片段。")
        with col2:
            total = st.session_state.vector_store.count()
            st.metric("已索引片段", total)
            if st.button("清空知识库", use_container_width=True):
                try:
                    st.session_state.vector_store.clear()
                    st.session_state.vector_store = VectorStore(
                        settings.vector_store_dir
                    )
                    st.success("知识库已重置。")
                except Exception as exc:
                    st.error(user_friendly_error(exc))

    with streamlit_panel("检索问答", "◈"):
        question = st.text_area(
            "你的问题",
            placeholder="例如：文档的核心结论是什么？",
            height=88,
            label_visibility="collapsed",
        )
        if st.button("开始检索并生成回答", type="primary"):
            if not question.strip():
                st.warning("请先输入问题。")
            else:
                try:
                    with st.spinner("检索并生成回答中…"):
                        answer, retrieved = rag.answer(
                            question,
                            temperature=0.3,
                            stream_callback=None,
                        )
                    if answer:
                        st.markdown(answer)
                    else:
                        st.warning("未能生成回答，请检查知识库与 API 配置。")
                    if retrieved:
                        with st.expander("查看引用片段", expanded=False):
                            for item in retrieved:
                                st.markdown(
                                    f"**{item.source}** · 片段 "
                                    f"`{item.chunk_index}`"
                                )
                                st.text(item.content[:500])
                except Exception as exc:
                    st.error(user_friendly_error(exc))


def render_agent_tools_mode(llm_client):
    from tools.calculator import TOOL_NAME as CALC_TOOL

    base = BaseAgent(llm_client)
    tools = base.list_tools()

    with streamlit_panel("工具箱", "⚙"):
        for tool in tools:
            st.markdown(f"**{tool.name}** — {tool.description}")

        tool_name = st.selectbox(
            "选择要执行的工具",
            [t.name for t in tools],
        )
        user_input = st.text_area(
            "输入内容",
            height=120,
            placeholder="计算器示例：(125 + 76) * 9\n摘要示例：粘贴需要总结的段落",
        )
        if st.button("执行", type="primary", use_container_width=True):
            with st.spinner("工具运行中…"):
                try:
                    result = base.dispatch_command(tool_name, user_input)
                    st.success("执行完成")
                    if tool_name == CALC_TOOL:
                        st.metric("计算结果", result)
                    else:
                        st.markdown(result)
                except Exception as exc:
                    st.error(user_friendly_error(exc))


# ---------- 主流程 ----------
render_hero()
cfg = render_sidebar()

notice = st.session_state.pop("agent_switch_notice", None)
if notice:
    st.info(notice)

try:
    settings = load_settings(
        api_key_override=normalize_sidebar_override(cfg["api_key_input"]),
        vendor=cfg["vendor"],
        model_override=cfg["model_name"],
    )
    settings.ensure_valid(require_api_key=True)
except ConfigError as exc:
    st.warning(str(exc))
    st.info(
        "在左侧填写 API Key，或复制 `.env.example` 为 `代码文件/.env` 后配置。"
    )
    st.stop()

try:
    llm_client = build_llm_client(
        api_key_override=normalize_sidebar_override(cfg["api_key_input"]),
        vendor=cfg["vendor"],
        model_override=cfg["model_name"],
    )
except ConfigError:
    st.warning(api_key_missing_message(cfg["vendor"]))
    st.stop()

render_mode_strip(cfg["mode"])

if cfg["mode"] == "多轮对话":
    render_chat_mode(llm_client, cfg)
elif cfg["mode"] == "RAG 知识库":
    render_rag_mode(llm_client, settings)
else:
    render_agent_tools_mode(llm_client)

st.markdown(
    '<div class="mjz-footer">'
    "<strong>MJZ AI Pro</strong> · Python · Streamlit · RAG · Agent"
    "</div>",
    unsafe_allow_html=True,
)
