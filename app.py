"""
MJZ AI Pro — Streamlit 主入口
AI 对话工作台：多轮对话 · RAG 知识库 · Agent 工具
"""
import time
import streamlit as st
import streamlit.components.v1 as components

from agents.base_agent import BaseAgent
from agents.chat_agent import ChatAgent
from agents.prompts import AGENT_NAME_ALIASES, SYSTEM_PROMPTS, normalize_agent_name
from common import build_llm_client
from core.config import (
    ConfigError,
    api_key_missing_message,
    load_settings,
    normalize_sidebar_override,
    VENDOR_DEEPSEEK,
)
from rag.rag_agent import RAGAgent
from rag.vector_store import VectorStore
from ui.facade import (
    AGENT_ICONS,
    RAG_UPLOAD_TYPES,
    inject_custom_css,
    inject_gsap_animations,
    is_new_upload,
    render_chat_area,
    render_citation_cards,
    render_drag_drop_uploader,
    render_input_bar,
    render_main_header,
    render_sidebar,
    render_upload_panel,
    streamlit_panel,
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
from utils.logger import setup_logging, user_friendly_error
from utils.math_intent import try_quick_calculate
from utils.metrics import (
    record_attachment_parsed,
    record_document_ingest,
    record_llm_response,
    record_visit,
)
from utils.session_utils import (
    build_initial_messages,
    reset_system,
    should_reset_messages_on_agent_change,
)
from utils.stream_ui import stream_chat_into_message

setup_logging()

st.set_page_config(
    page_title="MJZ AI Pro",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
inject_gsap_animations()

if not st.session_state.get("_sidebar_auto_expanded"):
    components.html(
        """
<script>
(function () {
  const doc = window.parent.document;
  const sb = doc.querySelector('[data-testid="stSidebar"]');
  if (!sb || sb.getAttribute("aria-expanded") === "true") return;
  const btn = doc.querySelector('[data-testid="stExpandSidebarButton"]');
  if (btn) btn.click();
})();
</script>
        """,
        height=0,
        width=0,
    )
    st.session_state["_sidebar_auto_expanded"] = True


def init_app_metrics_once() -> None:
    if st.session_state.get("_metrics_visit_done"):
        return
    st.session_state["_metrics_visit_done"] = True
    record_visit()


def migrate_agent_names() -> None:
    old_agent = st.session_state.get("current_agent")
    if old_agent and old_agent in AGENT_NAME_ALIASES:
        st.session_state.current_agent = normalize_agent_name(old_agent)


def get_parsed_attachment():
    return st.session_state.get(SESSION_KEY)


def effective_system_prompt(agent_type: str) -> str:
    base = SYSTEM_PROMPTS[normalize_agent_name(agent_type)]
    return apply_attachment_to_system(base, get_parsed_attachment())


def sync_messages_system_prompt(agent_type: str) -> None:
    if "messages" not in st.session_state or not st.session_state.messages:
        return
    content = effective_system_prompt(agent_type)
    if st.session_state.messages[0].get("role") == "system":
        st.session_state.messages[0]["content"] = content
    else:
        st.session_state.messages.insert(0, {"role": "system", "content": content})


def clear_parsed_attachment() -> None:
    st.session_state.pop(SESSION_KEY, None)
    for key in list(st.session_state.keys()):
        if key.startswith("_upload_fp_"):
            del st.session_state[key]


def parse_and_store_attachment(uploaded) -> dict:
    loaded = load_uploaded_file(uploaded)
    attachment = loaded_file_to_attachment(loaded)
    st.session_state[SESSION_KEY] = attachment
    record_attachment_parsed()
    return attachment


def init_chat_session(agent_type: str, keep_history: bool) -> None:
    agent_type = normalize_agent_name(agent_type)
    migrate_agent_names()
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = agent_type
    attachment = get_parsed_attachment()
    if "messages" not in st.session_state:
        st.session_state.messages = build_initial_messages(
            agent_type, SYSTEM_PROMPTS, attachment=attachment
        )
        st.session_state.current_agent = agent_type
    elif should_reset_messages_on_agent_change(
        st.session_state.current_agent, agent_type, keep_history
    ):
        st.session_state.messages = build_initial_messages(
            agent_type, SYSTEM_PROMPTS, attachment=attachment
        )
        st.session_state.current_agent = agent_type
        st.session_state.agent_switch_notice = (
            f"已切换至「{agent_type}」，历史对话已清空。"
        )
    elif st.session_state.current_agent != agent_type:
        st.session_state.messages = reset_system(
            st.session_state.messages, agent_type, SYSTEM_PROMPTS, attachment=attachment
        )
        st.session_state.current_agent = agent_type
        st.session_state.agent_switch_notice = (
            f"已切换至「{agent_type}」，已保留历史并更新系统角色。"
        )
    else:
        st.session_state.messages = reset_system(
            st.session_state.messages, agent_type, SYSTEM_PROMPTS, attachment=attachment
        )
    sync_messages_system_prompt(agent_type)


def process_chat_attachment(uploaded, file_note, agent, cfg) -> bool:
    if uploaded is not None:
        loaded = load_uploaded_file(uploaded)
        user_msg = build_file_user_message(loaded, file_note)
    else:
        stored = get_parsed_attachment()
        if not stored:
            raise ValueError("没有可分析的附件，请先添加文件。")
        user_msg = build_user_message_from_attachment(stored, file_note)
    st.session_state.messages.append(user_msg)
    st.session_state["_awaiting_llm_reply"] = True
    return True


def stream_pending_chat_reply(agent, cfg) -> str:
    sync_messages_system_prompt(normalize_agent_name(cfg["agent_type"]))
    agent.system_prompt = effective_system_prompt(cfg["agent_type"])
    started = time.perf_counter()
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
    finally:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if elapsed_ms > 0:
            record_llm_response(elapsed_ms)
    if reply:
        st.session_state.messages.append({"role": "assistant", "content": reply})
    return reply


def render_chat_sidebar_attachments(holder: dict) -> None:
    """附件上传暂放在原生 sidebar 的 expander 中。"""
    agent_type = normalize_agent_name(cfg_agent_type_from_session())
    att = get_parsed_attachment()

    def _attach_options(uploaded_now) -> None:
        att_now = get_parsed_attachment()
        if att_now:
            st.caption(attachment_status_line(att_now))
            if st.button("移除附件", use_container_width=True, key="sidebar_remove_attachment"):
                st.session_state["_remove_attachment_pending"] = True
                st.rerun()
            st.divider()
        st.text_input(
            "补充说明",
            placeholder="例如：请总结要点",
            key="chat_file_note",
        )
        if st.button("立即分析附件", use_container_width=True, key="sidebar_analyze_btn"):
            att_now = get_parsed_attachment()
            if not uploaded_now and not att_now:
                st.warning("请先添加附件。")
            else:
                try:
                    if uploaded_now:
                        parse_and_store_attachment(uploaded_now)
                        sync_messages_system_prompt(agent_type)
                    st.session_state["_analyze_attachment_pending"] = True
                    st.rerun()
                except Exception as exc:
                    st.error(user_friendly_error(exc))

    with st.expander("📎 附件上传", expanded=bool(att)):
        file_card = None
        if att:
            file_card = {
                "filename": att.get("filename", "已加载附件"),
                "size": att.get("size"),
            }

        def _on_remove() -> None:
            st.session_state["_remove_attachment_pending"] = True

        holder["value"] = render_upload_panel(
            "chat_file_upload",
            UPLOAD_TYPES,
            formats_hint="TXT PDF DOCX XLSX PNG JPG",
            options_body=_attach_options,
            file_card=file_card,
            on_remove=_on_remove if att else None,
        )


def cfg_agent_type_from_session() -> str:
    agent_keys = list(SYSTEM_PROMPTS.keys())
    agent_labels = [f"{AGENT_ICONS.get(k, '·')}  {k}" for k in agent_keys]
    picked = st.session_state.get("ws_agent", agent_labels[0] if agent_labels else "")
    try:
        return agent_keys[agent_labels.index(picked)]
    except (ValueError, IndexError):
        return agent_keys[0] if agent_keys else "通用聊天助手"


def render_chat_mode(llm_client, cfg, *, uploaded_holder: dict | None = None) -> None:
    uploaded = None
    if uploaded_holder is not None:
        uploaded = uploaded_holder.get("value")
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
        st.toast(upload_notice, icon="📎")

    att = get_parsed_attachment()

    empty_hint = (
        "附件已就绪，直接在底部提问即可。"
        if att
        else "选择下方建议，或在底部输入框开始对话。"
    )
    render_chat_area(
        st.session_state.messages,
        format_message_display,
        empty_icon=AGENT_ICONS.get(agent_type, "✦"),
        empty_title=f"{agent_type} 已就绪",
        empty_hint=empty_hint,
    )

    if st.session_state.pop("_awaiting_llm_reply", False):
        stream_pending_chat_reply(agent, cfg)

    suggestion = st.session_state.pop("_suggestion_prompt", None)
    if suggestion:
        st.session_state.messages.append({"role": "user", "content": suggestion})
        st.session_state["_awaiting_llm_reply"] = True
        st.rerun()

    if st.session_state.pop("_remove_attachment_pending", False):
        clear_parsed_attachment()
        sync_messages_system_prompt(agent_type)
        st.session_state["_upload_notice"] = "已移除附件。"
        st.rerun()

    if st.session_state.pop("_analyze_attachment_pending", False):
        try:
            file_note = st.session_state.get("chat_file_note", "")
            process_chat_attachment(None, file_note, agent, cfg)
            st.rerun()
        except Exception as exc:
            st.error(user_friendly_error(exc))

    att = get_parsed_attachment()
    chip = None
    if att:
        chip = (
            att.get("filename", "已加载附件"),
            attachment_status_line(att),
        )

    user_input = render_input_bar(
        "输入消息，Enter 发送…",
        key="chat_main_input",
        attachment_chip=chip,
    )

    if uploaded is not None:
        fp = upload_fingerprint(uploaded)
        if fp and is_new_upload("chat_file_upload", fp):
            try:
                with st.spinner("正在解析附件…"):
                    parse_and_store_attachment(uploaded)
                    sync_messages_system_prompt(agent_type)
                st.session_state["_upload_notice"] = attachment_status_line(
                    get_parsed_attachment()
                )
                if st.session_state.get("auto_analyze"):
                    process_chat_attachment(
                        uploaded, st.session_state.get("chat_file_note", ""), agent, cfg
                    )
                st.rerun()
            except Exception as exc:
                st.error(user_friendly_error(exc))

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        quick = try_quick_calculate(user_input)
        if quick:
            st.session_state.messages.append({"role": "assistant", "content": quick})
        else:
            st.session_state["_awaiting_llm_reply"] = True
        st.rerun()


def render_rag_mode(llm_client, settings) -> None:
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = VectorStore(settings.vector_store_dir)
    rag = RAGAgent(llm_client, st.session_state.vector_store)

    if settings.vendor == VENDOR_DEEPSEEK:
        st.caption("向量化走通义 Embedding，请在 .env 配置 DASHSCOPE_API_KEY。")

    with streamlit_panel("知识库", "📚"):
        col1, col2 = st.columns(2)
        with col1:
            docs = render_drag_drop_uploader(
                "rag_upload",
                RAG_UPLOAD_TYPES,
                multiple=True,
                formats_hint="TXT MD PDF DOCX XLSX",
            )
            auto_index = st.checkbox("拖入后自动索引", value=True, key="rag_auto")
            build = st.button("构建索引", type="primary", use_container_width=True)
            doc_list = docs if isinstance(docs, list) else ([docs] if docs else [])
            batch_fp = "|".join(upload_fingerprint(d) for d in doc_list)
            should_build = build or (
                doc_list and auto_index and is_new_upload("rag_upload", batch_fp)
            )
            if should_build and doc_list:
                total = 0
                with st.spinner("正在写入向量库…"):
                    for doc in doc_list:
                        count, msg = rag.ingest_upload(doc)
                        if count > 0:
                            total += count
                            record_document_ingest(chunks=count)
                            st.toast(f"{doc.name}：{msg}", icon="✅")
                        else:
                            st.error(f"{doc.name}：{msg}")
                if total:
                    st.toast(f"共入库 {total} 个片段", icon="📚")
        with col2:
            total = st.session_state.vector_store.count()
            st.metric("已索引片段", total)
            if st.button("清空知识库", use_container_width=True):
                st.session_state.vector_store.clear()
                st.session_state.vector_store = VectorStore(settings.vector_store_dir)
                st.toast("知识库已重置", icon="🗑")

    question = render_input_bar("基于知识库提问…", key="rag_input")
    if question:
        st.session_state["_rag_question"] = question
        st.session_state["_rag_pending"] = True
        st.rerun()

    pending_q = st.session_state.pop("_rag_question", None)
    if st.session_state.pop("_rag_pending", False) and pending_q:
        with st.chat_message("user"):
            st.markdown(pending_q)
        try:
            started = time.perf_counter()
            with st.chat_message("assistant"):
                with st.spinner("检索并生成…"):
                    answer, retrieved = rag.answer(
                        pending_q, temperature=0.3, stream_callback=None
                    )
                record_llm_response(int((time.perf_counter() - started) * 1000))
                if answer:
                    st.markdown(answer)
                else:
                    st.warning("未能生成回答。")
            render_citation_cards(retrieved)
        except Exception as exc:
            st.error(user_friendly_error(exc))


def render_agent_tools_mode(llm_client) -> None:
    from tools.calculator import TOOL_NAME as CALC_TOOL

    base = BaseAgent(llm_client)
    tools = base.list_tools()

    with streamlit_panel("选择工具", "⚡"):
        tool_name = st.selectbox(
            "工具",
            [t.name for t in tools],
            format_func=lambda n: next(
                (f"{t.name} — {t.description}" for t in tools if t.name == n), n
            ),
            label_visibility="collapsed",
        )

    user_input = render_input_bar("输入内容后 Enter 执行…", key="tool_input")
    if user_input:
        st.session_state["_tool_input"] = user_input
        st.session_state["_tool_pending"] = True
        st.session_state["_tool_name"] = tool_name
        st.rerun()

    if st.session_state.pop("_tool_pending", False):
        tool_name = st.session_state.pop("_tool_name", tool_name)
        user_input = st.session_state.pop("_tool_input", "")
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.spinner("工具运行中…"):
            try:
                started = time.perf_counter()
                result = base.dispatch_command(tool_name, user_input)
                if tool_name != CALC_TOOL:
                    record_llm_response(int((time.perf_counter() - started) * 1000))
                with st.chat_message("assistant"):
                    if tool_name == CALC_TOOL:
                        st.code(str(result))
                    else:
                        st.markdown(result)
            except Exception as exc:
                st.error(user_friendly_error(exc))


# ---------- 主流程 ----------
init_app_metrics_once()

chat_upload_holder: dict = {"value": None}

with st.sidebar:
    cfg = render_sidebar()
    if cfg["mode"] == "多轮对话":
        render_chat_sidebar_attachments(chat_upload_holder)

notice = st.session_state.pop("agent_switch_notice", None)
if notice:
    st.toast(notice, icon="ℹ️")

try:
    settings = load_settings(
        api_key_override=normalize_sidebar_override(cfg["api_key_input"]),
        vendor=cfg["vendor"],
        model_override=cfg["model_name"],
    )
    settings.ensure_valid(require_api_key=True)
except ConfigError as exc:
    render_main_header(cfg["mode"])
    st.warning(str(exc))
    st.info("请在侧边栏「设置」中填写 API Key，或配置 `.env` 文件。")
    st.stop()

try:
    llm_client = build_llm_client(
        api_key_override=normalize_sidebar_override(cfg["api_key_input"]),
        vendor=cfg["vendor"],
        model_override=cfg["model_name"],
    )
except ConfigError:
    render_main_header(cfg["mode"])
    st.warning(api_key_missing_message(cfg["vendor"]))
    st.stop()

render_main_header(cfg["mode"], agent_type=cfg.get("agent_type", ""))

if cfg["mode"] == "多轮对话":
    render_chat_mode(llm_client, cfg, uploaded_holder=chat_upload_holder)
elif cfg["mode"] == "RAG 知识库":
    render_rag_mode(llm_client, settings)
else:
    render_agent_tools_mode(llm_client)
